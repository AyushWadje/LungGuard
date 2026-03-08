"""
AeroLung — Anomaly Detector (Isolation Forest)
================================================
Identifies anomalous AQI sensor readings using an Isolation Forest
trained on real OpenAQ PM2.5 data.

Flags readings that deviate significantly from learned patterns
(sensor malfunction, unusual pollution events, data corruption).
Falls back to a statistical Z-score detector when no model exists.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

try:
    import joblib
    _JOBLIB_AVAILABLE = True
except ImportError:
    _JOBLIB_AVAILABLE = False

_MODEL_PATH  = Path(__file__).parent.parent / "saved_models" / "isolation_forest.joblib"
_SCALER_PATH = Path(__file__).parent.parent / "saved_models" / "if_scaler.joblib"

# City-level context lookup for normalisation
_KNOWN_CITIES: Dict[str, float] = {
    "Delhi":       115.0,
    "Beijing":     75.0,
    "Jakarta":     55.0,
    "Karachi":     95.0,
    "Cairo":       80.0,
    "São Paulo":   30.0,
    "Mexico City": 25.0,
    "Lagos":       60.0,
    "Dhaka":       120.0,
    "Bangkok":     35.0,
}


class AnomalyDetector:
    """
    Sensor anomaly detector for AQI/PM2.5 readings.

    Usage
    -----
    >>> ad = AnomalyDetector()
    >>> result = ad.detect({
    ...     "pm25": 850.0,
    ...     "hour":  14,
    ...     "day_of_week": 2,
    ...     "city": "Delhi",
    ... })
    >>> result["is_anomaly"]    # bool
    >>> result["anomaly_score"] # float − lower = more anomalous
    """

    CONTAMINATION: float = 0.05    # expected anomaly fraction in training data

    def __init__(self, model_path: Optional[Path] = None):
        self._model  = None
        self._scaler = None
        self._loaded = False
        self._window: List[float] = []    # rolling window for z-score fallback
        self._load(model_path or _MODEL_PATH)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load(self, model_path: Path) -> None:
        if not _JOBLIB_AVAILABLE:
            return

        if model_path.exists():
            try:
                self._model = joblib.load(model_path)
                logger.info(f"Isolation Forest loaded from {model_path.name}")
                self._loaded = True
            except Exception as exc:
                logger.warning(f"AnomalyDetector load error: {exc}")
        else:
            warnings.warn(
                f"AnomalyDetector: model not found at '{model_path}'. "
                "Falling back to Z-score detection. "
                "Run aerolung/ml/training/train_anomaly.py to train.",
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

    def detect(self, reading: Dict) -> Dict:
        """
        Evaluate a single PM2.5 sensor reading for anomalies.

        Parameters
        ----------
        reading : dict
            pm25        float   PM2.5 concentration (µg/m³)
            hour        int     hour of day 0–23
            day_of_week int     0=Mon … 6=Sun
            city        str     optional city name for contextual baseline

        Returns
        -------
        dict:
          is_anomaly      bool
          anomaly_score   float   Isolation Forest score (lower → more anomalous)
          z_score         float   standard-deviation distance from rolling mean
          flagged_reason  str     human-readable explanation
          method          str
        """
        pm25        = float(reading.get("pm25", 15.0))
        hour        = int(reading.get("hour", 12)) % 24
        dow         = int(reading.get("day_of_week", 0)) % 7
        city        = str(reading.get("city", ""))
        city_mean   = _KNOWN_CITIES.get(city, 30.0)

        if self._loaded and self._model is not None:
            return self._if_detect(pm25, hour, dow, city_mean)
        return self._zscore_detect(pm25, city_mean)

    def _build_feature(self, pm25: float, hour: int, dow: int, city_mean: float) -> np.ndarray:
        relative_pm25 = pm25 - city_mean              # deviation from city baseline
        hour_sin  = np.sin(2 * np.pi * hour / 24)
        hour_cos  = np.cos(2 * np.pi * hour / 24)
        dow_sin   = np.sin(2 * np.pi * dow  / 7)
        dow_cos   = np.cos(2 * np.pi * dow  / 7)
        vec = np.array([pm25, relative_pm25, hour_sin, hour_cos, dow_sin, dow_cos])
        if self._scaler is not None:
            vec = self._scaler.transform(vec.reshape(1, -1)).flatten()
        return vec

    def _if_detect(self, pm25: float, hour: int, dow: int, city_mean: float) -> Dict:
        feat  = self._build_feature(pm25, hour, dow, city_mean)
        pred  = int(self._model.predict(feat.reshape(1, -1))[0])     # −1=anomaly, 1=normal
        score = float(self._model.score_samples(feat.reshape(1, -1))[0])
        z     = abs(pm25 - city_mean) / max(city_mean * 0.4, 1.0)    # rough z approximation

        is_anom = pred == -1
        return {
            "is_anomaly":    is_anom,
            "anomaly_score": round(score, 4),
            "z_score":       round(z, 2),
            "flagged_reason": _explain(pm25, city_mean, is_anom),
            "method":        "isolation_forest",
        }

    def _zscore_detect(self, pm25: float, city_mean: float) -> Dict:
        """Z-score statistical fallback using a rolling 24-hour window."""
        self._window.append(pm25)
        if len(self._window) > 240:         # cap at 10 days of hourly readings
            self._window.pop(0)

        if len(self._window) >= 3:
            arr  = np.array(self._window)
            mean = float(arr.mean())
            std  = float(arr.std()) or 1.0
            z    = abs((pm25 - mean) / std)
        else:
            # Not enough data — use city-level baseline
            z = abs(pm25 - city_mean) / max(city_mean * 0.4, 1.0)

        is_anom = z > 3.0
        dummy_score = -1.0 if is_anom else 0.1   # mimic IF range

        return {
            "is_anomaly":    is_anom,
            "anomaly_score": round(dummy_score, 4),
            "z_score":       round(z, 2),
            "flagged_reason": _explain(pm25, city_mean, is_anom),
            "method":        "z_score",
        }

    # ------------------------------------------------------------------
    # Batch processing
    # ------------------------------------------------------------------

    def detect_batch(self, readings: List[Dict]) -> List[Dict]:
        """Run anomaly detection on a list of readings."""
        return [self.detect(r) for r in readings]

    def reset_window(self) -> None:
        """Clear the rolling Z-score window."""
        self._window.clear()

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> Dict:
        return {
            "model":        "AnomalyDetector",
            "backend":      "isolation_forest" if self._loaded else "z_score",
            "contamination": self.CONTAMINATION,
            "window_size":  len(self._window),
            "status":       "ok" if self._loaded else "degraded",
        }


def _explain(pm25: float, city_mean: float, is_anomaly: bool) -> str:
    if not is_anomaly:
        return "Reading is within expected range."
    ratio = pm25 / max(city_mean, 1.0)
    if ratio > 5:
        return "Extreme PM2.5 spike — possible sensor malfunction or catastrophic event."
    if ratio > 2:
        return "PM2.5 significantly above city baseline — possible pollution event."
    if pm25 < 0:
        return "Negative PM2.5 value — sensor calibration error."
    return "Unusual pattern detected — recommend cross-validation with adjacent sensors."
