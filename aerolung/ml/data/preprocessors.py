"""
AeroLung — Data Preprocessors
Shared preprocessing utilities used by all training scripts.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.preprocessing import MinMaxScaler, StandardScaler


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------
DATA_ROOT = Path(__file__).parent
PROCESSED_DIR = DATA_ROOT / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Time-series windowing (for LSTM AQI forecaster)
# ---------------------------------------------------------------------------

def create_sequences(
    data: np.ndarray,
    look_back: int = 24,
    forecast_horizon: int = 1,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Slice a 1-D or 2-D array of measurements into (X, y) windows.

    Args:
        data: shape (n_timesteps,) or (n_timesteps, n_features)
        look_back: number of past time steps used as input
        forecast_horizon: number of future steps to predict

    Returns:
        X: shape (n_samples, look_back, n_features)
        y: shape (n_samples, forecast_horizon)
    """
    if data.ndim == 1:
        data = data.reshape(-1, 1)

    X, y = [], []
    for i in range(len(data) - look_back - forecast_horizon + 1):
        X.append(data[i : i + look_back])
        y.append(data[i + look_back : i + look_back + forecast_horizon, 0])

    return np.array(X), np.array(y)


# ---------------------------------------------------------------------------
# AQI / EPA data cleaning
# ---------------------------------------------------------------------------

