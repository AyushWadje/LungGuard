"""
AeroLung — Disease Predictor (XGBoost multi-label)
===================================================
Predicts the probability of specific respiratory disease events:
  - Asthma exacerbation
  - COPD flare-up
  - Pulmonary hypertension risk
  - Respiratory infection susceptibility

Falls back to a PLSI-based analytical model when no trained model exists.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from loguru import logger

try:
    import joblib
    _JOBLIB_AVAILABLE = True
except ImportError:
    _JOBLIB_AVAILABLE = False

_MODEL_PATH  = Path(__file__).parent.parent / "saved_models" / "xgb_disease_predictor.joblib"
_SCALER_PATH = Path(__file__).parent.parent / "saved_models" / "xgb_disease_scaler.joblib"

DISEASE_LABELS: List[str] = [
    "asthma_exacerbation",
    "copd_flare_up",
    "pulmonary_hypertension",
    "respiratory_infection",
]

FEATURE_NAMES: List[str] = [
    "pm25", "pm10", "o3", "no2",
    "age", "bmi", "fev1_fvc_ratio",
    "asthma_ever", "copd",
    "current_smoker",
    "systolic_bp", "pulse_rate", "spo2",
    "heart_rate", "breathing_rate",
]


class DiseasePredictor:
    """
    Multi-label respiratory disease risk predictor.

    Usage
    -----
    >>> predictor = DiseasePredictor()
    >>> result = predictor.predict({
    ...     "pm25": 50, "o3": 40, "age": 60, "spo2": 95,
    ...     "copd": 1, "fev1_fvc_ratio": 0.65,
    ... })
    >>> result["disease_risks"]   # dict[disease_name → probability]
    """

    def __init__(self, model_path: Optional[Path] = None):
        self._models: Dict[str, object] = {}
        self._scaler = None
        self._loaded = False
        self._load(model_path or _MODEL_PATH)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load(self, model_path: Path) -> None:
        if not _JOBLIB_AVAILABLE:
            return

        if model_path.exists():
            try:
                bundle = joblib.load(model_path)
                if isinstance(bundle, dict):
                    self._models = bundle
                else:
                    # Treat as a single multi-output model
                    self._models = {"_multi": bundle}
                self._loaded = True
                logger.info(f"DiseasePredictor model(s) loaded from {model_path.name}")
            except Exception as exc:
                logger.warning(f"DiseasePredictor load error: {exc}")
        else:
            warnings.warn(
                f"DiseasePredictor: model not found at '{model_path}'. "
                "Falling back to analytical estimation. "
                "Run aerolung/ml/training/train_disease.py to train.",
                UserWarning,
                stacklevel=3,
            )

        if _SCALER_PATH.exists():
            try:
                self._scaler = joblib.load(_SCALER_PATH)
            except Exception:
                pass

    @property
    def is_ready(self) -> bool:
        return self._loaded

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(self, context: Dict) -> Dict:
        """
        Predict disease risk probabilities.

        Parameters
        ----------
        context : dict
            Environmental + physiological inputs (see FEATURE_NAMES).

        Returns
        -------
        dict:
          disease_risks     dict[str, float]  per-disease probability 0–1
          highest_risk      str               name of top-risk disease
          overall_risk      float             max probability
          method            str
          recommendations   list[str]
        """
        features = self._build_feature_vector(context)

        if self._loaded and self._models:
            probs = self._model_predict(features)
        else:
            probs = self._analytical_predict(context)

        results = dict(zip(DISEASE_LABELS, probs))
        highest = max(results, key=results.get)

        return {
            "disease_risks":   {k: round(v, 4) for k, v in results.items()},
            "highest_risk":    highest,
            "overall_risk":    round(float(max(probs)), 4),
            "method":          "xgboost" if self._loaded else "analytical",
            "recommendations": _generate_recommendations(results, context),
        }

    def _build_feature_vector(self, data: Dict) -> np.ndarray:
        defaults = {
            "pm25": 15.0, "pm10": 25.0, "o3": 30.0, "no2": 20.0,
            "age": 40, "bmi": 25.0, "fev1_fvc_ratio": 0.78,
            "asthma_ever": 0, "copd": 0, "current_smoker": 0,
            "systolic_bp": 120, "pulse_rate": 72, "spo2": 97,
            "heart_rate": 75, "breathing_rate": 16,
        }
        vec = np.array([float(data.get(f, defaults[f])) for f in FEATURE_NAMES])
        if self._scaler is not None:
            vec = self._scaler.transform(vec.reshape(1, -1)).flatten()
        return vec

    def _model_predict(self, features: np.ndarray) -> np.ndarray:
        if "_multi" in self._models:
            model = self._models["_multi"]
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(features.reshape(1, -1))
                if isinstance(proba, list):            # multi-output
                    return np.array([p[0, 1] for p in proba])
                return np.clip(proba[0], 0, 1)
            return np.clip(model.predict(features.reshape(1, -1))[0], 0, 1)
        # Per-label models
        probs = []
        feat_unscaled = features  # already scaled at this point
        for label in DISEASE_LABELS:
            if label in self._models:
                m = self._models[label]
                if hasattr(m, "predict_proba"):
                    probs.append(float(m.predict_proba(feat_unscaled.reshape(1, -1))[0, 1]))
                else:
                    probs.append(float(np.clip(m.predict(feat_unscaled.reshape(1, -1))[0], 0, 1)))
            else:
                probs.append(0.0)
        return np.array(probs)

    def _analytical_predict(self, data: Dict) -> np.ndarray:
        """Physics-based disease risk estimation."""
        pm25  = float(data.get("pm25", 15))
        o3    = float(data.get("o3",   30))
        age   = float(data.get("age",  40))
        spo2  = float(data.get("spo2", 97))
        fev   = float(data.get("fev1_fvc_ratio", 0.78))
        asthma  = int(data.get("asthma_ever", 0))
        copd    = int(data.get("copd",        0))
        smoker  = int(data.get("current_smoker", 0))

        base_env = min(1.0, pm25 / 250.0 + o3 / 200.0) * 0.5
        age_risk = 0.2 if age > 65 else (0.1 if age > 45 else 0.05)
        spo2_risk = max(0.0, (100 - spo2) / 20.0)
        fev_risk  = max(0.0, (0.80 - fev) / 0.40) if fev < 0.80 else 0.0

        asthma_prob = float(np.clip(
            0.05 + base_env * 0.6 + (0.20 if asthma else 0) + age_risk * 0.5 + spo2_risk * 0.3, 0, 1))
        copd_prob = float(np.clip(
            0.02 + base_env * 0.4 + (0.30 if copd else 0) + (0.15 if smoker else 0) + fev_risk * 0.5, 0, 1))
        ph_prob = float(np.clip(
            0.01 + spo2_risk * 0.5 + age_risk * 0.4 + base_env * 0.2, 0, 1))
        inf_prob = float(np.clip(
            0.03 + base_env * 0.3 + age_risk * 0.3 + (0.10 if smoker else 0), 0, 1))

        return np.array([asthma_prob, copd_prob, ph_prob, inf_prob])

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> Dict:
        return {
            "model":    "DiseasePredictor",
            "backend":  "xgboost" if self._loaded else "analytical",
            "diseases": DISEASE_LABELS,
            "status":   "ok" if self._loaded else "degraded",
        }


def _generate_recommendations(risks: Dict[str, float], context: Dict) -> List[str]:
    recs = []
    if risks.get("asthma_exacerbation", 0) > 0.5:
        recs.append("Keep rescue inhaler accessible. Avoid outdoor exposure during peak pollution hours.")
    if risks.get("copd_flare_up", 0) > 0.5:
        recs.append("COPD worsening predicted — contact pulmonologist. Use bronchodilator as prescribed.")
    if risks.get("pulmonary_hypertension", 0) > 0.4:
        recs.append("Elevated pulmonary hypertension risk — limit physical exertion. Monitor SpO2.")
    if risks.get("respiratory_infection", 0) > 0.4:
        recs.append("Increased infection susceptibility — wear N95 mask outdoors. Wash hands frequently.")
    if not recs:
        recs.append("Current risk levels are within acceptable range. Continue regular monitoring.")
    return recs
