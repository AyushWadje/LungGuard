"""
AeroLung — Health Risk Scorer (XGBoost)
========================================
Predicts a continuous respiratory health-risk score [0.0, 1.0]
using an XGBoost gradient-boosted tree trained on NHANES health data.

Falls back to a deterministic rule-based model when the trained
XGBoost model file is absent.
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

try:
    import xgboost as xgb
    _XGB_AVAILABLE = True
except ImportError:
    _XGB_AVAILABLE = False

_MODEL_PATH   = Path(__file__).parent.parent / "saved_models" / "xgb_health_risk.joblib"
_SCALER_PATH  = Path(__file__).parent.parent / "saved_models" / "xgb_hr_scaler.joblib"

# Feature order must match training
FEATURE_NAMES: List[str] = [
    "age", "gender", "race", "income_ratio",
    "fev1", "fvc", "fev1_fvc_ratio",
    "ever_smoked", "current_smoker",
    "asthma_ever", "copd",
    "systolic_bp", "diastolic_bp", "pulse_rate",
    "bmi",
]


class HealthRiskScorer:
    """
    Predicts individual respiratory health-risk score [0.0, 1.0].

    Usage
    -----
    >>> scorer = HealthRiskScorer()
    >>> result = scorer.score({
    ...     "age": 45, "gender": 1, "fev1": 2.8, "fvc": 3.5,
    ...     "fev1_fvc_ratio": 0.80, "systolic_bp": 130,
    ...     "diastolic_bp": 85, "bmi": 29, "copd": 0, "asthma_ever": 1,
    ... })
    >>> result["risk_score"]        # 0.0 – 1.0
    >>> result["risk_category"]     # "Low" / "Moderate" / "High"
    """

    def __init__(self, model_path: Optional[Path] = None):
        self._model  = None
        self._scaler = None
        self._loaded = False
        self._load(model_path or _MODEL_PATH)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load(self, model_path: Path) -> None:
        if not _JOBLIB_AVAILABLE:
            warnings.warn("joblib not installed — HealthRiskScorer using rule-based fallback.", UserWarning, stacklevel=3)
            return

        if model_path.exists():
            try:
                self._model = joblib.load(model_path)
                logger.info(f"HealthRiskScorer model loaded from {model_path.name}")
                self._loaded = True
            except Exception as exc:
                logger.warning(f"Could not load HealthRiskScorer model: {exc}")
        else:
            warnings.warn(
                f"HealthRiskScorer: model not found at '{model_path}'. "
                "Falling back to rule-based estimation. "
                "Run aerolung/ml/training/train_health_risk.py to train.",
                UserWarning,
                stacklevel=3,
            )

        scaler_path = _SCALER_PATH
        if scaler_path.exists():
            try:
                self._scaler = joblib.load(scaler_path)
            except Exception:
                pass

    @property
    def is_ready(self) -> bool:
        return self._loaded

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def score(self, patient_data: Dict) -> Dict:
        """
        Predict health risk score for a single patient.

        Parameters
        ----------
        patient_data : dict
            Keys map to FEATURE_NAMES.  Missing features default to
            population medians.

        Returns
        -------
        dict:
          risk_score      float     0.0 (healthy) – 1.0 (high risk)
          risk_category   str       Low / Moderate / High / Critical
          feature_contribution  dict[str, float]  approx SHAP-like weights
          confidence      float     model confidence (0–1)
          method          str
        """
        features = self._extract_features(patient_data)

        if self._loaded and self._model is not None:
            return self._xgb_score(features)
        return self._rule_based_score(patient_data)

    def _extract_features(self, data: Dict) -> np.ndarray:
        """Build the feature vector using defaults for missing fields."""
        defaults = {
            "age": 40, "gender": 1, "race": 3, "income_ratio": 2.0,
            "fev1": 3.0, "fvc": 3.8, "fev1_fvc_ratio": 0.78,
            "ever_smoked": 2, "current_smoker": 3,
            "asthma_ever": 2, "copd": 2,
            "systolic_bp": 120, "diastolic_bp": 80, "pulse_rate": 72,
            "bmi": 25.0,
        }
        vec = np.array([float(data.get(f, defaults[f])) for f in FEATURE_NAMES])

        if self._scaler is not None:
            vec = self._scaler.transform(vec.reshape(1, -1)).flatten()
        return vec

    def _xgb_score(self, features: np.ndarray) -> Dict:
        raw = float(self._model.predict_proba(features.reshape(1, -1))[0, 1])
        raw = float(np.clip(raw, 0.0, 1.0))
        contrib = {}
        if hasattr(self._model, "feature_importances_"):
            fi = self._model.feature_importances_
            for name, imp in zip(FEATURE_NAMES, fi):
                contrib[name] = round(float(imp), 4)
        return {
            "risk_score":          round(raw, 4),
            "risk_category":       _score_to_category(raw),
            "feature_contribution": contrib,
            "confidence":          0.85,
            "method":              "xgboost",
        }

    def _rule_based_score(self, data: Dict) -> Dict:
        """Simple rule-based fallback (no ML required)."""
        score = 0.0
        age = float(data.get("age", 40))
        if age > 65:   score += 0.20
        elif age < 5:  score += 0.15

        fev1_fvc = float(data.get("fev1_fvc_ratio", 0.78))
        if fev1_fvc < 0.70:  score += 0.25
        elif fev1_fvc < 0.75: score += 0.10

        bmi = float(data.get("bmi", 25))
        if bmi > 35:   score += 0.10
        elif bmi < 18: score += 0.08

        sbp = float(data.get("systolic_bp", 120))
        if sbp > 160:  score += 0.12
        elif sbp > 140: score += 0.06

        copd       = int(data.get("copd", 2))
        asthma     = int(data.get("asthma_ever", 2))
        smoker     = int(data.get("current_smoker", 3))

        if copd == 1:     score += 0.20
        if asthma == 1:   score += 0.12
        if smoker == 1:   score += 0.10

        score = float(np.clip(score, 0.0, 1.0))
        return {
            "risk_score":          round(score, 4),
            "risk_category":       _score_to_category(score),
            "feature_contribution": {},
            "confidence":          0.60,
            "method":              "rule_based",
        }

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> Dict:
        return {
            "model":        "HealthRiskScorer",
            "backend":      "xgboost" if self._loaded else "rule_based",
            "xgb_available": _XGB_AVAILABLE,
            "feature_count": len(FEATURE_NAMES),
            "status":       "ok" if self._loaded else "degraded",
        }


def _score_to_category(score: float) -> str:
    if score < 0.25:  return "Low"
    if score < 0.50:  return "Moderate"
    if score < 0.75:  return "High"
    return "Critical"
