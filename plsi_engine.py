import joblib
import os
import time
import warnings
import numpy as np
import pandas as pd
from typing import Dict


class TrendPredictor:
    """Loads trained ML models and provides continuous numerical forecasts."""

    def __init__(self, model_dir: str = "ML_model"):
        self.model_dir = model_dir
        self.env_model  = self._load_model("env_model.joblib")
        self.phys_model = self._load_model("phys_model.joblib")
        self.risk_model = self._load_model("risk_model.joblib")

    def _load_model(self, name: str):
        path = os.path.join(self.model_dir, name)
        if os.path.exists(path):
            return joblib.load(path)
        # FIX 3.1 — emit a proper UserWarning instead of a bare print
        warnings.warn(
            f"ML model '{name}' not found at '{path}'. "
            f"Falling back to statistical estimation. "
            f"Predictions will be approximate.",
            UserWarning,
            stacklevel=2,
        )
        return None

    @property
    def models_loaded(self) -> dict:
        """FIX 3.1 — report which models are actually loaded."""
        return {
            "env_model":  self.env_model  is not None,
            "phys_model": self.phys_model is not None,
            "risk_model": self.risk_model is not None,
        }

    def predict_trends(self, pollutants: Dict, physiology: Dict) -> Dict:
        """Generates 3-hour numerical forecasts for all 3 trend lines."""
        forecasts: Dict = {
            "environment_pm25": [],
            "physiology_breathing": [],
            "integrated_risk": [],
        }

        # FIX 3.2 — validate and clamp all inputs; warn on out-of-range values
        raw_pm25 = pollutants.get("pm25", 50)
        raw_br   = physiology.get("breathing_rate_lpm", 15)
        raw_hr   = physiology.get("heart_rate", 75)
        raw_spo2 = physiology.get("spo2", 97)
        raw_o3   = pollutants.get("o3", 30)
        raw_no2  = pollutants.get("no2", 40)

        curr_pm25 = max(0.0,  min(float(raw_pm25), 1000.0))
        curr_br   = max(1.0,  min(float(raw_br),   60.0))
        curr_hr   = max(30,   min(int(raw_hr),      220))
        curr_spo2 = max(70.0, min(float(raw_spo2),  100.0))
        curr_o3   = max(0.0,  min(float(raw_o3),    500.0))
        curr_no2  = max(0.0,  min(float(raw_no2),   500.0))

        # Warn whenever an input was out of clinical range
        _clamp_checks = [
            ("pm25",                raw_pm25, curr_pm25, 0.0,  1000.0),
            ("breathing_rate_lpm",  raw_br,   curr_br,   1.0,  60.0),
            ("heart_rate",          raw_hr,   curr_hr,   30,   220),
            ("spo2",                raw_spo2, curr_spo2, 70.0, 100.0),
            ("o3",                  raw_o3,   curr_o3,   0.0,  500.0),
            ("no2",                 raw_no2,  curr_no2,  0.0,  500.0),
        ]
        for field, original, clamped, lo, hi in _clamp_checks:
            if float(original) != float(clamped):
                warnings.warn(
                    f"Input '{field}' value {original} is outside valid range "
                    f"[{lo}, {hi}]; clamped to {clamped}.",
                    UserWarning,
                    stacklevel=2,
                )

        # FIX 3.3 — physics-based deterministic fallback using local time
        hour = time.localtime().tm_hour

        for i in range(1, 4):
            # --- Environment (PM2.5) ---
            if self.env_model:
                _X_env = pd.DataFrame([{
                    "pm2.5_ug_m3_lag_1": curr_pm25,
                    "pm2.5_ug_m3_lag_2": curr_pm25 * 0.9,
                    "pm2.5_ug_m3_lag_3": curr_pm25 * 0.8,
                    "ozone_ppb":         curr_o3,
                    "no2_ppb":           curr_no2,
                }])
                pred_pm25 = float(self.env_model.predict(_X_env)[0])
                curr_pm25 = max(0.0, pred_pm25)
            else:
                # Night-time (18:00-06:00) PM2.5 tends to rise; daytime falls
                trend_factor = 1.05 if (hour >= 18 or hour <= 6) else 0.98
                curr_pm25 = round(curr_pm25 * (trend_factor ** i), 2)

            forecasts["environment_pm25"].append(round(float(curr_pm25), 2))

            # --- Physiology (breathing rate) ---
            if self.phys_model:
                _X_phys = pd.DataFrame([{
                    "breathing_rate_lpm_lag_1": curr_br,
                    "breathing_rate_lpm_lag_2": curr_br * 0.9,
                    "heart_rate_bpm":           curr_hr,
                    "spo2_percent":             curr_spo2,
                }])
                pred_br = float(self.phys_model.predict(_X_phys)[0])
                curr_br = max(1.0, pred_br)
            else:
                # Breathing rate increases slightly with PM2.5 exposure
                curr_br = round(min(30.0, curr_br + (curr_pm25 / 500.0)), 2)

            forecasts["physiology_breathing"].append(round(float(curr_br), 2))

            # --- Integrated risk ---
            if self.risk_model:
                _X_risk = pd.DataFrame([{
                    "pm2.5_ug_m3":      curr_pm25,
                    "breathing_rate_lpm": curr_br,
                    "heart_rate_bpm":    curr_hr,
                    "ozone_ppb":         curr_o3,
                }])
                pred_risk = float(self.risk_model.predict(_X_risk)[0])
            else:
                # FIX 3.3 — weighted deterministic risk formula
                pred_risk = round(
                    (0.4  * curr_pm25 / 250.0)
                    + (0.35 * (curr_br - 12) / 20.0)
                    + (0.25 * (1 - curr_spo2 / 100.0)),
                    4,
                )

            forecasts["integrated_risk"].append(round(float(pred_risk), 4))

        return forecasts


