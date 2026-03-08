"""
AeroLung — Anomaly Detector Training Script (Isolation Forest)
===============================================================
Trains an Isolation Forest on OpenAQ PM2.5 sensor data to detect
anomalous readings (sensor faults, pollution spikes, data corruption).

Usage
-----
    python -m aerolung.ml.training.train_anomaly [--contamination 0.05]

Outputs
-------
    aerolung/ml/saved_models/isolation_forest.joblib
    aerolung/ml/saved_models/if_scaler.joblib
    aerolung/ml/saved_models/if_metrics.json
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
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

_ROOT     = Path(__file__).parent.parent
_DATA_DIR = _ROOT / "data" / "raw" / "openaq"
_SAVE_DIR = _ROOT / "saved_models"

sys.path.insert(0, str(_ROOT.parent.parent))


def load_openaq(data_dir: Path) -> pd.DataFrame:
    csv = data_dir / "openaq_pm25_2023.csv"
    if csv.exists():
        logger.info(f"Loading OpenAQ data from {csv}")
        df = pd.read_csv(csv, parse_dates=["datetime"])
        return df

    logger.warning("OpenAQ CSV not found — generating synthetic sensor data.")
    rng = np.random.default_rng(42)
    n   = 10_000
    cities = ["Delhi", "Beijing", "Jakarta", "Karachi", "Cairo",
              "São Paulo", "Mexico City", "Lagos", "Dhaka", "Bangkok"]
    city_means = [115, 75, 55, 95, 80, 30, 25, 60, 120, 35]
    city_idx   = rng.integers(0, len(cities), n)

    means = np.array([city_means[i] for i in city_idx], dtype=float)
    pm25  = means + rng.normal(0, means * 0.2, n)
    # Inject ~5% anomalies
    anom_mask           = rng.random(n) < 0.05
    pm25[anom_mask]     = rng.choice([rng.uniform(800, 1000, anom_mask.sum()),
                                      rng.uniform(-10, -1, anom_mask.sum())],
                                     axis=0)[0]
    datetimes = pd.date_range("2023-01-01", periods=n, freq="h")

    df = pd.DataFrame({
        "datetime":      datetimes,
        "pm25":          pm25.clip(-20, 1200),
        "city":          [cities[i] for i in city_idx],
        "is_anomaly":    anom_mask.astype(int),
    })
    return df


def build_features(df: pd.DataFrame) -> np.ndarray:
    """Construct feature matrix from OpenAQ DataFrame."""
    city_means = {
        "Delhi": 115, "Beijing": 75, "Jakarta": 55, "Karachi": 95, "Cairo": 80,
        "São Paulo": 30, "Mexico City": 25, "Lagos": 60, "Dhaka": 120, "Bangkok": 35,
    }

    pm25 = df["pm25"].values.astype(float)

    if "datetime" in df.columns:
        dt   = pd.to_datetime(df["datetime"])
        hour = dt.dt.hour.values
        dow  = dt.dt.dayofweek.values
    else:
        hour = np.zeros(len(df), dtype=int)
        dow  = np.zeros(len(df), dtype=int)

    city_mean_arr = np.array([city_means.get(c, 30) for c in df.get("city", ["Unknown"] * len(df))], dtype=float)
    relative_pm25 = pm25 - city_mean_arr
    hour_sin = np.sin(2 * np.pi * hour / 24)
    hour_cos = np.cos(2 * np.pi * hour / 24)
    dow_sin  = np.sin(2 * np.pi * dow  / 7)
    dow_cos  = np.cos(2 * np.pi * dow  / 7)

    return np.column_stack([pm25, relative_pm25, hour_sin, hour_cos, dow_sin, dow_cos])


def train(
    contamination: float  = 0.05,
    n_estimators: int     = 200,
    max_features: float   = 1.0,
    max_samples: str      = "auto",
    random_state: int     = 42,
) -> dict:
    _SAVE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    df = load_openaq(_DATA_DIR)
    logger.info(f"OpenAQ data: {len(df):,} rows")

    # 2. Features
    X      = build_features(df)
    scaler = StandardScaler()
    X_sc   = scaler.fit_transform(X)

    # 3. Train
    logger.info(f"Fitting Isolation Forest (n_estimators={n_estimators}, contamination={contamination})…")
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        max_features=max_features,
        max_samples=max_samples,
        random_state=random_state,
        n_jobs=-1,
        verbose=1,
    )
    model.fit(X_sc)

    # 4. Evaluate (if ground-truth available)
    metrics: dict = {
        "n_training_samples": len(df),
        "contamination":      contamination,
        "n_estimators":       n_estimators,
    }

    if "is_anomaly" in df.columns:
        y_true   = df["is_anomaly"].values
        scores   = model.score_samples(X_sc)          # lower = more anomalous
        preds    = model.predict(X_sc)                 # -1 = anomaly, 1 = normal
        pred_bin = (preds == -1).astype(int)

        # AUC and AP (negate scores because lower = more anomalous)
        try:
            auc = roc_auc_score(y_true, -scores)
            ap  = average_precision_score(y_true, -scores)
        except Exception:
            auc, ap = 0.0, 0.0

        precision = float((pred_bin[y_true == 1]).mean()) if y_true.sum() > 0 else 0.0
        recall    = float((y_true[pred_bin == 1]).mean()) if pred_bin.sum() > 0 else 0.0

        logger.info(f"Anomaly AUC: {auc:.4f}  AP: {ap:.4f}  Precision: {precision:.4f}  Recall: {recall:.4f}")
        metrics.update({
            "auc":       round(auc, 4),
            "ap":        round(ap,  4),
            "precision": round(precision, 4),
            "recall":    round(recall,    4),
        })
    else:
        logger.info("No ground-truth anomaly labels — skipping classification metrics.")

    # 5. Save
    joblib.dump(model,  _SAVE_DIR / "isolation_forest.joblib")
    joblib.dump(scaler, _SAVE_DIR / "if_scaler.joblib")

    with open(_SAVE_DIR / "if_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    logger.success(f"AnomalyDetector saved → {_SAVE_DIR / 'isolation_forest.joblib'}")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Isolation Forest anomaly detector")
    parser.add_argument("--contamination", type=float, default=0.05, help="Expected anomaly fraction")
    parser.add_argument("--n-estimators",  type=int,   default=200)
    parser.add_argument("--max-features",  type=float, default=1.0)
    parser.add_argument("--seed",          type=int,   default=42)
    args = parser.parse_args()

    metrics = train(
        contamination=args.contamination,
        n_estimators=args.n_estimators,
        max_features=args.max_features,
        random_state=args.seed,
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
