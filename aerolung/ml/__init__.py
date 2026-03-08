"""AeroLung ML pipeline package."""
from pathlib import Path

# Convenience path roots
PACKAGE_ROOT = Path(__file__).parent.parent
ML_ROOT = Path(__file__).parent
DATA_ROOT = ML_ROOT / "data"
SAVED_MODELS_ROOT = ML_ROOT / "saved_models"
RAW_DATA_ROOT = DATA_ROOT / "raw"
PROCESSED_DATA_ROOT = DATA_ROOT / "processed"