class AlertEngine:
    """Generates health alerts based on PLSI score and pollutant levels."""

    # WHO guideline thresholds
    THRESHOLDS = {
        "pm25": {"moderate": 35,  "high": 75,  "critical": 150},
        "pm10": {"moderate": 50,  "high": 150, "critical": 250},
        "o3":   {"moderate": 60,  "high": 100, "critical": 180},
        "no2":  {"moderate": 40,  "high": 80,  "critical": 150},
    }

    ACTIONS = {
        "pm25": {
            "moderate": "Sensitive groups should reduce outdoor activity.",
            "high":     "Use an N95 mask outdoors. Limit exposure.",
            "critical": "Stay indoors. Use air purifiers. Seek medical help if symptomatic.",
        },
        "pm10": {
            "moderate": "Close windows during peak traffic hours.",
            "high":     "Avoid outdoor exercise. Use masks.",
            "critical": "Stay indoors. Avoid all outdoor activity.",
        },
        "o3": {
            "moderate": "Limit prolonged outdoor exertion.",
            "high":     "Avoid outdoor activity during midday hours.",
            "critical": "Stay indoors. Ozone levels are dangerous.",
        },
        "no2": {
            "moderate": "Avoid heavy traffic areas.",
            "high":     "Use masks near roadways. Limit outdoor time.",
            "critical": "Stay indoors. NO2 levels are hazardous.",
        },
    }

    @staticmethod
    def _get_level(score: float) -> str:
        if score < 20:
            return "Low"
        if score < 40:
            return "Mild"
        if score < 60:
            return "Medium"
        if score < 80:
            return "High"
        return "Extreme"

    @classmethod
    def generate_alerts(cls, plsi: float, risks: Dict, pollutants: Dict, profile: Dict) -> Dict:
        alerts = {
            "plsi": {"level": cls._get_level(plsi), "score": round(plsi, 2)},
            "environmental": [],
        }

        for pollutant, thresholds in cls.THRESHOLDS.items():
            value = pollutants.get(pollutant, 0)
            if value >= thresholds["critical"]:
                level = "Critical"
            elif value >= thresholds["high"]:
                level = "High"
            elif value >= thresholds["moderate"]:
                level = "Moderate"
            else:
                continue

            action_key = (
                "critical" if level == "Critical"
                else ("high" if level == "High" else "moderate")
            )
            alerts["environmental"].append({
                "parameter": pollutant.upper(),
                "value": round(value, 1),
                "level": level,
                "action": cls.ACTIONS.get(pollutant, {}).get(action_key, "Monitor conditions."),
            })

        pre_conditions = profile.get("pre_existing_conditions", [])
        smoking = profile.get("smoking_history", "none")

        if "asthma" in pre_conditions and plsi > 40:
            alerts["environmental"].append({
                "parameter": "ASTHMA_RISK",
                "level": "High",
                "action": "Keep rescue inhaler accessible. Consider preventive medication.",
            })

        if smoking == "active" and plsi > 30:
            alerts["environmental"].append({
                "parameter": "SMOKER_RISK",
                "level": "High",
                "action": "Smoking combined with current air quality significantly increases risk.",
            })

        return alerts


