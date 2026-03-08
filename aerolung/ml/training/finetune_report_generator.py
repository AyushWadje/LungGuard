"""
AeroLung — Seq2Seq Health Report Generator Fine-tuning Script
==============================================================
Fine-tunes google/flan-t5-base (or any Seq2Seq model) on the
synthetic + real medical transcription dataset with PEFT/LoRA
for efficient training on consumer hardware.

Usage
-----
    python -m aerolung.ml.training.finetune_report_generator \
        [--base-model google/flan-t5-base] \
        [--epochs 3] \
        [--batch-size 8]

Outputs
-------
    aerolung/ml/saved_models/report_generator/   (HuggingFace SavedModel)
    aerolung/ml/saved_models/report_generator_metrics.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

_ROOT     = Path(__file__).parent.parent
_DATA_DIR = _ROOT / "data" / "raw" / "medical"
_SAVE_DIR = _ROOT / "saved_models" / "report_generator"

sys.path.insert(0, str(_ROOT.parent.parent))

try:
    import torch
    from datasets import Dataset
    from evaluate import load as load_metric
    from peft import LoraConfig, TaskType, get_peft_model, PeftModel
    from transformers import (
        AutoTokenizer,
        AutoModelForSeq2SeqLM,
        DataCollatorForSeq2Seq,
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
    )
    _HF_OK = True
except ImportError as _e:
    _HF_OK = False
    logger.warning(f"HuggingFace stack not installed: {_e}. Fine-tuning will not run.")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_BASE_MODEL = "google/flan-t5-base"
MAX_INPUT_LEN      = 512
MAX_TARGET_LEN     = 256
LORA_RANK          = 16
LORA_ALPHA         = 32
LORA_DROPOUT       = 0.10
LORA_TARGET_MODULES = ["q", "v"]   # flan-t5 attention projections


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_training_data(data_dir: Path) -> pd.DataFrame:
    """Load synthetic + real medical transcription advisory pairs."""
    frames = []

    synthetic = data_dir / "synthetic_health_reports.csv"
    if synthetic.exists():
        df_syn = pd.read_csv(synthetic)
        logger.info(f"Loaded {len(df_syn):,} synthetic pairs from {synthetic.name}")
        frames.append(df_syn[["input_text", "target_text"]])

    real = data_dir / "medical_transcriptions_clean.csv"
    if real.exists():
        df_real = pd.read_csv(real)
        if "input_text" in df_real.columns and "target_text" in df_real.columns:
            logger.info(f"Loaded {len(df_real):,} real transcription pairs")
            frames.append(df_real[["input_text", "target_text"]])

    if not frames:
        logger.warning("No training data found — generating minimal synthetic dataset.")
        from aerolung.ml.training.download_datasets import generate_synthetic_health_reports
        df_fallback = generate_synthetic_health_reports(n=1000)
        frames.append(df_fallback[["input_text", "target_text"]])

    df = pd.concat(frames, ignore_index=True).dropna()
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    logger.info(f"Total training pairs: {len(df):,}")
    return df


# ---------------------------------------------------------------------------
# Tokenisation
# ---------------------------------------------------------------------------

def tokenise_dataset(df: pd.DataFrame, tokenizer, prefix: str = "generate health advisory: "):
    hf_ds = Dataset.from_pandas(df[["input_text", "target_text"]])
    split  = hf_ds.train_test_split(test_size=0.10, seed=42)

    def tokenise_fn(batch):
        inputs  = [prefix + t for t in batch["input_text"]]
        targets = batch["target_text"]
        model_inputs = tokenizer(inputs,  max_length=MAX_INPUT_LEN,  truncation=True, padding=False)
        with tokenizer.as_target_tokenizer():
            labels = tokenizer(targets, max_length=MAX_TARGET_LEN, truncation=True, padding=False)
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    train_ds = split["train"].map(tokenise_fn, batched=True, remove_columns=["input_text", "target_text"])
    eval_ds  = split["test"].map(tokenise_fn,  batched=True, remove_columns=["input_text", "target_text"])
    return train_ds, eval_ds


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def build_compute_metrics(tokenizer):
    rouge = load_metric("rouge")

    def compute_metrics(eval_preds):
        preds, labels = eval_preds
        if isinstance(preds, tuple):
            preds = preds[0]
        preds  = np.where(preds  != -100, preds,  tokenizer.pad_token_id)
        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        decoded_preds  = tokenizer.batch_decode(preds,  skip_special_tokens=True)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
        # Wrap labels in a list for rouge
        result = rouge.compute(
            predictions=decoded_preds,
            references=[[l] for l in decoded_labels],
            use_stemmer=True,
        )
        return {k: round(v, 4) for k, v in result.items()}

    return compute_metrics


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def finetune(
    base_model: str    = DEFAULT_BASE_MODEL,
    epochs: int        = 3,
    batch_size: int    = 8,
    grad_accum: int    = 4,
    warmup_steps: int  = 50,
    lr: float          = 3e-4,
    fp16: bool         = False,
) -> dict:
    if not _HF_OK:
        raise RuntimeError(
            "HuggingFace stack not installed. "
            "Run: pip install transformers datasets evaluate peft accelerate"
        )

    _SAVE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    df = load_training_data(_DATA_DIR)

    # 2. Tokeniser + model
    logger.info(f"Loading base model: {base_model}")
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model_raw = AutoModelForSeq2SeqLM.from_pretrained(base_model)

    # 3. LoRA / PEFT wrapping
    lora_cfg = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM,
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGET_MODULES,
        bias="none",
    )
    model = get_peft_model(model_raw, lora_cfg)
    model.print_trainable_parameters()

    # 4. Tokenise
    train_ds, eval_ds = tokenise_dataset(df, tokenizer)
    logger.info(f"Train: {len(train_ds):,} rows  |  Eval: {len(eval_ds):,} rows")

    # 5. Training args
    training_args = Seq2SeqTrainingArguments(
        output_dir=str(_SAVE_DIR / "checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        warmup_steps=warmup_steps,
        learning_rate=lr,
        weight_decay=0.01,
        predict_with_generate=True,
        generation_max_length=MAX_TARGET_LEN,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="rougeL",
        fp16=fp16,
        logging_dir=str(_SAVE_DIR / "logs"),
        logging_steps=20,
        report_to="none",
        dataloader_num_workers=0,
    )

    collator = DataCollatorForSeq2Seq(tokenizer, model=model, padding=True)
    compute  = build_compute_metrics(tokenizer)

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        tokenizer=tokenizer,
        data_collator=collator,
        compute_metrics=compute,
    )

    # 6. Train
    logger.info("Starting fine-tuning…")
    train_result = trainer.train()

    # 7. Evaluate
    eval_result = trainer.evaluate()
    logger.info(f"Final eval: {eval_result}")

    # 8. Merge LoRA weights into base model and save
    merged_model = model.merge_and_unload()
    merged_model.save_pretrained(str(_SAVE_DIR))
    tokenizer.save_pretrained(str(_SAVE_DIR))

    metrics = {
        "base_model":           base_model,
        "epochs":               epochs,
        "batch_size":           batch_size,
        "lora_rank":            LORA_RANK,
        "train_samples":        len(train_ds),
        "eval_samples":         len(eval_ds),
        "train_runtime_s":      round(train_result.metrics.get("train_runtime", 0), 1),
        "train_loss":           round(train_result.metrics.get("train_loss", 0), 4),
        "eval_rougeL":          round(eval_result.get("eval_rougeL", 0), 4),
        "eval_rouge1":          round(eval_result.get("eval_rouge1", 0), 4),
    }

    with open(_SAVE_DIR.parent / "report_generator_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    logger.success(f"Fine-tuned model saved → {_SAVE_DIR}")
    return metrics


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune Seq2Seq health report generator")
    parser.add_argument("--base-model",    type=str,   default=DEFAULT_BASE_MODEL)
    parser.add_argument("--epochs",        type=int,   default=3)
    parser.add_argument("--batch-size",    type=int,   default=8)
    parser.add_argument("--grad-accum",    type=int,   default=4)
    parser.add_argument("--lr",            type=float, default=3e-4)
    parser.add_argument("--warmup-steps",  type=int,   default=50)
    parser.add_argument("--fp16",          action="store_true", help="Use mixed-precision training")
    args = parser.parse_args()

    if not _HF_OK:
        logger.error("HuggingFace libraries not installed. Cannot fine-tune.")
        logger.error("Install via: pip install -r requirements_ml.txt")
        sys.exit(1)

    metrics = finetune(
        base_model=args.base_model,
        epochs=args.epochs,
        batch_size=args.batch_size,
        grad_accum=args.grad_accum,
        warmup_steps=args.warmup_steps,
        lr=args.lr,
        fp16=args.fp16,
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
