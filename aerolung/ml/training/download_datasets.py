"""
AeroLung — Dataset Download Script
===================================
Downloads ALL datasets required for the AeroLung ML pipeline.

Usage:
    python -m aerolung.ml.training.download_datasets          # all datasets
    python -m aerolung.ml.training.download_datasets --epa   # EPA only
    python -m aerolung.ml.training.download_datasets --nhanes
    python -m aerolung.ml.training.download_datasets --medical
    python -m aerolung.ml.training.download_datasets --openaq
    python -m aerolung.ml.training.download_datasets --synthetic
"""

from __future__ import annotations

import argparse
import io
import os
import time
import warnings
import zipfile
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm

load_dotenv()

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
_ML_ROOT   = Path(__file__).parent.parent          # aerolung/ml/
RAW_ROOT   = _ML_ROOT / "data" / "raw"

EPA_DIR     = RAW_ROOT / "epa"
NHANES_DIR  = RAW_ROOT / "nhanes"
MEDICAL_DIR = RAW_ROOT / "medical"
OPENAQ_DIR  = RAW_ROOT / "openaq"

for _d in (EPA_DIR, NHANES_DIR, MEDICAL_DIR, OPENAQ_DIR):
    _d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Shared download helper
# ---------------------------------------------------------------------------

def _download_file(url: str, dest: Path, desc: str = "", chunk_size: int = 8192) -> Path:
    """Download *url* to *dest* with a tqdm progress bar.  Returns dest."""
    if dest.exists():
        logger.info(f"Already downloaded: {dest.name}")
        return dest

    logger.info(f"Downloading {desc or dest.name} …")
    headers = {"User-Agent": "AeroLung-DataPipeline/1.0"}
    try:
        resp = requests.get(url, stream=True, headers=headers, timeout=60)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        with open(dest, "wb") as fh, tqdm(
            total=total, unit="B", unit_scale=True, desc=desc or dest.name, leave=False
        ) as pbar:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                fh.write(chunk)
                pbar.update(len(chunk))
        logger.success(f"Saved → {dest}")
    except Exception as exc:
        logger.warning(f"Download failed for {url}: {exc}")
        if dest.exists():
            dest.unlink()
        raise
    return dest


# ---------------------------------------------------------------------------
# DATASET 1 — EPA Air Quality (PM2.5 / Ozone / NO2 / CO)
# ---------------------------------------------------------------------------

EPA_BASE = "https://aqs.epa.gov/aqsweb/airdata/"
EPA_FILES = [
    ("hourly_88101_2021.zip", "PM2.5 2021"),
    ("hourly_88101_2022.zip", "PM2.5 2022"),
    ("hourly_88101_2023.zip", "PM2.5 2023"),
    ("hourly_44201_2023.zip", "Ozone 2023"),
    ("hourly_42602_2023.zip", "NO2 2023"),
    ("hourly_42101_2023.zip", "CO 2023"),
]

EPA_COLUMN_MAP = {
    "Date Local":         "date",
    "Time Local":         "time",
    "Sample Measurement": "pm25",
    "State Name":         "state",
    "County Name":        "county",
    "Latitude":           "lat",
    "Longitude":          "lng",
}


