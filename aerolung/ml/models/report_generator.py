"""
AeroLung — Health Report Generator (HuggingFace Seq2Seq)
=========================================================
Fine-tuned Flan-T5 model that generates personalised air-quality
health advisories from structured patient + environmental data.

Falls back to template-based generation when the fine-tuned model
is unavailable, so the service is always functional.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from string import Template
from typing import Dict, List, Optional

from loguru import logger

_MODEL_DIR = Path(__file__).parent.parent / "saved_models" / "report_generator"
_BASE_MODEL = "google/flan-t5-base"

try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
    _HF_AVAILABLE = True
except ImportError:
    _HF_AVAILABLE = False

# ---------------------------------------------------------------------------
# Template-based fallback bank
# ---------------------------------------------------------------------------
_TEMPLATES = {
    "Low": Template(
        "Air quality is currently GOOD (AQI $aqi, PM2.5 $pm25 µg/m³). "
        "All pollutant levels are below WHO thresholds. $name can continue "
        "normal outdoor activities. Routine check-up in $weeks weeks."
    ),
    "Moderate": Template(
        "Air quality index of $aqi indicates MODERATE conditions "
        "(PM2.5 $pm25 µg/m³). $name (age $age) with $conditions "
        "should limit prolonged outdoor exertion, especially during "
        "afternoon peak hours. Stay hydrated and monitor symptoms."
    ),
    "High": Template(
        "CAUTION — AQI $aqi with PM2.5 $pm25 µg/m³ exceeds safe thresholds. "
        "$name (age $age) presenting $conditions is at elevated risk. "
        "Recommend: (1) Stay indoors with windows closed. "
        "(2) Use N95 mask if outdoor exposure is necessary. "
        "(3) Follow bronchodilator schedule. Next review in 3 days."
    ),
    "Very High": Template(
        "ALERT — Very Unhealthy air (AQI $aqi, PM2.5 $pm25 µg/m³). "
        "$name, given $conditions, faces serious respiratory risk. "
        "Action required: (1) Remain indoors with air purifier. "
        "(2) Contact pulmonologist within 24 h if dyspnoea worsens. "
        "(3) Emergency inhaler on person at all times. "
        "(4) Review medications with care team."
    ),
    "Hazardous": Template(
        "EMERGENCY HAZARD — AQI $aqi, PM2.5 $pm25 µg/m³ is HAZARDOUS. "
        "$name with $conditions: Evacuate to clean-air shelter immediately "
        "if possible. If breathing difficulties occur, call emergency services. "
        "Do NOT exercise outdoors. Check back with clinician in 24 h."
    ),
}

_AQI_CATEGORY = {(0, 50): "Low", (51, 100): "Moderate", (101, 150): "High",
                 (151, 200): "Very High", (201, 500): "Hazardous"}


class ReportGenerator:
    """
    Personalised health advisory generator.

    Usage
    -----
    >>> gen = ReportGenerator()
    >>> report = gen.generate({
    ...     "name": "Patient A", "age": 67,
    ...     "conditions": ["asthma", "COPD"],
    ...     "spo2": 94, "breathing_rate": 22,
    ...     "aqi": 145, "pm25": 52.3,
    ... })
    >>> print(report["advisory"])
    """

    MAX_NEW_TOKENS: int = 256
    TEMPERATURE:    float = 0.7

    def __init__(self, model_dir: Optional[Path] = None, device: str = "cpu"):
        self.model_dir = model_dir or _MODEL_DIR
        self.device    = device
        self._pipeline = None
        self._tokenizer = None
        self._model_obj = None
        self._loaded   = False
        self._load()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not _HF_AVAILABLE:
            warnings.warn(
                "transformers library not installed. "
                "ReportGenerator will use template fallback. "
                "Install via: pip install transformers",
                UserWarning,
                stacklevel=3,
            )
            return

        load_dir = self.model_dir if (self.model_dir / "config.json").exists() else None

        try:
            model_id = str(load_dir) if load_dir else _BASE_MODEL
            logger.info(f"Loading Seq2Seq model from: {model_id}")
            self._tokenizer = AutoTokenizer.from_pretrained(model_id)
            self._model_obj = AutoModelForSeq2SeqLM.from_pretrained(model_id)
            self._pipeline  = pipeline(
                "text2text-generation",
                model=self._model_obj,
                tokenizer=self._tokenizer,
                device=-1 if self.device == "cpu" else 0,
                max_new_tokens=self.MAX_NEW_TOKENS,
            )
            source = "fine-tuned" if load_dir else "base (not fine-tuned)"
            logger.info(f"ReportGenerator loaded ({source}).")
            self._loaded = True
        except Exception as exc:
            logger.warning(f"ReportGenerator load error: {exc}. Using templates.")
            warnings.warn(
                f"ReportGenerator: could not load model ({exc}). "
                "Falling back to template-based generation. "
                "Run aerolung/ml/training/finetune_report_generator.py to fine-tune.",
                UserWarning,
                stacklevel=3,
            )

    @property
    def is_ready(self) -> bool:
        return self._loaded

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def generate(self, patient_context: Dict) -> Dict:
        """
        Generate a personalised health advisory.

        Parameters
        ----------
        patient_context : dict
            name            str
            age             int
            conditions      list[str]   e.g. ["asthma", "COPD"]
            spo2            float
            breathing_rate  float
            heart_rate      float
            aqi             int         EPA AQI
            pm25            float       µg/m³

        Returns
        -------
        dict:
          advisory    str     full advisory text
          risk_level  str     Low / Moderate / High / Very High / Hazardous
          method      str     "flan_t5" or "template"
          word_count  int
        """
        aqi  = int(patient_context.get("aqi", 50))
        risk = _classify_risk(aqi)

        if self._loaded and self._pipeline is not None:
            advisory = self._hf_generate(patient_context, risk)
            method   = "flan_t5"
        else:
            advisory = self._template_generate(patient_context, risk)
            method   = "template"

        return {
            "advisory":   advisory.strip(),
            "risk_level": risk,
            "method":     method,
            "word_count": len(advisory.split()),
        }

    def _hf_generate(self, ctx: Dict, risk: str) -> str:
        prompt = _build_prompt(ctx, risk)
        try:
            out = self._pipeline(prompt, do_sample=True, temperature=self.TEMPERATURE)
            return out[0]["generated_text"]
        except Exception as exc:
            logger.warning(f"HF generation error: {exc}. Falling back to template.")
            return self._template_generate(ctx, risk)

    def _template_generate(self, ctx: Dict, risk: str) -> str:
        tmpl   = _TEMPLATES.get(risk, _TEMPLATES["Moderate"])
        name   = str(ctx.get("name", "The patient"))
        age    = int(ctx.get("age", 40))
        conds  = ctx.get("conditions", [])
        cond_str = ", ".join(conds) if conds else "no major pre-existing conditions"
        pm25   = float(ctx.get("pm25", 15.0))
        aqi    = int(ctx.get("aqi", 50))
        weeks  = 4 if risk in ("Low",) else (2 if risk == "Moderate" else 1)
        return tmpl.safe_substitute(
            name=name, age=age, conditions=cond_str,
            pm25=round(pm25, 1), aqi=aqi, weeks=weeks,
        )

    # ------------------------------------------------------------------
    # Batch generation
    # ------------------------------------------------------------------

    def generate_batch(self, patients: List[Dict]) -> List[Dict]:
        return [self.generate(p) for p in patients]

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> Dict:
        return {
            "model":        "ReportGenerator",
            "backend":      "flan_t5" if self._loaded else "template",
            "base_model":   _BASE_MODEL,
            "hf_available": _HF_AVAILABLE,
            "status":       "ok",   # always ok — template fallback exists
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify_risk(aqi: int) -> str:
    for (lo, hi), label in _AQI_CATEGORY.items():
        if lo <= aqi <= hi:
            return label
    return "Hazardous"


def _build_prompt(ctx: Dict, risk: str) -> str:
    name   = ctx.get("name", "Patient")
    age    = ctx.get("age", 40)
    conds  = ", ".join(ctx.get("conditions", [])) or "none"
    aqi    = ctx.get("aqi", 50)
    pm25   = round(float(ctx.get("pm25", 15)), 1)
    spo2   = ctx.get("spo2", 97)
    br     = ctx.get("breathing_rate", 16)
    hr     = ctx.get("heart_rate", 72)

    return (
        f"generate health advisory: "
        f"patient name={name}, age={age}, conditions={conds}, "
        f"AQI={aqi}, risk_level={risk}, PM2.5={pm25} ug/m3, "
        f"SpO2={spo2}%, breathing_rate={br} breaths/min, "
        f"heart_rate={hr} bpm. "
        f"Write a concise, actionable advisory in 3-5 sentences."
    )
