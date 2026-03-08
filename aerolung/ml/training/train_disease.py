"""
AeroLung — Disease Predictor Training Script (XGBoost Multi-label)
===================================================================
Trains one XGBoost binary classifier per disease label on NHANES data.

Diseases: asthma_exacerbation, copd_flare_up,
          pulmonary_hypertension, respiratory_infection

Usage
-----
    python -m aerolung.ml.training.train_disease [--n-estimators 400]

Outputs
-------
    aerolung/ml/saved_models/xgb_disease_predictor.joblib   # dict of 4 models
    aerolung/ml/saved_models/xgb_disease_scaler.joblib
    aerolung/ml/saved_models/xgb_disease_metrics.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

_ROOT     = Path(__file__).parent.parent
_DATA_DIR = _ROOT / "data" / "raw" / "nhanes"
_SAVE_DIR = _ROOT / "saved_models"

sys.path.insert(0, str(_ROOT.parent.parent))
from aerolung.ml.models.disease_predictor import DISEASE_LABELS, FEATURE_NAMES

try:
    import xgboost as xgb
    _XGB_OK = True
except ImportError:
    _XGB_OK = False
    logger.error("XGBoost not installed.")


def load_nhanes_with_env(data_dir: Path) -> pd.DataFrame:
    csv = data_dir / "nhanes_merged.csv"
    if csv.exists():
        df = pd.read_csv(csv)
    else:
        logger.warning("NHANES CSV not found — generating synthetic data.")
        rng = np.random.default_rng(42)
        n   = 5000
        df  = pd.DataFrame({
            "age":           rng.integers(18, 80, n),
            "bmi":           rng.uniform(17, 45, n),
            "fev1_fvc_ratio":rng.uniform(0.50, 0.95, n),
            "asthma_ever":   rng.integers(0, 2, n),
            "copd":          rng.integers(0, 2, n),
            "current_smoker":rng.integers(0, 2, n),
            "systolic_bp":   rng.integers(90, 180, n),
            "pulse_rate":    rng.integers(50, 110, n),
            "spo2":          rng.uniform(90, 99, n),
            "heart_rate":    rng.integers(55, 110, n),
            "breathing_rate":rng.integers(12, 28, n),
        })

    # Add synthetic environmental context
    rng = np.random.default_rng(0)
    n   = len(df)
    df["pm25"] = rng.exponential(20, n).clip(0, 300)
    df["pm10"] = df["pm25"] * rng.uniform(1.2, 2.5, n)
    df["o3"]   = rng.uniform(10, 80, n)
    df["no2"]  = rng.uniform(5,  60, n)

    # Ensure feature columns exist
    for col in FEATURE_NAMES:
        if col not in df.columns:
            df[col] = 0.0

    # Create disease labels
    fev = df.get("fev1_fvc_ratio", 0.78)
    copd_col    = df.get("copd", 0)
    asthma_col  = df.get("asthma_ever", 0)
    smoker_col  = df.get("current_smoker", 0)
    pm25_col    = df.get("pm25", 15)
    spo2_col    = df.get("spo2", 97)
    age_col     = df.get("age", 40)

    df["asthma_exacerbation"]  = ((asthma_col == 1) | (fev < 0.70) | (pm25_col > 55)).astype(int)
    df["copd_flare_up"]        = ((copd_col == 1)   | (fev < 0.65) | (smoker_col == 1)).astype(int)
    df["pulmonary_hypertension"] = ((spo2_col < 92) | (age_col > 65)).astype(int)
    df["respiratory_infection"]  = ((pm25_col > 75) | (smoker_col == 1) | (age_col > 70)).astype(int)

    return df


def train_per_label(
    df: pd.DataFrame,
    n_estimators: int   = 400,
    max_depth: int      = 5,
    learning_rate: float= 0.05,
) -> Dict:
    X = df[FEATURE_NAMES].values.astype(float)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    models: Dict[str, object] = {}
    all_metrics: Dict[str, dict] = {}

    for label in DISEASE_LABELS:
        y = df[label].values if label in df.columns else np.zeros(len(df), dtype=int)

        X_tr, X_te, y_tr, y_te = train_test_split(
            X_scaled, y, test_size=0.20, stratify=y, random_state=42
        )
        X_tr, X_val, y_tr, y_val = train_test_split(
            X_tr, y_tr, test_size=0.15, stratify=y_tr, random_state=42
        )

        pos_rate    = float(y_tr.mean()) or 0.01
        scale_pos   = (1 - pos_rate) / pos_rate

        clf = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            scale_pos_weight=scale_pos,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="aucpr",
            early_stopping_rounds=30,
            random_state=42,
            n_jobs=-1,
        )
        clf.fit(
            X_tr, y_tr,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        y_prob = clf.predict_proba(X_te)[:, 1]
        auc    = roc_auc_score(y_te, y_prob) if len(np.unique(y_te)) > 1 else 0.0
        ap     = average_precision_score(y_te, y_prob) if len(np.unique(y_te)) > 1 else 0.0

        logger.info(f"[{label}] AUC={auc:.4f}  AP={ap:.4f}  best_iter={clf.best_iteration}")
        models[label] = clf
        all_metrics[label] = {
            "auc":          round(auc, 4),
            "ap":           round(ap,  4),
            "best_iter":    clf.best_iteration,
            "pos_rate":     round(pos_rate, 4),
        }

    return models, scaler, all_metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train XGBoost disease predictor")
    parser.add_argument("--n-estimators",  type=int,   default=400)
    parser.add_argument("--max-depth",     type=int,   default=5)
    parser.add_argument("--lr",            type=float, default=0.05)
    args = parser.parse_args()

    if not _XGB_OK:
        logger.error("XGBoost not installed. Aborting.")
        sys.exit(1)

    _SAVE_DIR.mkdir(parents=True, exist_ok=True)

    df = load_nhanes_with_env(_DATA_DIR)
    logger.info(f"Data shape: {df.shape}")

    models, scaler, metrics = train_per_label(
        df,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.lr,
    )

    joblib.dump(models, _SAVE_DIR / "xgb_disease_predictor.joblib")
    joblib.dump(scaler, _SAVE_DIR / "xgb_disease_scaler.joblib")

    with open(_SAVE_DIR / "xgb_disease_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    logger.success(f"DiseasePredictor models saved → {_SAVE_DIR / 'xgb_disease_predictor.joblib'}")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