def download_epa_aqi_data() -> pd.DataFrame:
    """
    Download EPA hourly PM2.5 / Ozone / NO2 / CO data (2021–2023),
    merge into a single DataFrame and save as epa_pm25_merged.csv.
    """
    merged_path = EPA_DIR / "epa_pm25_merged.csv"
    if merged_path.exists():
        logger.info("EPA merged CSV already exists — loading from cache.")
        df = pd.read_csv(merged_path, low_memory=False)
        _print_epa_stats(df)
        return df

    downloaded_csvs: list[Path] = []

    for fname, desc in EPA_FILES:
        zip_path = EPA_DIR / fname
        try:
            _download_file(EPA_BASE + fname, zip_path, desc)
        except Exception:
            logger.warning(f"Skipping {fname} due to download error.")
            continue

        # Extract zip
        extract_dir = EPA_DIR / fname.replace(".zip", "")
        extract_dir.mkdir(exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)
            downloaded_csvs.extend(extract_dir.glob("*.csv"))
        except zipfile.BadZipFile as exc:
            logger.warning(f"Bad zip: {zip_path} — {exc}")

    # Only load PM2.5 files (parameter code 88101)
    pm25_csvs = [p for p in downloaded_csvs if "88101" in p.name]

    if not pm25_csvs:
        logger.warning("No EPA PM2.5 CSVs found — generating synthetic fallback data.")
        return _epa_synthetic_fallback(merged_path)

    frames = []
    for csv_path in pm25_csvs:
        try:
            chunk = pd.read_csv(csv_path, usecols=list(EPA_COLUMN_MAP.keys()),
                                low_memory=False)
            chunk.rename(columns=EPA_COLUMN_MAP, inplace=True)
            frames.append(chunk)
        except Exception as exc:
            logger.warning(f"Could not read {csv_path}: {exc}")

    if not frames:
        return _epa_synthetic_fallback(merged_path)

    df = pd.concat(frames, ignore_index=True)
    df["timestamp"] = pd.to_datetime(
        df["date"].astype(str) + " " + df["time"].astype(str), errors="coerce"
    )
    df = df.dropna(subset=["timestamp", "pm25"])
    df = df[(df["pm25"] >= 0) & (df["pm25"] <= 1000)]
    df = df.sort_values("timestamp").reset_index(drop=True)

    df.to_csv(merged_path, index=False)
    _print_epa_stats(df)
    return df


def _print_epa_stats(df: pd.DataFrame) -> None:
    unique_stations = (
        df.groupby(["lat", "lng"]).ngroups if "lat" in df.columns else "N/A"
    )
    logger.info(
        f"EPA data — rows={len(df):,}  "
        f"date_range=[{df['timestamp'].min()}, {df['timestamp'].max()}]  "
        f"unique_stations={unique_stations}"
    )


def _epa_synthetic_fallback(save_path: Path) -> pd.DataFrame:
    """
    Generate minimal synthetic EPA-like data so the rest of the pipeline
    can run even when the real EPA files are unavailable.
    """
    logger.warning("Generating synthetic EPA fallback data (8 760 hours of 1 year).")
    rng = np.random.default_rng(42)
    timestamps = pd.date_range("2023-01-01", periods=8_760, freq="1H")
    pm25 = np.clip(
        rng.normal(loc=15.0, scale=10.0, size=len(timestamps)) +
        5 * np.sin(np.linspace(0, 4 * np.pi, len(timestamps))),
        0, 300,
    )
    df = pd.DataFrame({
        "timestamp": timestamps,
        "date":  [str(t.date()) for t in timestamps],
        "time":  [str(t.time())[: 5] for t in timestamps],
        "pm25":  pm25.round(2),
        "state": "California",
        "county": "Los Angeles",
        "lat":   34.0522,
        "lng":   -118.2437,
    })
    df.to_csv(save_path, index=False)
    logger.success(f"Synthetic EPA data saved → {save_path}")
    return df


# ---------------------------------------------------------------------------
# DATASET 2 — NHANES Health Survey
# ---------------------------------------------------------------------------

NHANES_FILES = {
    "DEMO_J.XPT": "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/DEMO_J.XPT",
    "SPX_J.XPT":  "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/SPX_J.XPT",
    "SMQ_J.XPT":  "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/SMQ_J.XPT",
    "MCQ_J.XPT":  "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/MCQ_J.XPT",
    "BPX_J.XPT":  "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/BPX_J.XPT",
    "BMX_J.XPT":  "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/BMX_J.XPT",
}

NHANES_COL_MAPS = {
    "DEMO_J.XPT": {
        "SEQN": "seqn", "RIDAGEYR": "age", "RIAGENDR": "gender",
        "RIDRETH3": "race", "INDFMPIR": "income_ratio",
    },
    "SPX_J.XPT": {
        "SEQN": "seqn", "SPXNFEV1": "fev1", "SPXNFVC": "fvc",
        "SPXNFEV1FVC": "fev1_fvc_ratio",
    },
    "SMQ_J.XPT": {
        "SEQN": "seqn", "SMQ020": "ever_smoked", "SMQ040": "current_smoker",
    },
    "MCQ_J.XPT": {
        "SEQN": "seqn", "MCQ010": "asthma_ever", "MCQ035": "asthma_still",
        "MCQ160B": "copd", "MCQ160E": "heart_attack", "MCQ160F": "stroke",
    },
    "BPX_J.XPT": {
        "SEQN": "seqn", "BPXSY1": "systolic_bp", "BPXDI1": "diastolic_bp",
        "BPXPLS": "pulse_rate",
    },
    "BMX_J.XPT": {
        "SEQN": "seqn", "BMXBMI": "bmi", "BMXWT": "weight", "BMXHT": "height",
    },
}