def preprocess_epa_data(df: pd.DataFrame, look_back: int = 24) -> dict:
    """
    Clean and window the merged EPA PM2.5 CSV for LSTM training.

    Steps
    -----
    1.  Sort by timestamp
    2.  Resample to hourly median (fill gaps with forward-fill, max 3 h)
    3.  Remove outliers via 99th-percentile cap
    4.  Normalise to [0, 1] using MinMaxScaler
    5.  Create (X, y) sequences with look_back window

    Returns a dict with keys: X_train, X_val, X_test, y_train, y_val,
    y_test, scaler, feature_names
    """
    logger.info("Preprocessing EPA data …")
    df = df.copy()

    # Ensure timestamp column exists
    if "timestamp" not in df.columns:
        df["timestamp"] = pd.to_datetime(
            df["date"].astype(str) + " " + df["time"].astype(str),
            errors="coerce",
        )
    df = df.dropna(subset=["timestamp", "pm25"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Outlier cap
    cap = df["pm25"].quantile(0.99)
    df["pm25"] = df["pm25"].clip(0, cap)

    # Hourly resample (group to site-level mean first, then time)
    df.set_index("timestamp", inplace=True)
    hourly = df["pm25"].resample("1H").median().ffill(limit=3).dropna()
    hourly = hourly.reset_index()
    hourly.columns = ["timestamp", "pm25"]

    values = hourly["pm25"].values.reshape(-1, 1)

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(values)

    X, y = create_sequences(scaled, look_back=look_back, forecast_horizon=1)

    n = len(X)
    train_end = int(n * 0.70)
    val_end   = int(n * 0.85)

    result = {
        "X_train": X[:train_end],
        "X_val":   X[train_end:val_end],
        "X_test":  X[val_end:],
        "y_train": y[:train_end],
        "y_val":   y[train_end:val_end],
        "y_test":  y[val_end:],
        "scaler":  scaler,
        "feature_names": ["pm25"],
    }
    logger.info(
        f"EPA sequences — train={result['X_train'].shape}, "
        f"val={result['X_val'].shape}, test={result['X_test'].shape}"
    )
    return result


# ---------------------------------------------------------------------------
# NHANES health data cleaning
# ---------------------------------------------------------------------------

NHANES_FEATURE_COLS = [
    "age", "gender", "race", "income_ratio",
    "fev1", "fvc", "fev1_fvc_ratio",
    "ever_smoked", "current_smoker",
    "asthma_ever", "asthma_still", "copd",
    "heart_attack", "stroke",
    "systolic_bp", "diastolic_bp", "pulse_rate",
    "bmi", "weight", "height",
]

NHANES_TARGET_COLS = ["asthma_still", "copd"]


def preprocess_nhanes_data(df: pd.DataFrame) -> dict:
    """
    Prepare NHANES data for XGBoost health-risk scoring.

    Returns dict with: X_train, X_val, X_test, y_train, y_val, y_test,
    feature_names, scaler
    """
    logger.info("Preprocessing NHANES data …")
    df = df.copy()

    # Clip extreme values
    if "age" in df.columns:
        df = df[(df["age"] >= 18) & (df["age"] <= 90)]
    if "bmi" in df.columns:
        df["bmi"] = df["bmi"].clip(10, 70)
    if "systolic_bp" in df.columns:
        df["systolic_bp"] = df["systolic_bp"].clip(60, 240)

    # Select available feature columns
    available_features = [c for c in NHANES_FEATURE_COLS if c in df.columns]
    target = "asthma_still" if "asthma_still" in df.columns else available_features[-1]

    df_clean = df[available_features].copy()
    df_clean = df_clean.fillna(df_clean.median(numeric_only=True))

    X = df_clean.drop(columns=[target], errors="ignore").values
    y = df[target].fillna(0).astype(int).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    n = len(X_scaled)
    train_end = int(n * 0.70)
    val_end   = int(n * 0.85)

    return {
        "X_train": X_scaled[:train_end],
        "X_val":   X_scaled[train_end:val_end],
        "X_test":  X_scaled[val_end:],
        "y_train": y[:train_end],
        "y_val":   y[train_end:val_end],
        "y_test":  y[val_end:],
        "feature_names": [c for c in available_features if c != target],
        "scaler": scaler,
    }


# ---------------------------------------------------------------------------
# OpenAQ anomaly data cleaning
# ---------------------------------------------------------------------------

def preprocess_openaq_data(df: pd.DataFrame) -> dict:
    """
    Prepare OpenAQ data for Isolation Forest anomaly detection.

    Features used: pm25, hour_of_day, day_of_week, city_encoded
    """
    logger.info("Preprocessing OpenAQ data …")
    df = df.copy()

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        df["hour_of_day"]  = df["timestamp"].dt.hour
        df["day_of_week"]  = df["timestamp"].dt.dayofweek

    if "city" in df.columns:
        df["city_encoded"] = df["city"].astype("category").cat.codes
    else:
        df["city_encoded"] = 0

    feature_cols = ["pm25", "hour_of_day", "day_of_week", "city_encoded"]
    available = [c for c in feature_cols if c in df.columns]
    df_clean = df[available].dropna()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_clean.values)

    labels = df.loc[df_clean.index, "is_anomaly"].values if "is_anomaly" in df.columns else None

    return {
        "X": X_scaled,
        "labels": labels,
        "feature_names": available,
        "scaler": scaler,
        "raw_df": df_clean,
    }


# ---------------------------------------------------------------------------
# Medical transcription preprocessing (for LLM fine-tuning)
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Strip HTML tags, collapse whitespace, normalise quotes."""
    text = re.sub(r"<[^>]+>", " ", str(text))
    text = re.sub(r"\s+", " ", text)
    text = text.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    return text.strip()


def preprocess_medical_transcriptions(
    df: pd.DataFrame,
    max_input_length: int = 512,
    max_target_length: int = 256,
) -> pd.DataFrame:
    """
    Prepare the medical transcriptions dataset for Seq2Seq fine-tuning.

    Creates two columns:
      - ``input_text``  : air_quality_context (or description)
      - ``target_text`` : cleaned transcription excerpt (≤ max_target_length words)
    """
    logger.info("Preprocessing medical transcriptions …")
    df = df.copy()

    text_col = "air_quality_context" if "air_quality_context" in df.columns else "transcription"
    df["input_text"]  = df.get("description", df[text_col]).astype(str).apply(clean_text)
    df["target_text"] = df[text_col].astype(str).apply(clean_text)

    # Truncate to word limits
    def truncate(text: str, n_words: int) -> str:
        words = text.split()
        return " ".join(words[:n_words])

    df["input_text"]  = df["input_text"].apply(lambda t: truncate(t, max_input_length))
    df["target_text"] = df["target_text"].apply(lambda t: truncate(t, max_target_length))

    # Drop too-short rows
    df = df[df["target_text"].str.split().str.len() >= 10].reset_index(drop=True)

    logger.info(f"Medical transcriptions ready: {len(df)} rows")
    return df[["input_text", "target_text"]].copy()


# ---------------------------------------------------------------------------
# Generic utilities
# ---------------------------------------------------------------------------

def train_val_test_split(
    df: pd.DataFrame,
    train_frac: float = 0.70,
    val_frac: float   = 0.15,
    shuffle: bool     = True,
    seed: int         = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (train, val, test) DataFrames."""
    if shuffle:
        df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    n = len(df)
    t = int(n * train_frac)
    v = int(n * (train_frac + val_frac))
    return df.iloc[:t], df.iloc[t:v], df.iloc[v:]


def save_processed(df: pd.DataFrame, name: str) -> Path:
    """Save a processed DataFrame as a Parquet file."""
    out = PROCESSED_DIR / f"{name}.parquet"
    df.to_parquet(out, index=False)
    logger.info(f"Saved processed data → {out}")
    return out
