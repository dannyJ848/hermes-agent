#!/usr/bin/env python3
"""Direct PEFT/LoRA training script for Qwen 27B on DGX Spark (GB10).

This replaces axolotl (incompatible with GB10's CUDA 13.0 / sm_121 PyTorch).
Run inside eval_venv which has torch 2.11.0+cu130.

Usage:
    source /data/SpecForge/custom_dflash/eval_venv/bin/activate
    python3 direct_peft_lora_training.py
"""

import os
import json
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model
from datasets import Dataset

# ==================== CONFIGURATION ====================
MODEL_PATH = "/data/SpecForge/custom_dflash/checkpoints/final_model_merged"
OUTPUT_DIR = "/data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256"
DATASET_PATHS = [
    "/data/SpecForge/custom_dflash/datasets/tier1-reasoning.jsonl",
    "/data/SpecForge/custom_dflash/datasets/tier2-reasoning.jsonl",
]

# LoRA config
LORA_R = 256
LORA_ALPHA = 512
LORA_DROPOUT = 0.05
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

# Training config
BATCH_SIZE = 1
GRAD_ACCUM = 4
LEARNING_RATE = 2e-4
NUM_EPOCHS = 2
MAX_SEQ_LENGTH = 4096
WARMUP_STEPS = 100
SAVE_STEPS = 1000
LOGGING_STEPS = 10
# =======================================================


def load_datasets(paths):
    """Load and combine datasets from JSONL files with input/output format."""
    all_data = []
    for path in paths:
        if not os.path.exists(path):
            print(f"Warning: {path} not found, skipping")
            continue
        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    text = f"### Input:\n{record.get('input', '')}\n\n### Response:\n{record.get('output', '')}"
                    all_data.append({"text": text})
                    count += 1
                    if count % 100000 == 0:
                        print(f"  Loaded {count} records from {path}...")
                except json.JSONDecodeError:
                    continue
        print(f"Loaded {count} records from {path}")
    print(f"Total records: {len(all_data)}")
    return Dataset.from_list(all_data)


def main():
    print("=" * 60)
    print("Qwen 27B LoRA Training - Direct PEFT")
    print("=" * 60)

    # Check GPU
    print(f"\nGPU: {torch.cuda.get_device_name(0)}")
    print(f"CUDA: {torch.version.cuda}")
    print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    # Load tokenizer
    print("\nLoading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model
    print("Loading model (this may take 5-10 minutes)...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Model loaded. Parameters: {total_params / 1e6:.0f}M")

    # Configure LoRA
    print(f"\nConfiguring LoRA (r={LORA_R}, alpha={LORA_ALPHA})...")
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        target_modules=TARGET_MODULES,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Load datasets
    print("\nLoading datasets...")
    dataset = load_datasets(DATASET_PATHS)

    # Split train/val
    dataset = dataset.train_test_split(test_size=0.02, seed=42)
    train_dataset = dataset["train"]
    eval_dataset = dataset["test"]

    # Tokenize
    print("\nTokenizing...")

    def tokenize_fn(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=MAX_SEQ_LENGTH,
            padding="max_length",
            return_tensors=None,
        )

    train_dataset = train_dataset.map(
        tokenize_fn,
        batched=True,
        remove_columns=["text"],
    )
    eval_dataset = eval_dataset.map(
        tokenize_fn,
        batched=True,
        remove_columns=["text"],
    )

    # Training arguments
    print("\nSetting up training...")
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=LEARNING_RATE,
        warmup_steps=WARMUP_STEPS,
        logging_steps=LOGGING_STEPS,
        save_steps=SAVE_STEPS,
        eval_strategy="steps",
        eval_steps=200,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        bf16=True,
        tf32=True,
        dataloader_num_workers=2,
        remove_unused_columns=False,
        report_to="none",
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
    )

    # Train
    print("\n" + "=" * 60)
    print("Starting training...")
    print("=" * 60)
    trainer.train()

    # Save
    print("\nSaving final model...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Model saved to {OUTPUT_DIR}")

    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