def _load_xpt(path: Path, col_map: dict) -> pd.DataFrame:
    """Load an XPT file, keep only the mapped columns, return renamed DataFrame."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = pd.read_sas(str(path), format="xport", encoding="utf-8")
    keep = {k: v for k, v in col_map.items() if k in df.columns}
    return df[list(keep.keys())].rename(columns=keep)


def download_nhanes_data() -> pd.DataFrame:
    """Download and merge all NHANES 2017–2018 survey modules."""
    merged_path = NHANES_DIR / "nhanes_merged.csv"
    if merged_path.exists():
        logger.info("NHANES merged CSV already exists — loading from cache.")
        df = pd.read_csv(merged_path, low_memory=False)
        _print_nhanes_stats(df)
        return df

    frames: dict[str, pd.DataFrame] = {}
    for fname, url in NHANES_FILES.items():
        dest = NHANES_DIR / fname
        try:
            _download_file(url, dest, fname)
            frames[fname] = _load_xpt(dest, NHANES_COL_MAPS[fname])
        except Exception as exc:
            logger.warning(f"Could not load {fname}: {exc} — will skip.")

    if not frames:
        logger.warning("No NHANES files loaded — generating synthetic fallback data.")
        return _nhanes_synthetic_fallback(merged_path)

    # Merge all on seqn
    base = frames.get("DEMO_J.XPT")
    if base is None:
        base = next(iter(frames.values()))

    for fname, df_part in frames.items():
        if "DEMO_J.XPT" in fname:
            continue
        base = base.merge(df_part, on="seqn", how="inner")

    df = base.copy()
    if "age" in df.columns:
        df = df[(df["age"] >= 18) & (df["age"] <= 90)]

    # Fill numeric NaNs with column median
    num_cols = df.select_dtypes(include="number").columns
    df[num_cols] = df[num_cols].fillna(df[num_cols].median())

    df.to_csv(merged_path, index=False)
    _print_nhanes_stats(df)
    return df


def _print_nhanes_stats(df: pd.DataFrame) -> None:
    logger.info(
        f"NHANES data — rows={len(df):,}  columns={list(df.columns)}\n"
        f"  missing values:\n{df.isnull().sum()[df.isnull().sum() > 0]}"
    )


def _nhanes_synthetic_fallback(save_path: Path) -> pd.DataFrame:
    """Generate NHANES-like synthetic health data for pipeline testing."""
    logger.warning("Generating synthetic NHANES fallback data (5 000 subjects).")
    rng = np.random.default_rng(42)
    n = 5_000
    df = pd.DataFrame({
        "seqn":           np.arange(1, n + 1),
        "age":            rng.integers(18, 90, n),
        "gender":         rng.integers(1, 3, n),
        "race":           rng.integers(1, 7, n),
        "income_ratio":   rng.uniform(0, 5, n).round(2),
        "fev1":           rng.normal(3.0, 0.7, n).clip(0.5, 7.0).round(2),
        "fvc":            rng.normal(3.8, 0.8, n).clip(0.8, 8.0).round(2),
        "fev1_fvc_ratio": rng.normal(0.78, 0.10, n).clip(0.3, 1.0).round(3),
        "ever_smoked":    rng.integers(1, 3, n),
        "current_smoker": rng.integers(1, 4, n),
        "asthma_ever":    rng.integers(1, 3, n),
        "asthma_still":   rng.integers(1, 3, n),
        "copd":           rng.integers(1, 3, n),
        "heart_attack":   rng.integers(1, 3, n),
        "stroke":         rng.integers(1, 3, n),
        "systolic_bp":    rng.normal(120, 20, n).clip(60, 240).round(0),
        "diastolic_bp":   rng.normal(80, 12, n).clip(40, 140).round(0),
        "pulse_rate":     rng.normal(72, 12, n).clip(40, 180).round(0),
        "bmi":            rng.normal(27, 6, n).clip(10, 70).round(1),
        "weight":         rng.normal(75, 18, n).clip(30, 200).round(1),
        "height":         rng.normal(170, 12, n).clip(130, 210).round(1),
    })
    df.to_csv(save_path, index=False)
    logger.success(f"Synthetic NHANES data saved → {save_path}")
    return df


# ---------------------------------------------------------------------------
# DATASET 3 — Medical Transcriptions (for report generator fine-tuning)
# ---------------------------------------------------------------------------

PULM_SPECIALTIES = [
    "Pulmonology",
    "Emergency Room Reports",
    "Internal Medicine",
    "General Medicine",
    "Cardiovascular / Pulmonary",
]


def download_medical_transcriptions() -> pd.DataFrame:
    """
    Download MTSamples medical transcription dataset.
    Falls back to HuggingFace datasets if Kaggle credentials are absent.
    """
    save_path = MEDICAL_DIR / "medical_transcriptions_clean.csv"
    if save_path.exists():
        logger.info("Medical transcriptions already downloaded — loading from cache.")
        df = pd.read_csv(save_path)
        _print_medical_stats(df)
        return df

    kaggle_user = os.getenv("KAGGLE_USERNAME", "")
    kaggle_key  = os.getenv("KAGGLE_KEY", "")

    df_raw: Optional[pd.DataFrame] = None

    if kaggle_user and kaggle_key:
        try:
            import kaggle
            kaggle.api.authenticate()
            kaggle.api.dataset_download_files(
                "tboyle10/medicaltranscriptions",
                path=str(MEDICAL_DIR),
                unzip=True,
            )
            csv_path = MEDICAL_DIR / "mtsamples.csv"
            if csv_path.exists():
                df_raw = pd.read_csv(csv_path)
                logger.success("MTSamples downloaded via Kaggle API.")
        except Exception as exc:
            logger.warning(f"Kaggle download failed: {exc} — trying HuggingFace fallback.")

    if df_raw is None:
        # HuggingFace fallback
        logger.info("Attempting HuggingFace datasets fallback for medical transcriptions …")
        try:
            from datasets import load_dataset
            ds = load_dataset("owkin/medical-transcriptions", split="train", trust_remote_code=True)
            df_raw = ds.to_pandas()
            logger.success("Loaded medical transcriptions from HuggingFace.")
        except Exception as exc:
            logger.warning(f"HuggingFace load failed: {exc} — generating synthetic fallback.")
            df_raw = None

    if df_raw is None:
        df_raw = _medical_synthetic_fallback()

    # Normalise column names
    df_raw.columns = [c.lower().strip() for c in df_raw.columns]
    text_col = next(
        (c for c in ("transcription", "text", "content") if c in df_raw.columns),
        df_raw.columns[0],
    )
    spec_col = next(
        (c for c in ("medical_specialty", "specialty", "category") if c in df_raw.columns),
        None,
    )

    df = df_raw.copy()
    df.rename(columns={text_col: "transcription"}, inplace=True)

    # Filter by specialty if available
    if spec_col and spec_col in df.columns:
        df["medical_specialty"] = df[spec_col]
        df = df[df["medical_specialty"].isin(PULM_SPECIALTIES)]

    # Drop short transcriptions
    df = df[df["transcription"].notna()]
    df = df[df["transcription"].astype(str).str.len() >= 100]

    # Add synthetic AQI context with seed for reproducibility
    rng = np.random.default_rng(42)
    n = len(df)
    aqis   = rng.integers(30, 301, n)
    pm25s  = rng.integers(10, 201, n)
    spo2s  = rng.integers(88, 100, n)
    df = df.copy()
    df["air_quality_context"] = [
        f"[AQI Context: PM2.5={pm25s[i]}, AQI={aqis[i]}, SpO2={spo2s[i]}%] "
        f"{str(row['transcription'])[:800]}"
        for i, (_, row) in enumerate(df.iterrows())
    ]

    keep_cols = [c for c in ("transcription", "description", "medical_specialty", "air_quality_context") if c in df.columns]
    df = df[keep_cols].reset_index(drop=True)
    df.to_csv(save_path, index=False)
    _print_medical_stats(df)
    return df


def _print_medical_stats(df: pd.DataFrame) -> None:
    spec_col = "medical_specialty" if "medical_specialty" in df.columns else None
    dist_str = str(df[spec_col].value_counts().to_dict()) if spec_col else "N/A"
    logger.info(f"Medical transcriptions — rows={len(df):,}  specialty distribution={dist_str}")


def _medical_synthetic_fallback() -> pd.DataFrame:
    """Minimal synthetic medical transcription dataset."""
    logger.warning("Generating synthetic medical transcription fallback data.")
    templates = [
        ("Pulmonology",
         "Patient presents with shortness of breath and reduced FEV1. "
         "History of asthma since childhood. Current AQI in residential area is elevated. "
         "Recommend increased inhaler frequency and avoidance of outdoor exercise."),
        ("Emergency Room Reports",
         "45-year-old male with acute respiratory distress. O2 saturation 88% on room air. "
         "PM2.5 in the area has been high this week. Administered bronchodilator and supplemental O2."),
        ("Internal Medicine",
         "Routine follow-up for COPD. Patient reports worsening dyspnoea on exertion. "
         "Spirometry shows obstructive pattern. Environmental exposure to particulate matter noted."),
        ("General Medicine",
         "Patient complains of persistent cough for 3 weeks. "
         "No fever. Lives near industrial zone with high NO2 readings. "
         "Chest X-ray clear. Prescribed antihistamine and air purifier recommended."),
        ("Cardiovascular / Pulmonary",
         "Evaluation for exercise-induced dyspnoea. ECG normal. "
         "Echocardiography shows mild pulmonary hypertension. "
         "Air quality in patient's neighbourhood has been poor."),
    ]
    rows = []
    for _ in range(200):
        t = templates[np.random.randint(len(templates))]
        rows.append({
            "transcription":     t[1],
            "medical_specialty": t[0],
            "description":       f"Sample {t[0]} report",
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# DATASET 4 — OpenAQ historical PM2.5 (for Anomaly Detection)
# ---------------------------------------------------------------------------

OPENAQ_CITIES = {
    "New York":    {"id": 8118,  "country": "US"},
    "Los Angeles": {"id": 8119,  "country": "US"},
    "Chicago":     {"id": 8120,  "country": "US"},
    "Delhi":       {"id": 8121,  "country": "IN"},
    "Mumbai":      {"id": 8122,  "country": "IN"},
    "Beijing":     {"id": 8123,  "country": "CN"},
    "London":      {"id": 8124,  "country": "GB"},
    "Paris":       {"id": 8125,  "country": "FR"},
    "Tokyo":       {"id": 8126,  "country": "JP"},
    "Sydney":      {"id": 8127,  "country": "AU"},
}

OPENAQ_BASE = "https://api.openaq.org/v3"


def _fetch_openaq_measurements(
    location_id: int,
    api_key: str,
    date_from: str = "2023-01-01T00:00:00Z",
    date_to:   str = "2023-12-31T23:59:59Z",
    limit:     int = 1000,
) -> list[dict]:
    """Paginate through OpenAQ measurements for a single location."""
    all_results: list[dict] = []
    page = 1
    headers = {"X-API-Key": api_key} if api_key else {}

    while True:
        url = f"{OPENAQ_BASE}/locations/{location_id}/measurements"
        params = {
            "parameter": "pm25",
            "date_from": date_from,
            "date_to":   date_to,
            "limit":     limit,
            "page":      page,
        }
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            all_results.extend(results)
            if len(results) < limit:
                break
            page += 1
            time.sleep(0.5)
        except Exception as exc:
            logger.warning(f"OpenAQ fetch error (loc={location_id}, page={page}): {exc}")
            break

    return all_results


def _label_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Label per-city anomalies using the 3-sigma rule."""
    frames = []
    for city, group in df.groupby("city"):
        g = group.copy()
        mean = g["pm25"].mean()
        std  = g["pm25"].std()
        if std == 0 or np.isnan(std):
            g["is_anomaly"] = 0
        else:
            g["is_anomaly"] = (
                (g["pm25"] > mean + 3 * std) | (g["pm25"] < mean - 3 * std)
            ).astype(int)
        frames.append(g)
    return pd.concat(frames, ignore_index=True)


