"""
AeroLung — Health Risk Scorer Training Script (XGBoost)
=========================================================
Trains an XGBoost binary classifier on NHANES data to predict
individual respiratory health-risk probability.

Usage
-----
    python -m aerolung.ml.training.train_health_risk [--n-estimators 500]

Outputs
-------
    aerolung/ml/saved_models/xgb_health_risk.joblib
    aerolung/ml/saved_models/xgb_hr_scaler.joblib
    aerolung/ml/saved_models/xgb_hr_feature_importance.json
    aerolung/ml/saved_models/xgb_hr_metrics.json
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
from sklearn.metrics import (
    accuracy_score, roc_auc_score, classification_report,
    average_precision_score,
)
from sklearn.model_selection import StratifiedKFold

_ROOT     = Path(__file__).parent.parent
_DATA_DIR = _ROOT / "data" / "raw" / "nhanes"
_SAVE_DIR = _ROOT / "saved_models"

sys.path.insert(0, str(_ROOT.parent.parent))
from aerolung.ml.data.preprocessors import preprocess_nhanes_data
from aerolung.ml.models.health_risk_scorer import FEATURE_NAMES

try:
    import xgboost as xgb
    _XGB_OK = True
except ImportError:
    _XGB_OK = False
    logger.error("XGBoost not installed. Run: pip install xgboost")


def load_nhanes(data_dir: Path) -> pd.DataFrame:
    csv = data_dir / "nhanes_merged.csv"
    if csv.exists():
        logger.info(f"Loading NHANES data from {csv}")
        return pd.read_csv(csv)
    logger.warning("NHANES CSV not found — generating synthetic data.")
    rng  = np.random.default_rng(42)
    n    = 5000
    data = {
        "age":           rng.integers(18, 80, n),
        "gender":        rng.integers(1, 3, n),
        "race":          rng.integers(1, 6, n),
        "income_ratio":  rng.uniform(0.5, 5.0, n),
        "fev1":          rng.uniform(1.5, 5.5, n),
        "fvc":           rng.uniform(2.0, 7.0, n),
        "fev1_fvc_ratio":rng.uniform(0.50, 0.95, n),
        "ever_smoked":   rng.integers(1, 3, n),
        "current_smoker":rng.integers(1, 4, n),
        "asthma_ever":   rng.integers(1, 3, n),
        "copd":          rng.integers(1, 3, n),
        "systolic_bp":   rng.integers(90, 180, n),
        "diastolic_bp":  rng.integers(55, 110, n),
        "pulse_rate":    rng.integers(50, 110, n),
        "bmi":           rng.uniform(17.0, 45.0, n),
    }
    df = pd.DataFrame(data)
    # Synthetic label: high risk if copd=1 OR asthma=1 OR fev1_fvc<0.70
    df["risk_label"] = (
        (df["copd"] == 1) | (df["asthma_ever"] == 1) | (df["fev1_fvc_ratio"] < 0.70)
    ).astype(int)
    return df


def train(
    n_estimators: int     = 500,
    max_depth: int        = 6,
    learning_rate: float  = 0.05,
    cv_folds: int         = 5,
    early_stopping: int   = 40,
) -> dict:
    if not _XGB_OK:
        raise RuntimeError("XGBoost is required. Install requirements_ml.txt first.")

    _SAVE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    df = load_nhanes(_DATA_DIR)
    datasets = preprocess_nhanes_data(df)
    X_train, y_train = datasets["X_train"], datasets["y_train"]
    X_val,   y_val   = datasets["X_val"],   datasets["y_val"]
    X_test,  y_test  = datasets["X_test"],  datasets["y_test"]
    scaler           = datasets.get("scaler")

    logger.info(f"Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")
    logger.info(f"Positive class rate (train): {y_train.mean():.2%}")

    # 2. Scale weight for imbalanced data
    pos_rate = float(y_train.mean())
    scale_pos = (1.0 - pos_rate) / max(pos_rate, 1e-6)

    # 3. Build model
    model = xgb.XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        scale_pos_weight=scale_pos,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        use_label_encoder=False,
        eval_metric="aucpr",
        early_stopping_rounds=early_stopping,
        random_state=42,
        n_jobs=-1,
    )

    # 4. Fit
    logger.info("Fitting XGBoost health risk model…")
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=50,
    )

    # 5. CV evaluation
    skf  = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    auc_scores = []
    X_all = np.vstack([X_train, X_val])
    y_all = np.hstack([y_train, y_val])
    for fold, (tr_idx, va_idx) in enumerate(skf.split(X_all, y_all)):
        fold_model = xgb.XGBClassifier(
            n_estimators=model.best_iteration or n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            scale_pos_weight=scale_pos,
            use_label_encoder=False,
            eval_metric="auc",
            random_state=42,
            n_jobs=-1,
        )
        fold_model.fit(X_all[tr_idx], y_all[tr_idx], verbose=False)
        preds = fold_model.predict_proba(X_all[va_idx])[:, 1]
        auc_scores.append(roc_auc_score(y_all[va_idx], preds))
    logger.info(f"CV AUC: {np.mean(auc_scores):.4f} ± {np.std(auc_scores):.4f}")

    # 6. Test metrics
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred       = (y_pred_proba > 0.5).astype(int)
    auc          = roc_auc_score(y_test, y_pred_proba)
    ap           = average_precision_score(y_test, y_pred_proba)
    acc          = accuracy_score(y_test, y_pred)
    report_str   = classification_report(y_test, y_pred)
    logger.info(f"Test AUC: {auc:.4f}  AP: {ap:.4f}  Acc: {acc:.4f}")
    logger.info(f"\n{report_str}")

    # 7. Save
    joblib.dump(model, _SAVE_DIR / "xgb_health_risk.joblib")
    if scaler is not None:
        joblib.dump(scaler, _SAVE_DIR / "xgb_hr_scaler.joblib")

    # Feature importance
    fi = {n: round(float(v), 6) for n, v in zip(FEATURE_NAMES, model.feature_importances_)}
    with open(_SAVE_DIR / "xgb_hr_feature_importance.json", "w") as f:
        json.dump(dict(sorted(fi.items(), key=lambda x: x[1], reverse=True)), f, indent=2)

    metrics = {
        "test_auc":      round(auc,  4),
        "test_ap":       round(ap,   4),
        "test_accuracy": round(acc,  4),
        "cv_auc_mean":   round(float(np.mean(auc_scores)), 4),
        "cv_auc_std":    round(float(np.std(auc_scores)), 4),
        "best_iteration": model.best_iteration or n_estimators,
        "n_estimators":  n_estimators,
        "max_depth":     max_depth,
        "learning_rate": learning_rate,
    }
    with open(_SAVE_DIR / "xgb_hr_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    logger.success(f"HealthRiskScorer saved → {_SAVE_DIR / 'xgb_health_risk.joblib'}")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train XGBoost health risk scorer")
    parser.add_argument("--n-estimators",  type=int,   default=500)
    parser.add_argument("--max-depth",     type=int,   default=6)
    parser.add_argument("--lr",            type=float, default=0.05)
    parser.add_argument("--cv-folds",      type=int,   default=5)
    parser.add_argument("--early-stopping",type=int,   default=40)
    args = parser.parse_args()

    metrics = train(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.lr,
        cv_folds=args.cv_folds,
        early_stopping=args.early_stopping,
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
