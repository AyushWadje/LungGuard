"""
AeroLung — AQI Forecaster (LSTM)
=================================
Loads a saved Keras/TensorFlow LSTM model and generates multi-step
PM2.5 / AQI forecasts with confidence intervals.

If the saved model is absent the class falls back to an exponential
smoothing estimator so the pipeline degrades gracefully.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

# Optional heavy imports — handled gracefully
try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model as _keras_load
    _TF_AVAILABLE = True
except ImportError:
    _TF_AVAILABLE = False

try:
    import joblib
    _JOBLIB_AVAILABLE = True
except ImportError:
    _JOBLIB_AVAILABLE = False

_MODEL_DIR = Path(__file__).parent.parent / "saved_models" / "lstm_aqi_forecaster"
_SCALER_PATH = _MODEL_DIR / "scaler.joblib"
_KERAS_PATH  = _MODEL_DIR / "model.keras"          # SavedModel format
_H5_PATH     = _MODEL_DIR / "model.h5"             # legacy HDF5 fallback


class AQIForecaster:
    """
    Multi-step PM2.5 / AQI LSTM forecaster.

    Usage
    -----
    >>> fc = AQIForecaster()
    >>> result = fc.forecast(recent_pm25_readings=[12.0, 14.5, 18.2, ...], steps=3)
    >>> result["forecasts"]   # list of predicted PM2.5 values
    >>> result["confidence"]  # list of ±σ confidence intervals
    """

    LOOK_BACK: int = 24          # hours of history required
    DEFAULT_STEPS: int = 3       # forecast horizon (hours)

    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or _MODEL_DIR
        self._model  = None
        self._scaler = None
        self._loaded = False
        self._load()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Attempt to load the LSTM model and scaler from disk."""
        scaler_path = self.model_dir / "scaler.joblib"
        keras_path  = self.model_dir / "model.keras"
        h5_path     = self.model_dir / "model.h5"

        # Load scaler
        if _JOBLIB_AVAILABLE and scaler_path.exists():
            import joblib
            self._scaler = joblib.load(scaler_path)
            logger.debug("AQI scaler loaded.")
        else:
            logger.debug("AQI scaler not found — will use raw values.")

        # Load Keras model
        if _TF_AVAILABLE:
            for path in (keras_path, h5_path):
                if path.exists():
                    try:
                        self._model = _keras_load(str(path))
                        logger.info(f"LSTM AQI model loaded from {path.name}")
                        self._loaded = True
                        return
                    except Exception as exc:
                        logger.warning(f"Could not load {path.name}: {exc}")

        if not self._loaded:
            warnings.warn(
                "AQIForecaster: No LSTM model found. "
                "Falling back to exponential smoothing. "
                "Run aerolung/ml/training/train_forecaster.py to train.",
                UserWarning,
                stacklevel=3,
            )

    @property
    def is_ready(self) -> bool:
        return self._loaded

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def forecast(
        self,
        recent_pm25_readings: List[float],
        steps: int = DEFAULT_STEPS,
    ) -> Dict:
        """
        Forecast PM2.5 levels for the next *steps* hours.

        Parameters
        ----------
        recent_pm25_readings : list of float
            Recent hourly PM2.5 readings.  At least LOOK_BACK values
            required; extras are ignored (only the most recent are used).
        steps : int
            Number of hours ahead to forecast.

        Returns
        -------
        dict with keys:
          forecasts   list[float]   predicted PM2.5 per step
          confidence  list[float]   ±1σ uncertainty per step
          method      str           "lstm" or "exponential_smoothing"
          aqi_values  list[int]     EPA AQI integer per step
        """
        arr = np.array(recent_pm25_readings, dtype=float)
        arr = np.clip(arr, 0, 1000)

        # Pad or trim to LOOK_BACK
        if len(arr) < self.LOOK_BACK:
            arr = np.pad(arr, (self.LOOK_BACK - len(arr), 0), mode="edge")
        arr = arr[-self.LOOK_BACK:]

        if self._loaded and self._model is not None:
            return self._lstm_forecast(arr, steps)
        return self._fallback_forecast(arr, steps)

    def _scale(self, x: np.ndarray) -> np.ndarray:
        if self._scaler is not None:
            return self._scaler.transform(x.reshape(-1, 1)).flatten()
        return x / 300.0          # rough normalisation if no scaler

    def _inverse_scale(self, x: np.ndarray) -> np.ndarray:
        if self._scaler is not None:
            return self._scaler.inverse_transform(x.reshape(-1, 1)).flatten()
        return x * 300.0

    def _lstm_forecast(self, arr: np.ndarray, steps: int) -> Dict:
        forecasts, confidences = [], []
        current = self._scale(arr).copy()

        for _ in range(steps):
            X = current[-self.LOOK_BACK:].reshape(1, self.LOOK_BACK, 1)
            # Monte-Carlo dropout: 20 forward passes
            preds = np.array([self._model(X, training=True).numpy()[0, 0] for _ in range(20)])
            mean_pred = float(preds.mean())
            std_pred  = float(preds.std())

            raw_val = float(self._inverse_scale(np.array([mean_pred]))[0])
            raw_val = max(0.0, raw_val)
            conf    = float(self._inverse_scale(np.array([std_pred]))[0])

            forecasts.append(round(raw_val, 2))
            confidences.append(round(abs(conf), 2))
            current = np.append(current, mean_pred)

        return {
            "forecasts":  forecasts,
            "confidence": confidences,
            "method":     "lstm",
            "aqi_values": [_pm25_to_aqi(v) for v in forecasts],
        }

    def _fallback_forecast(self, arr: np.ndarray, steps: int) -> Dict:
        """Holt (double) exponential smoothing fallback."""
        alpha   = 0.3
        beta    = 0.1
        level   = arr[-1]
        trend   = arr[-1] - arr[-2] if len(arr) > 1 else 0.0
        forecasts, confidences = [], []
        residuals = np.diff(arr)
        base_std  = float(residuals.std()) if len(residuals) > 1 else 2.0

        for i in range(1, steps + 1):
            forecast_val = level + i * trend
            forecast_val = max(0.0, float(forecast_val))
            forecasts.append(round(forecast_val, 2))
            confidences.append(round(base_std * np.sqrt(i), 2))

        return {
            "forecasts":  forecasts,
            "confidence": confidences,
            "method":     "exponential_smoothing",
            "aqi_values": [_pm25_to_aqi(v) for v in forecasts],
        }

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> Dict:
        return {
            "model":      "AQIForecaster",
            "backend":    "lstm" if self._loaded else "exponential_smoothing",
            "look_back":  self.LOOK_BACK,
            "tf_available": _TF_AVAILABLE,
            "status":     "ok" if self._loaded else "degraded",
        }


# ---------------------------------------------------------------------------
# EPA AQI conversion helper (mirrored from main.py)
# ---------------------------------------------------------------------------

def _pm25_to_aqi(pm25: float) -> int:
    if pm25 <= 12.0:   return int((50 / 12.0) * pm25)
    if pm25 <= 35.4:   return int(50  + ((100 - 50)  / (35.4 - 12.1))  * (pm25 - 12.1))
    if pm25 <= 55.4:   return int(100 + ((150 - 100) / (55.4 - 35.5))  * (pm25 - 35.5))
    if pm25 <= 150.4:  return int(150 + ((200 - 150) / (150.4 - 55.5)) * (pm25 - 55.5))
    if pm25 <= 250.4:  return int(200 + ((300 - 200) / (250.4 - 150.5))* (pm25 - 150.5))
    return min(500, int(300 + (pm25 - 250.5) * 0.99))