def download_openaq_data() -> pd.DataFrame:
    """Download 2023 PM2.5 measurements for 10 global cities from OpenAQ."""
    save_path = OPENAQ_DIR / "openaq_pm25_2023.csv"
    if save_path.exists():
        logger.info("OpenAQ CSV already exists — loading from cache.")
        df = pd.read_csv(save_path, parse_dates=["timestamp"])
        _print_openaq_stats(df)
        return df

    api_key = os.getenv("OPENAQ_API_KEY", "")
    all_rows: list[dict] = []

    for city, info in OPENAQ_CITIES.items():
        logger.info(f"Fetching OpenAQ data for {city} (id={info['id']}) …")
        measurements = _fetch_openaq_measurements(info["id"], api_key)

        if not measurements:
            logger.warning(f"No data returned for {city} — using synthetic fill.")
            all_rows.extend(_openaq_synthetic_city(city))
            continue

        for m in measurements:
            try:
                coords = m.get("coordinates") or {}
                all_rows.append({
                    "city":      city,
                    "timestamp": m["date"]["utc"],
                    "pm25":      float(m.get("value", np.nan)),
                    "unit":      m.get("unit", "µg/m³"),
                    "lat":       coords.get("latitude",  np.nan),
                    "lng":       coords.get("longitude", np.nan),
                })
            except (KeyError, TypeError):
                continue

        time.sleep(0.5)

    if not all_rows:
        logger.warning("No OpenAQ data at all — generating full synthetic dataset.")
        df = _openaq_full_synthetic()
    else:
        df = pd.DataFrame(all_rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
        df = df.dropna(subset=["timestamp", "pm25"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        df = _label_anomalies(df)

    df.to_csv(save_path, index=False)
    _print_openaq_stats(df)
    return df


def _openaq_synthetic_city(city: str, n: int = 1_000) -> list[dict]:
    rng = np.random.default_rng(hash(city) % (2**31))
    base_pm25 = {"Delhi": 90, "Beijing": 80, "Mumbai": 60}.get(city, 15)
    timestamps = pd.date_range("2023-01-01", periods=n, freq="8H", tz="UTC")
    return [
        {
            "city":      city,
            "timestamp": str(ts),
            "pm25":      max(0, round(rng.normal(base_pm25, base_pm25 * 0.3), 2)),
            "unit":      "µg/m³",
            "lat":       0.0,
            "lng":       0.0,
        }
        for ts in timestamps
    ]


def _openaq_full_synthetic() -> pd.DataFrame:
    frames = [pd.DataFrame(_openaq_synthetic_city(city)) for city in OPENAQ_CITIES]
    df = pd.concat(frames, ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp").reset_index(drop=True)
    return _label_anomalies(df)


def _print_openaq_stats(df: pd.DataFrame) -> None:
    anomaly_count = int(df["is_anomaly"].sum()) if "is_anomaly" in df.columns else 0
    pct = round(anomaly_count / max(len(df), 1) * 100, 2)
    logger.info(
        f"OpenAQ data — rows={len(df):,}  "
        f"anomalies={anomaly_count:,} ({pct}%)"
    )


# ---------------------------------------------------------------------------
# DATASET 5 — Synthetic Health-AQI Report Pairs
# ---------------------------------------------------------------------------

INPUT_TEMPLATES = [
    "Patient data: Age={age}, Gender={gender}, AQI={aqi}, PM2.5={pm25}µg/m³, "
    "SpO2={spo2}%, Heart Rate={hr}bpm, Smoker={smoker}, Asthma={asthma}, COPD={copd}. "
    "Generate health advisory.",
    "Clinical summary needed for: {age}yo {gender} patient. "
    "Current air quality: AQI={aqi}, PM2.5={pm25}µg/m³. "
    "Vitals: SpO2={spo2}%, HR={hr}bpm. History: smoker={smoker}, asthma={asthma}. Advisory?",
    "Respiratory risk assessment — "
    "Demographics: age {age}, {gender}. Environment: AQI {aqi} (PM2.5={pm25}µg/m³). "
    "Physiology: SpO2={spo2}%, HR={hr}. Comorbidities: asthma={asthma}, COPD={copd}. "
    "Provide advisory.",
    "PLSI query: patient {age}yo, AQI={aqi}, PM2.5={pm25}, SpO2={spo2}%, "
    "HR={hr}, smoker={smoker}, asthma={asthma}, COPD={copd}. Output risk advisory.",
    "Environmental health check: AQI={aqi}, PM2.5={pm25}µg/m³. "
    "Patient profile: {age}yo {gender}, SpO2={spo2}%, pulse={hr}. "
    "Asthma: {asthma}. Suggest course of action.",
    "Generate clinical note: {age}-year-old {gender} presenting in AQI={aqi} conditions. "
    "PM2.5={pm25}µg/m³. O2 sat={spo2}%, HR={hr}. Asthma={asthma}, COPD={copd}.",
    "Health advisory request — "
    "Patient: age={age}, gender={gender}, BMI not recorded. "
    "Air: AQI={aqi}, PM2.5={pm25}. Vitals: SpO2={spo2}%, HR={hr}bpm. "
    "Risk factors: smoking={smoker}, asthma={asthma}.",
    "AQI impact analysis for {age}yo patient (gender={gender}). "
    "Outdoor AQI={aqi}, PM2.5={pm25}µg/m³. Baseline SpO2={spo2}%, HR={hr}bpm. "
    "Previous conditions: asthma={asthma}, COPD={copd}. Advisory:",
    "Pulmonary risk profile — "
    "AQI={aqi} ({pm25}µg/m³ PM2.5). SpO2={spo2}%, HR={hr}. "
    "Patient age {age}, gender {gender}. Asthma: {asthma}. Provide recommendations.",
    "Emergency pre-screening: {age}yo {gender} with SpO2={spo2}%, HR={hr}bpm. "
    "AQI outside={aqi}. PM2.5={pm25}µg/m³. Smoker={smoker}, COPD={copd}. "
    "Action required?",
]


def _risk_level(aqi: int) -> str:
    if aqi <= 50:   return "low"
    if aqi <= 100:  return "moderate"
    if aqi <= 150:  return "high"
    if aqi <= 200:  return "very_high"
    return "critical"


def _build_advisory(vals: dict) -> str:
    aqi  = vals["aqi"]
    pm25 = vals["pm25"]
    spo2 = vals["spo2"]
    age  = vals["age"]
    pct  = round((pm25 / 15.0) * 100, 1)           # % of WHO 24h limit
    asthma_note = "Asthma patients especially at risk. " if vals["asthma"] == "Yes" else ""
    copd_note   = "COPD patients should stay indoors. "  if vals["copd"]   == "Yes" else ""

    if aqi <= 50:
        return (
            f"Air quality is currently Good (AQI={aqi}). "
            f"PM2.5 levels ({pm25}µg/m³) are within WHO guidelines. "
            f"No restrictions needed for {age}-year-old patient. "
            f"SpO2 at {spo2}% is normal. Continue regular activities."
        )
    if aqi <= 100:
        return (
            f"Air quality is Moderate (AQI={aqi}). "
            f"PM2.5 at {pm25}µg/m³ is {pct}% of WHO 24h limit. "
            f"{asthma_note}Recommend limiting prolonged outdoor exertion. "
            f"Monitor SpO2 if below 95%. Consider wearing N95 mask."
        )
    if aqi <= 150:
        return (
            f"HEALTH ALERT — Air quality Unhealthy for Sensitive Groups (AQI={aqi}). "
            f"PM2.5={pm25}µg/m³ ({pct}% of WHO limit). "
            f"{asthma_note}{copd_note}"
            f"SpO2={spo2}% — seek medical attention if below 92%. "
            f"Patient age {age}: avoid all outdoor activity. Use air purifier indoors."
        )
    if aqi <= 200:
        return (
            f"URGENT — Unhealthy air quality (AQI={aqi}, PM2.5={pm25}µg/m³). "
            f"{asthma_note}{copd_note}"
            f"SpO2={spo2}%. Immediate bronchodilator review recommended. "
            f"Stay indoors. Seek emergency care if SpO2 drops below 90%."
        )
    return (
        f"CRITICAL HAZARD — AQI={aqi}, PM2.5={pm25}µg/m³ ({pct}% of WHO limit). "
        f"Hazardous conditions for all individuals. "
        f"{asthma_note}{copd_note}"
        f"SpO2={spo2}% — emergency monitoring required for {age}-year-old patient. "
        f"Evacuate to clean-air environment immediately. Call emergency services if SpO2 < 90%."
    )


def generate_synthetic_health_reports(n_samples: int = 5_000) -> pd.DataFrame:
    """
    Generate synthetic input-output pairs for healthcare report LLM fine-tuning.
    5 000 samples covering all AQI risk bands with 10 input template variations.
    """
    save_path = MEDICAL_DIR / "synthetic_health_reports.csv"
    if save_path.exists():
        logger.info("Synthetic health reports already exist — loading from cache.")
        df = pd.read_csv(save_path)
        logger.info(f"Loaded {len(df):,} synthetic report pairs.")
        return df

    logger.info(f"Generating {n_samples:,} synthetic health report pairs …")
    rng = np.random.default_rng(42)

    rows = []
    for i in range(n_samples):
        age     = int(rng.integers(5, 90))
        gender  = rng.choice(["Male", "Female"])
        aqi     = int(rng.integers(10, 401))
        pm25    = round(float(rng.uniform(2, 250)), 1)
        spo2    = int(rng.integers(88, 100))
        hr      = int(rng.integers(50, 120))
        smoker  = rng.choice(["Yes", "No"])
        asthma  = rng.choice(["Yes", "No"])
        copd    = rng.choice(["Yes", "No"])

        vals = dict(age=age, gender=gender, aqi=aqi, pm25=pm25,
                    spo2=spo2, hr=hr, smoker=smoker, asthma=asthma, copd=copd)

        tmpl   = INPUT_TEMPLATES[i % len(INPUT_TEMPLATES)]
        input_text  = tmpl.format(**vals)
        target_text = _build_advisory(vals)

        rows.append({
            "input_text":   input_text,
            "target_text":  target_text,
            "risk_level":   _risk_level(aqi),
            "aqi":          aqi,
        })

    df = pd.DataFrame(rows)
    df.to_csv(save_path, index=False)

    dist = df["risk_level"].value_counts().to_dict()
    logger.success(f"Synthetic health reports saved — {len(df):,} rows | distribution: {dist}")
    return df


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(args: argparse.Namespace) -> None:
    run_all = not any([args.epa, args.nhanes, args.medical, args.openaq, args.synthetic])

    results: dict[str, Optional[pd.DataFrame]] = {}

    if run_all or args.epa:
        logger.info("=== Dataset 1: EPA Air Quality ===")
        try:
            results["epa"] = download_epa_aqi_data()
        except Exception as exc:
            logger.error(f"EPA download failed: {exc}")

    if run_all or args.nhanes:
        logger.info("=== Dataset 2: NHANES Health Survey ===")
        try:
            results["nhanes"] = download_nhanes_data()
        except Exception as exc:
            logger.error(f"NHANES download failed: {exc}")

    if run_all or args.medical:
        logger.info("=== Dataset 3: Medical Transcriptions ===")
        try:
            results["medical"] = download_medical_transcriptions()
        except Exception as exc:
            logger.error(f"Medical transcriptions download failed: {exc}")

    if run_all or args.openaq:
        logger.info("=== Dataset 4: OpenAQ Sensor Data ===")
        try:
            results["openaq"] = download_openaq_data()
        except Exception as exc:
            logger.error(f"OpenAQ download failed: {exc}")

    if run_all or args.synthetic:
        logger.info("=== Dataset 5: Synthetic Health Reports ===")
        try:
            results["synthetic"] = generate_synthetic_health_reports()
        except Exception as exc:
            logger.error(f"Synthetic generation failed: {exc}")

    downloaded = [k for k, v in results.items() if v is not None]
    logger.success(f"Download complete. Available datasets: {downloaded}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AeroLung Dataset Downloader")
    parser.add_argument("--epa",      action="store_true", help="Download EPA data only")
    parser.add_argument("--nhanes",   action="store_true", help="Download NHANES data only")
    parser.add_argument("--medical",  action="store_true", help="Download medical transcriptions only")
    parser.add_argument("--openaq",   action="store_true", help="Download OpenAQ data only")
    parser.add_argument("--synthetic",action="store_true", help="Generate synthetic reports only")
    main(parser.parse_args())
