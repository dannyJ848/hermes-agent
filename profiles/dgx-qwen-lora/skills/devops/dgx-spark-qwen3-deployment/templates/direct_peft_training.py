#!/usr/bin/env python3
"""
Direct PEFT LoRA training for Qwen 27B on DGX Spark GB10.
Verified working: May 2026.

CRITICAL: Must use low_cpu_mem_usage=False to prevent meta-device gradient bugs.
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
    Trainer, DataCollatorForLanguageModeling, TrainerCallback
)
from peft import LoraConfig, get_peft_model, TaskType

# ============================================================================
# CONFIGURATION - Adjust these for your setup
# ============================================================================
MODEL_PATH = '/data/SpecForge/custom_dflash/checkpoints/final_model_merged'
OUTPUT_DIR = '/data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256'
DATASET_DIR = '/data/SpecForge/custom_dflash/datasets'

LORA_R = 256
LORA_ALPHA = 512
LORA_DROPOUT = 0.05
LEARNING_RATE = 2e-4
NUM_EPOCHS = 2
BATCH_SIZE = 1
GRAD_ACCUMULATION = 4
MAX_SEQ_LENGTH = 4096
WARMUP_STEPS = 100
SAVE_STEPS = 500
LOGGING_STEPS = 10

TARGET_MODULES = ['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']

# ============================================================================
# MONITORING
# ============================================================================
class TrainingMonitor:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.output_dir / 'training_metrics.jsonl'
        self.start_time = time.time()
        self.step = 0
    
    def log_step(self, loss, lr, epoch=None):
        self.step += 1
        entry = {
            'step': self.step,
            'timestamp': datetime.utcnow().isoformat(),
            'elapsed_seconds': time.time() - self.start_time,
            'loss': loss,
            'learning_rate': lr
        }
        if epoch is not None:
            entry['epoch'] = epoch
        with open(self.metrics_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        print(f'Step {self.step}: loss={loss:.4f} lr={lr:.2e}', flush=True)

# ============================================================================
# DATASET
# ============================================================================
class ChatDataset(Dataset):
    """Dataset for chat-formatted JSONL files."""
    
    def __init__(self, file_path, tokenizer, max_length=4096):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.examples = []
        print(f'Loading {file_path}...')
        with open(file_path) as f:
            for line in f:
                data = json.loads(line.strip())
                if 'messages' in data:
                    text = self._messages_to_text(data['messages'])
                elif 'text' in data:
                    text = data['text']
                else:
                    continue
                self.examples.append(text)
        print(f'Loaded {len(self.examples)} examples')
    
    def _messages_to_text(self, messages):
        parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'system':
                parts.append(f'<|im_start|>system\n{content}<|im_end|>')
            elif role == 'user':
                parts.append(f'<|im_start|>user\n{content}<|im_end|>')
            elif role == 'assistant':
                parts.append(f'<|im_start|>assistant\n{content}<|im_end|>')
        return '\n'.join(parts)
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        text = self.examples[idx]
        enc = self.tokenizer(
            text, truncation=True, max_length=self.max_length,
            padding='max_length', return_tensors='pt'
        )
        return {
            'input_ids': enc['input_ids'].squeeze(),
            'attention_mask': enc['attention_mask'].squeeze(),
            'labels': enc['input_ids'].squeeze()
        }

# ============================================================================
# MODEL SETUP
# ============================================================================
def setup_model_and_tokenizer():
    print('Loading tokenizer...')
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    print('Loading model (~5 min)...')
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map='cuda:0',
        low_cpu_mem_usage=False,  # CRITICAL: prevents meta-device gradient bugs
        trust_remote_code=True
    )
    print(f'Model loaded. Params: {sum(p.numel() for p in model.parameters())/1e6:.0f}M')
    print(f'GPU memory: {torch.cuda.memory_allocated()/1e9:.1f} GB')
    return model, tokenizer

def apply_lora(model):
    lora_config = LoraConfig(
        r=LORA_R, lora_alpha=LORA_ALPHA,
        target_modules=TARGET_MODULES,
        lora_dropout=LORA_DROPOUT,
        bias='none', task_type=TaskType.CAUSAL_LM
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return model

# ============================================================================
# DATA LOADING
# ============================================================================
def load_datasets(tokenizer):
    datasets = []
    tier_files = [
        ('tier1-reasoning-chat.jsonl', 'tier1'),
        ('tier2-reasoning-chat.jsonl', 'tier2'),
        ('tier3-health-chat.jsonl', 'tier3'),
    ]
    for filename, name in tier_files:
        filepath = os.path.join(DATASET_DIR, filename)
        if os.path.exists(filepath):
            ds = ChatDataset(filepath, tokenizer, max_length=MAX_SEQ_LENGTH)
            datasets.append(ds)
        else:
            print(f'Warning: {filepath} not found')
    if not datasets:
        raise ValueError('No datasets found!')
    combined = ConcatDataset(datasets)
    print(f'Total examples: {len(combined)}')
    return combined

# ============================================================================
# TRAINING CALLBACK
# ============================================================================
class MetricsCallback(TrainerCallback):
    def __init__(self, monitor):
        self.monitor = monitor
    
    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs and 'loss' in logs:
            self.monitor.log_step(
                loss=logs.get('loss', 0),
                lr=logs.get('learning_rate', 0),
                epoch=logs.get('epoch')
            )

# ============================================================================
# MAIN
# ============================================================================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    monitor = TrainingMonitor(OUTPUT_DIR)
    
    model, tokenizer = setup_model_and_tokenizer()
    model = apply_lora(model)
    train_dataset = load_datasets(tokenizer)
    
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        warmup_steps=WARMUP_STEPS,
        logging_steps=LOGGING_STEPS,
        save_steps=SAVE_STEPS,
        save_total_limit=3,
        bf16=True,
        tf32=True,
        optim='adamw_torch',
        weight_decay=0.0,
        max_grad_norm=1.0,
        dataloader_num_workers=2,
        dataloader_pin_memory=True,
        remove_unused_columns=False,
        report_to=['none'],
        logging_dir=os.path.join(OUTPUT_DIR, 'logs')
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
        callbacks=[MetricsCallback(monitor)]
    )
    
    print('Starting training...')
    trainer.train()
    
    final_path = os.path.join(OUTPUT_DIR, 'final')
    trainer.save_model(final_path)
    print(f'Training complete! Saved to {final_path}')

if __name__ == '__main__':
    main()