class PLSICalculator:
    """Personal Lung Stress Index Calculator with ML-powered trend forecasting."""

    def __init__(self, w1: float = 0.4, w2: float = 0.35, w3: float = 0.25):
        self.w1 = w1
        self.w2 = w2
        self.w3 = w3
        # FIX 3.4 — validate that weights sum to 1.0
        total = round(self.w1 + self.w2 + self.w3, 6)
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"PLSICalculator weights must sum to 1.0, got {total}. "
                f"w1={w1}, w2={w2}, w3={w3}"
            )
        self.predictor = TrendPredictor()

    def health_check(self) -> dict:
        """FIX 3.5 — return operational status of all sub-components."""
        return {
            "calculator": "PLSICalculator",
            "weights": {"w1": self.w1, "w2": self.w2, "w3": self.w3},
            "models": self.predictor.models_loaded,
            "status": "ok" if all(self.predictor.models_loaded.values()) else "degraded",
        }

    def calculate(
        self,
        pollutants: Dict,
        breathing_rate: float,
        profile: Dict,
        physiology: Dict,
    ) -> Dict:
        # 1. Normalize environmental stress (0-1)
        e_norm = min(1.0, max(0.0, pollutants.get("pm25", 0) / 250))

        # 2. Normalize physical demand (0-1)
        p_norm = min(1.0, max(0.0, (breathing_rate - 5) / 115))

        # 3. Biological vulnerability based on age
        age = profile.get("age", 30)
        if age < 5:
            b_risk = 0.7
        elif age < 18:
            b_risk = 0.3
        elif age < 45:
            b_risk = 0.1
        elif age < 65:
            b_risk = 0.3
        else:
            b_risk = 0.6

        pre_conditions = profile.get("pre_existing_conditions", [])
        if "asthma" in pre_conditions:
            b_risk = min(1.0, b_risk + 0.15)
        if "copd" in pre_conditions:
            b_risk = min(1.0, b_risk + 0.2)

        smoking = profile.get("smoking_history", "none")
        if smoking == "active":
            b_risk = min(1.0, b_risk + 0.15)
        elif smoking == "former":
            b_risk = min(1.0, b_risk + 0.05)

        # Calculate PLSI score
        plsi_score = (self.w1 * e_norm + self.w2 * p_norm + self.w3 * b_risk) * 100

        # Generate ML / physics-based forecasts
        forecasts = self.predictor.predict_trends(pollutants, physiology)

        plsi_factor = plsi_score / 100.0
        disease_risks = {
            "asthma_exacerbation":  round(min(1.0, 0.05 + plsi_factor * 0.4), 3),
            "copd_flare_up":        round(min(1.0, 0.02 + plsi_factor * 0.3), 3),
            "general_inflammation": round(min(1.0, plsi_factor), 3),
        }

        return {
            "plsi_score": round(plsi_score, 2),
            "interpretation": AlertEngine._get_level(plsi_score),
            "alerts": AlertEngine.generate_alerts(plsi_score, disease_risks, pollutants, profile),
            "impact_explanations": [
                f"Environment accounts for {round(e_norm * 100)}% of stress.",
                f"Physical activity accounts for {round(p_norm * 100)}% of impact.",
                f"Biological vulnerability factor: {round(b_risk * 100)}%.",
            ],
            "disease_risks": disease_risks,
            "risk_drivers": self._get_risk_drivers(e_norm, p_norm, b_risk, pollutants),
            "breakdown": {
                "environmental_stress":    round(e_norm,  4),
                "physical_demand":         round(p_norm,  4),
                "biological_vulnerability": round(b_risk, 4),
            },
            "forecasts": forecasts,
        }

    @staticmethod
    def _get_risk_drivers(
        e_norm: float, p_norm: float, b_risk: float, pollutants: Dict
    ) -> list:
        """Identify the top risk drivers."""
        drivers = []
        factors = [
            (e_norm, "Environmental pollution"),
            (p_norm, "Physical exertion"),
            (b_risk, "Biological vulnerability"),
        ]
        factors.sort(key=lambda x: x[0], reverse=True)

        for value, name in factors:
            if value > 0.1:
                drivers.append(f"{name} is a significant factor ({round(value * 100)}%).")

        if pollutants.get("pm25", 0) > 100:
            drivers.append("PM2.5 levels are critically elevated.")
        if pollutants.get("o3", 0) > 100:
            drivers.append("Ozone levels are dangerously high.")

        return drivers if drivers else ["All risk factors are within normal range."]


