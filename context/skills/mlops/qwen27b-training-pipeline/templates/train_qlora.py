#!/usr/bin/env python3
"""
QLoRA training for Qwen-27B on DGX Spark GB10.
4-bit quantization (NF4) + LoRA for memory-efficient fine-tuning.
No gradient checkpointing needed — much faster than full-precision + checkpointing.

NOTE: As of May 13 2026, QLoRA on GB10 is still intractably slow (~529s/step)
for 27B models. This script is provided for reference but training 27B on GB10
is not recommended. Use for smaller models (7B) or cloud GPUs instead.

BitsAndBytesConfig import: from transformers import BitsAndBytesConfig
(NOT from bitsandbytes — common pitfall)
"""
import os
import json
import time
from datetime import datetime
from pathlib import Path

import torch
from torch.utils.data import Dataset, ConcatDataset
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, TrainingArguments,
    Trainer, DataCollatorForLanguageModeling, TrainerCallback,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training

MODEL_PATH = '/data/SpecForge/custom_dflash/checkpoints/final_model_merged'
OUTPUT_DIR = '/data/SpecForge/custom_dflash/adapters/qwen27b-qlora-r64'
PREPROCESSED_DIR = '/data/SpecForge/custom_dflash/preprocessed'
DATASET_DIR = '/data/SpecForge/custom_dflash/datasets'

LORA_R = 64
LORA_ALPHA = 128
LORA_DROPOUT = 0.05
LEARNING_RATE = 2e-4
NUM_EPOCHS = 1
BATCH_SIZE = 1
GRAD_ACCUMULATION = 4
MAX_SEQ_LENGTH = 4096
WARMUP_STEPS = 100
SAVE_STEPS = 500
LOGGING_STEPS = 10
MAX_TIER1_SAMPLES = 100000  # Sample subset for faster iteration

TARGET_MODULES = ['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']

class TrainingMonitor:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.output_dir / 'training_metrics.jsonl'
        self.start_time = time.time()
        self.step = 0
    def log_step(self, loss, lr, epoch=None):
        self.step += 1
        entry = {'step': self.step, 'timestamp': datetime.utcnow().isoformat(),
                 'elapsed_seconds': time.time() - self.start_time,
                 'loss': loss, 'learning_rate': lr}
        if epoch is not None: entry['epoch'] = epoch
        with open(self.metrics_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        print(f'Step {self.step}: loss={loss:.4f} lr={lr:.2e}', flush=True)

class LazyPreTokenizedDataset(Dataset):
    def __init__(self, file_path, max_length=4096, max_samples=None):
        self.file_path = file_path
        self.max_length = max_length
        self.offsets = []
        print(f'Indexing {file_path}...')
        with open(file_path, 'rb') as f:
            offset = 0
            for line in f:
                self.offsets.append(offset)
                offset += len(line)
                if max_samples and len(self.offsets) >= max_samples:
                    break
        print(f'Indexed {len(self.offsets)} examples')
    def __len__(self):
        return len(self.offsets)
    def __getitem__(self, idx):
        with open(self.file_path, 'rb') as f:
            f.seek(self.offsets[idx])
            line = f.readline().decode('utf-8')
            data = json.loads(line.strip())
        input_ids = data.get('input_ids', [])
        attention_mask = data.get('attention_mask', [])
        labels = data.get('labels', [])
        if len(input_ids) > self.max_length:
            input_ids = input_ids[:self.max_length]
            attention_mask = attention_mask[:self.max_length]
            labels = labels[:self.max_length]
        return {'input_ids': input_ids, 'attention_mask': attention_mask, 'labels': labels}

class LazyChatDataset(Dataset):
    def __init__(self, file_path, tokenizer, max_length=4096):
        self.file_path = file_path
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.offsets = []
        print(f'Indexing {file_path}...')
        with open(file_path, 'rb') as f:
            offset = 0
            for line in f:
                self.offsets.append(offset)
                offset += len(line)
        print(f'Indexed {len(self.offsets)} examples')
    def __len__(self):
        return len(self.offsets)
    def __getitem__(self, idx):
        with open(self.file_path, 'rb') as f:
            f.seek(self.offsets[idx])
            line = f.readline().decode('utf-8')
            data = json.loads(line.strip())
        messages = data.get('messages', data.get('conversations', []))
        if not messages and 'text' in data:
            messages = [{'role': 'user', 'content': data['text']}]
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        tokens = self.tokenizer(text, truncation=True, max_length=self.max_length, padding='max_length')
        input_ids = tokens['input_ids']
        attention_mask = tokens['attention_mask']
        labels = [tid if mask == 1 else -100 for tid, mask in zip(input_ids, attention_mask)]
        return {'input_ids': input_ids, 'attention_mask': attention_mask, 'labels': labels}

class MetricsCallback(TrainerCallback):
    def __init__(self, monitor):
        self.monitor = monitor
    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs and 'loss' in logs:
            self.monitor.log_step(logs['loss'], logs.get('learning_rate', 0), logs.get('epoch'))

def main():
    print('Loading tokenizer...')
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    print('Loading model in 4-bit for QLoRA (~2 min)...')
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type='nf4',
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        quantization_config=bnb_config,
        device_map='auto',
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    model = prepare_model_for_kbit_training(model)

    print(f'Applying LoRA (r={LORA_R}, alpha={LORA_ALPHA})...')
    lora_config = LoraConfig(
        r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=LORA_DROPOUT,
        target_modules=TARGET_MODULES, task_type=TaskType.CAUSAL_LM,
        bias='none',
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print('Loading datasets...')
    datasets = []
    preprocessed_file = Path(PREPROCESSED_DIR) / 'tier1_preprocessed.jsonl'
    if preprocessed_file.exists():
        ds = LazyPreTokenizedDataset(preprocessed_file, max_length=MAX_SEQ_LENGTH, max_samples=MAX_TIER1_SAMPLES)
        datasets.append(ds)
    tier2_file = Path(DATASET_DIR) / 'tier2-reasoning-chat.jsonl'
    if tier2_file.exists():
        ds = LazyChatDataset(tier2_file, tokenizer, max_length=MAX_SEQ_LENGTH)
        datasets.append(ds)
    tier3_file = Path(DATASET_DIR) / 'tier3-health-chat.jsonl'
    if tier3_file.exists():
        ds = LazyChatDataset(tier3_file, tokenizer, max_length=MAX_SEQ_LENGTH)
        datasets.append(ds)

    if not datasets:
        raise ValueError('No datasets found')
    train_dataset = ConcatDataset(datasets)
    print(f'Total examples: {len(train_dataset)}')

    monitor = TrainingMonitor(OUTPUT_DIR)
    callbacks = [MetricsCallback(monitor)]

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR, num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUMULATION,
        learning_rate=LEARNING_RATE, warmup_steps=WARMUP_STEPS,
        logging_steps=LOGGING_STEPS, save_steps=SAVE_STEPS,
        save_total_limit=3, bf16=True,
        optim='paged_adamw_8bit', weight_decay=0.01, max_grad_norm=0.3,
        lr_scheduler_type='cosine', report_to='none',
        remove_unused_columns=False,
    )

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    trainer = Trainer(
        model=model, args=training_args, train_dataset=train_dataset,
        data_collator=data_collator, callbacks=callbacks,
    )

    print('Starting QLoRA training...')
    trainer.train()
    print('Training complete. Saving adapter...')
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f'Adapter saved to {OUTPUT_DIR}')

if __name__ == '__main__':
    main()
