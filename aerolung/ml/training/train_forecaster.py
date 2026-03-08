"""
AeroLung — LSTM AQI Forecaster Training Script
================================================
Trains a multi-step LSTM model on EPA AQS PM2.5 data.

Usage
-----
    python -m aerolung.ml.training.train_forecaster [--epochs 50] [--batch-size 64]

Outputs
-------
    aerolung/ml/saved_models/lstm_aqi_forecaster/model.keras
    aerolung/ml/saved_models/lstm_aqi_forecaster/scaler.joblib
    aerolung/ml/saved_models/lstm_aqi_forecaster/training_metrics.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from tqdm import tqdm

# Resolve project root
_ROOT     = Path(__file__).parent.parent
_DATA_DIR = _ROOT / "data" / "raw" / "epa"
_SAVE_DIR = _ROOT / "saved_models" / "lstm_aqi_forecaster"

sys.path.insert(0, str(_ROOT.parent.parent))
from aerolung.ml.data.preprocessors import preprocess_epa_data

try:
    import tensorflow as tf
    from tensorflow.keras import callbacks as keras_callbacks
    from tensorflow.keras.layers import (
        LSTM, Dense, Dropout, Input, Bidirectional, BatchNormalization
    )
    from tensorflow.keras.models import Model
    from tensorflow.keras.optimizers import Adam
    _TF_OK = True
except ImportError:
    _TF_OK = False
    logger.error("TensorFlow not installed. Run: pip install tensorflow>=2.13")


def build_lstm_model(look_back: int, horizon: int) -> "tf.keras.Model":
    """Bidirectional LSTM with dropout for multi-step PM2.5 forecasting."""
    inp = Input(shape=(look_back, 1))
    x   = Bidirectional(LSTM(128, return_sequences=True))(inp)
    x   = BatchNormalization()(x)
    x   = Dropout(0.3)(x)
    x   = Bidirectional(LSTM(64, return_sequences=False))(x)
    x   = BatchNormalization()(x)
    x   = Dropout(0.2)(x)
    x   = Dense(64, activation="relu")(x)
    x   = Dense(32, activation="relu")(x)
    out = Dense(horizon)(x)
    model = Model(inputs=inp, outputs=out, name="aqi_lstm_forecaster")
    model.compile(
        optimizer=Adam(learning_rate=1e-3),
        loss="huber",
        metrics=["mae"],
    )
    return model


def load_or_generate_data(data_dir: Path) -> pd.DataFrame:
    """Load EPA CSV or generate synthetic fallback."""
    csv = data_dir / "epa_pm25_merged.csv"
    if csv.exists():
        logger.info(f"Loading EPA data from {csv}")
        df = pd.read_csv(csv, parse_dates=["Date Local"])
        return df
    logger.warning("EPA data not found — generating synthetic PM2.5 data.")
    rng  = np.random.default_rng(42)
    n    = 8760    # 1 year hourly
    t    = np.linspace(0, 4 * np.pi, n)
    base = 20 + 15 * np.sin(t) + 5 * np.cos(3 * t)
    noise = rng.normal(0, 3, n)
    pm25  = np.clip(base + noise, 0, 300)
    dates = pd.date_range("2023-01-01", periods=n, freq="h")
    return pd.DataFrame({"Date Local": dates, "Arithmetic Mean": pm25})


def train(
    epochs: int       = 50,
    batch_size: int   = 64,
    look_back: int    = 24,
    horizon: int      = 1,
    patience: int     = 8,
) -> dict:
    if not _TF_OK:
        raise RuntimeError("TensorFlow is required. Install requirements_ml.txt first.")

    _SAVE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    df       = load_or_generate_data(_DATA_DIR)
    datasets = preprocess_epa_data(df, look_back=look_back)

    X_train, y_train = datasets["X_train"], datasets["y_train"]
    X_val,   y_val   = datasets["X_val"],   datasets["y_val"]
    X_test,  y_test  = datasets["X_test"],  datasets["y_test"]
    scaler           = datasets["scaler"]

    logger.info(f"Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")

    # 2. Build model
    model = build_lstm_model(look_back, horizon)
    model.summary(print_fn=logger.info)

    # 3. Callbacks
    cb = [
        keras_callbacks.EarlyStopping(patience=patience, restore_best_weights=True, verbose=1),
        keras_callbacks.ReduceLROnPlateau(factor=0.5, patience=4, min_lr=1e-6, verbose=1),
        keras_callbacks.ModelCheckpoint(
            str(_SAVE_DIR / "best_model.keras"),
            save_best_only=True,
            monitor="val_mae",
            verbose=1,
        ),
    ]

    # 4. Train
    logger.info(f"Training LSTM: {epochs} epochs, batch size {batch_size}")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs, batch_size=batch_size,
        callbacks=cb, verbose=1,
    )

    # 5. Evaluate on test set
    test_loss, test_mae   = model.evaluate(X_test, y_test, verbose=0)
    y_pred   = model.predict(X_test).flatten()
    y_true   = y_test.flatten()
    # Inverse transform for true µg/m³ MAE
    pred_inv = scaler.inverse_transform(y_pred.reshape(-1, 1)).flatten()
    true_inv = scaler.inverse_transform(y_true.reshape(-1, 1)).flatten()
    mae_ug   = float(np.mean(np.abs(pred_inv - true_inv)))
    rmse_ug  = float(np.sqrt(np.mean((pred_inv - true_inv) ** 2)))

    logger.info(f"Test MAE: {mae_ug:.2f} µg/m³  RMSE: {rmse_ug:.2f} µg/m³")

    # 6. Save artefacts
    model.save(str(_SAVE_DIR / "model.keras"))
    joblib.dump(scaler, _SAVE_DIR / "scaler.joblib")

    metrics = {
        "test_loss":    float(test_loss),
        "test_mae_scaled": float(test_mae),
        "test_mae_ugm3":   round(mae_ug, 3),
        "test_rmse_ugm3":  round(rmse_ug, 3),
        "epochs_trained":  len(history.history["loss"]),
        "look_back":    look_back,
        "horizon":      horizon,
        "batch_size":   batch_size,
    }
    with open(_SAVE_DIR / "training_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    logger.success(f"LSTM model saved → {_SAVE_DIR / 'model.keras'}")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train AQI LSTM forecaster")
    parser.add_argument("--epochs",      type=int, default=50)
    parser.add_argument("--batch-size",  type=int, default=64)
    parser.add_argument("--look-back",   type=int, default=24, help="Hours of history")
    parser.add_argument("--horizon",     type=int, default=1,  help="Steps to forecast")
    parser.add_argument("--patience",    type=int, default=8,  help="Early-stopping patience")
    args = parser.parse_args()

    metrics = train(
        epochs=args.epochs,
        batch_size=args.batch_size,
        look_back=args.look_back,
        horizon=args.horizon,
        patience=args.patience,
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