# =============================================================================
# ML Orchestrator — integrates all 5 AeroLung ML models into a single
# interface that augments the existing PLSICalculator output.
# =============================================================================

class AeroLungMLOrchestrator:
    """
    Unified interface over all five AeroLung ML pipeline models.

    Lazy-loads each model on first use.  If a model is unavailable its
    contribution is omitted and the remaining models still operate normally.

    Usage
    -----
    >>> orch = AeroLungMLOrchestrator()
    >>> result = orch.predict(
    ...     pollutants={"pm25": 55.0, "pm10": 80.0, "o3": 40.0, "no2": 25.0},
    ...     physiology={"spo2": 95.0, "heart_rate": 88, "breathing_rate": 20},
    ...     profile={"age": 65, "conditions": ["asthma"], "name": "Patient A"},
    ...     recent_pm25_history=[12.0, 14.0, 55.0],  # last N hourly readings
    ... )
    """

    def __init__(self):
        self._forecaster      = None
        self._risk_scorer     = None
        self._disease_pred    = None
        self._anomaly_det     = None
        self._report_gen      = None
        self._init_error: dict = {}
        self._lazy_init()

    # ------------------------------------------------------------------
    # Lazy initialisation
    # ------------------------------------------------------------------

    def _lazy_init(self) -> None:
        """Import and instantiate all models, swallowing individual failures."""
        try:
            from aerolung.ml.models.aqi_forecaster import AQIForecaster
            self._forecaster = AQIForecaster()
        except Exception as exc:
            self._init_error["forecaster"] = str(exc)

        try:
            from aerolung.ml.models.health_risk_scorer import HealthRiskScorer
            self._risk_scorer = HealthRiskScorer()
        except Exception as exc:
            self._init_error["risk_scorer"] = str(exc)

        try:
            from aerolung.ml.models.disease_predictor import DiseasePredictor
            self._disease_pred = DiseasePredictor()
        except Exception as exc:
            self._init_error["disease_predictor"] = str(exc)

        try:
            from aerolung.ml.models.anomaly_detector import AnomalyDetector
            self._anomaly_det = AnomalyDetector()
        except Exception as exc:
            self._init_error["anomaly_detector"] = str(exc)

        try:
            from aerolung.ml.models.report_generator import ReportGenerator
            self._report_gen = ReportGenerator()
        except Exception as exc:
            self._init_error["report_generator"] = str(exc)

    # ------------------------------------------------------------------
    # Main inference entry point
    # ------------------------------------------------------------------

    def predict(
        self,
        pollutants: Dict,
        physiology: Dict,
        profile: Dict,
        recent_pm25_history: list = None,
        forecast_steps: int = 3,
    ) -> Dict:
        """
        Run all available ML models and return a unified result dict.

        The return value is designed to be merged directly into the
        PLSICalculator.calculate() output under the key "ml_insights".

        Parameters
        ----------
        pollutants          : dict  pm25, pm10, o3, no2  (current readings)
        physiology          : dict  spo2, heart_rate, breathing_rate
        profile             : dict  age, conditions, name, gender, bmi, etc.
        recent_pm25_history : list  past hourly PM2.5 values for LSTM
        forecast_steps      : int   number of hours to forecast

        Returns
        -------
        dict with keys:
          aqi_forecast      dict   {forecasts, confidence, method, aqi_values}
          health_risk       dict   {risk_score, risk_category, method, …}
          disease_risks_ml  dict   {disease_risks, highest_risk, …}
          anomaly           dict   {is_anomaly, anomaly_score, flagged_reason}
          advisory          dict   {advisory, risk_level, method}
          model_status      dict   which models loaded successfully
        """
        result: Dict = {"model_status": self._model_status()}

        pm25 = float(pollutants.get("pm25", 15.0))
        aqi  = _pm25_to_aqi_local(pm25)

        # 1. AQI Forecaster
        if self._forecaster is not None:
            history = recent_pm25_history or [pm25]
            try:
                result["aqi_forecast"] = self._forecaster.forecast(history, steps=forecast_steps)
            except Exception as exc:
                warnings.warn(f"AQIForecaster.forecast() failed: {exc}", UserWarning, stacklevel=2)

        # 2. Health Risk Scorer
        if self._risk_scorer is not None:
            combined = {**pollutants, **physiology, **profile}
            try:
                result["health_risk"] = self._risk_scorer.score(combined)
            except Exception as exc:
                warnings.warn(f"HealthRiskScorer.score() failed: {exc}", UserWarning, stacklevel=2)

        # 3. Disease Predictor
        if self._disease_pred is not None:
            combined = {**pollutants, **physiology, **profile}
            try:
                result["disease_risks_ml"] = self._disease_pred.predict(combined)
            except Exception as exc:
                warnings.warn(f"DiseasePredictor.predict() failed: {exc}", UserWarning, stacklevel=2)

        # 4. Anomaly Detector
        if self._anomaly_det is not None:
            try:
                from datetime import datetime
                now = datetime.now()
                reading = {
                    "pm25": pm25,
                    "hour": now.hour,
                    "day_of_week": now.weekday(),
                    "city": profile.get("city", ""),
                }
                result["anomaly"] = self._anomaly_det.detect(reading)
            except Exception as exc:
                warnings.warn(f"AnomalyDetector.detect() failed: {exc}", UserWarning, stacklevel=2)

        # 5. Report Generator
        if self._report_gen is not None:
            patient_ctx = {
                **profile,
                "aqi":            aqi,
                "pm25":           pm25,
                "spo2":           physiology.get("spo2", 97),
                "heart_rate":     physiology.get("heart_rate", 72),
                "breathing_rate": physiology.get("breathing_rate", 16),
                "conditions":     profile.get("conditions", []),
            }
            try:
                result["advisory"] = self._report_gen.generate(patient_ctx)
            except Exception as exc:
                warnings.warn(f"ReportGenerator.generate() failed: {exc}", UserWarning, stacklevel=2)

        return result

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def _model_status(self) -> Dict:
        return {
            "forecaster":       self._forecaster is not None,
            "risk_scorer":      self._risk_scorer is not None,
            "disease_predictor": self._disease_pred is not None,
            "anomaly_detector": self._anomaly_det is not None,
            "report_generator": self._report_gen is not None,
            "init_errors":      self._init_error,
        }

    def health_check(self) -> Dict:
        """Returns health status for all constituent models."""
        checks = {"orchestrator": "ok", "models": {}}
        degraded = False

        for name, model in [
            ("forecaster",       self._forecaster),
            ("risk_scorer",      self._risk_scorer),
            ("disease_predictor", self._disease_pred),
            ("anomaly_detector", self._anomaly_det),
            ("report_generator", self._report_gen),
        ]:
            if model is not None and hasattr(model, "health_check"):
                checks["models"][name] = model.health_check()
                if checks["models"][name].get("status") == "degraded":
                    degraded = True
            else:
                checks["models"][name] = {"status": "unavailable"}
                degraded = True

        checks["orchestrator"] = "degraded" if degraded else "ok"
        return checks


# ---------------------------------------------------------------------------
# Module-level helper (shared with AQIForecaster without circular import)
# ---------------------------------------------------------------------------

def _pm25_to_aqi_local(pm25: float) -> int:
    """EPA AQI conversion — mirrors the function in main.py."""
    if pm25 <= 12.0:   return int((50 / 12.0) * pm25)
    if pm25 <= 35.4:   return int(50  + ((100 - 50)  / (35.4 - 12.1))  * (pm25 - 12.1))
    if pm25 <= 55.4:   return int(100 + ((150 - 100) / (55.4 - 35.5))  * (pm25 - 35.5))
    if pm25 <= 150.4:  return int(150 + ((200 - 150) / (150.4 - 55.5)) * (pm25 - 55.5))
    if pm25 <= 250.4:  return int(200 + ((300 - 200) / (250.4 - 150.5))* (pm25 - 150.5))
    return min(500, int(300 + (pm25 - 250.5) * 0.99))
