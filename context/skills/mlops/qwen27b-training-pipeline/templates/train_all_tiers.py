#!/usr/bin/env python3
"""
Qwen 27B LoRA training with ALL THREE TIERS of data.
Working template — verified on DGX Spark GB10 with system Python.

Tier 1: Pre-tokenized (327k examples) — loaded from JSONL
Tier 2: Raw chat format (131k examples) — tokenized on-the-fly
Tier 3: Raw chat format (194 examples) — tokenized on-the-fly, repeated for balance

CRITICAL: Use system Python (/usr/bin/python3), NOT train-venv.
train-venv has CPU-only PyTorch which will cause apparent "deadlocks".
"""
import os
import sys
import json
import time
import torch
import logging
from dataclasses import dataclass

log_dir = "/data/SpecForge/custom_dflash/logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"train_alltiers_{time.strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_file)]
)
logger = logging.getLogger(__name__)

def format_chat(messages):
    """Convert messages list to a single text string."""
    parts = []
    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if role == 'system':
            parts.append(f"System: {content}")
        elif role == 'user':
            parts.append(f"User: {content}")
        elif role == 'assistant':
            parts.append(f"Assistant: {content}")
    return "\n\n".join(parts)

class MultiTierDataset:
    def __init__(self, tokenizer, seq_len=1024):
        self.tokenizer = tokenizer
        self.seq_len = seq_len
        self.examples = []
        
        # Tier 1: Pre-tokenized
        tier1_path = "/data/SpecForge/custom_dflash/preprocessed/tier1_preprocessed.jsonl"
        logger.info(f"Loading Tier 1 from {tier1_path}...")
        count = 0
        with open(tier1_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                if 'input_ids' in data and 'labels' in data:
                    self.examples.append({
                        'input_ids': torch.tensor(data['input_ids'][:seq_len], dtype=torch.long),
                        'labels': torch.tensor(data['labels'][:seq_len], dtype=torch.long),
                        'tier': 1
                    })
                    count += 1
        logger.info(f"Tier 1 loaded: {count} examples")
        
        # Tier 2: Raw chat - tokenize on the fly
        tier2_path = "/data/SpecForge/custom_dflash/datasets/tier2-reasoning-chat.jsonl"
        logger.info(f"Loading Tier 2 from {tier2_path}...")
        count = 0
        with open(tier2_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                if 'messages' in data:
                    text = format_chat(data['messages'])
                    encoded = tokenizer(text, truncation=True, max_length=seq_len, return_tensors='pt')
                    input_ids = encoded['input_ids'][0]
                    labels = input_ids.clone()
                    self.examples.append({
                        'input_ids': input_ids,
                        'labels': labels,
                        'tier': 2
                    })
                    count += 1
        logger.info(f"Tier 2 loaded: {count} examples")
        
        # Tier 3: Raw chat - small but high quality, repeat for balance
        tier3_path = "/data/SpecForge/custom_dflash/datasets/tier3-health-chat.jsonl"
        logger.info(f"Loading Tier 3 from {tier3_path}...")
        tier3_examples = []
        with open(tier3_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                if 'messages' in data:
                    text = format_chat(data['messages'])
                    encoded = tokenizer(text, truncation=True, max_length=seq_len, return_tensors='pt')
                    input_ids = encoded['input_ids'][0]
                    labels = input_ids.clone()
                    tier3_examples.append({
                        'input_ids': input_ids,
                        'labels': labels,
                        'tier': 3
                    })
        
        # Repeat tier 3 to get ~5k examples
        repeat_count = max(1, 5000 // len(tier3_examples)) if tier3_examples else 0
        for _ in range(repeat_count):
            self.examples.extend(tier3_examples)
        logger.info(f"Tier 3 loaded: {len(tier3_examples)} unique, {len(tier3_examples)*repeat_count} total")
        
        logger.info(f"Total examples: {len(self.examples)}")
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        return self.examples[idx]

def collate_fn(batch, pad_token_id):
    max_len = max(item['input_ids'].shape[0] for item in batch)
    input_ids_list = []
    labels_list = []
    for item in batch:
        seq_len = item['input_ids'].shape[0]
        if seq_len < max_len:
            padding = torch.full((max_len - seq_len,), pad_token_id, dtype=torch.long)
            input_ids = torch.cat([item['input_ids'], padding])
            labels = torch.cat([item['labels'], padding])
        else:
            input_ids = item['input_ids']
            labels = item['labels']
        input_ids_list.append(input_ids)
        labels_list.append(labels)
    return {
        'input_ids': torch.stack(input_ids_list),
        'labels': torch.stack(labels_list),
    }

def main():
    logger.info("=" * 70)
    logger.info("QWEN 27B LoRA - ALL THREE TIERS")
    logger.info("=" * 70)
    
    # Config
    model_path = "/data/models/Qwen3.6-27B-Uncensored/"
    checkpoint_dir = "/data/SpecForge/custom_dflash/checkpoints/"
    seq_len = 1024
    batch_size = 1
    grad_accum = 4
    lora_r = 256
    lora_alpha = 512
    lr = 1e-4
    max_steps = 10000
    save_every = 500
    log_every = 10
    
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Load tokenizer
    logger.info("Loading tokenizer...")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load model
    logger.info("Loading model...")
    from transformers import AutoModelForCausalLM
    from peft import LoraConfig, get_peft_model, TaskType
    
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        low_cpu_mem_usage=False,  # CRITICAL for >20B models with LoRA
    )
    logger.info(f"Model loaded. GPU: {torch.cuda.memory_allocated()/1e9:.1f}GB")
    
    # LoRA
    logger.info("Applying LoRA...")
    lora_config = LoraConfig(
        r=lora_r, lora_alpha=lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05, bias="none", task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    logger.info(f"LoRA applied. GPU: {torch.cuda.memory_allocated()/1e9:.1f}GB")
    
    # Gradient checkpointing
    logger.info("Enabling gradient checkpointing...")
    model.config.use_cache = False
    model.gradient_checkpointing_enable({"use_reentrant": False})
    model.train()
    logger.info(f"GC enabled. GPU: {torch.cuda.memory_allocated()/1e9:.1f}GB")
    
    # Optimizer
    from bitsandbytes.optim import AdamW8bit
    optimizer = AdamW8bit(
        [p for p in model.parameters() if p.requires_grad],
        lr=lr, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.01,
    )
    logger.info("Optimizer created")
    
    # Dataset - all three tiers
    dataset = MultiTierDataset(tokenizer, seq_len=seq_len)
    
    from torch.utils.data import DataLoader
    dataloader = DataLoader(
        dataset, batch_size=batch_size, shuffle=True, num_workers=0,
        collate_fn=lambda batch: collate_fn(batch, tokenizer.pad_token_id),
    )
    logger.info("DataLoader ready")
    
    # Training loop
    global_step = 0
    batch_count = 0
    accumulated_loss = 0.0
    start_time = time.time()
    
    logger.info("=" * 70)
    logger.info("STARTING TRAINING")
    logger.info("=" * 70)
    
    while global_step < max_steps:
        for batch in dataloader:
            if global_step >= max_steps:
                break
            
            input_ids = batch['input_ids'].to('cuda')
            labels = batch['labels'].to('cuda')
            
            outputs = model(input_ids=input_ids, labels=labels)
            loss = outputs.loss / grad_accum
            loss.backward()
            
            accumulated_loss += loss.item() * grad_accum
            batch_count += 1
            
            if batch_count % grad_accum == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                optimizer.zero_grad()
                
                if global_step % log_every == 0:
                    elapsed = time.time() - start_time
                    speed = global_step / elapsed if elapsed > 0 and global_step > 0 else 0.001
                    eta_hours = (max_steps - global_step) / speed / 3600 if speed > 0 else 999
                    logger.info(
                        f"Step {global_step}/{max_steps} | "
                        f"Loss: {accumulated_loss/grad_accum:.4f} | "
                        f"GPU: {torch.cuda.memory_allocated()/1e9:.1f}GB | "
                        f"Speed: {speed:.3f} steps/s | "
                        f"ETA: {eta_hours:.1f}h"
                    )
                
                accumulated_loss = 0.0
                global_step += 1
                
                if global_step % save_every == 0:
                    ckpt_path = os.path.join(checkpoint_dir, f"checkpoint_step_{global_step}")
                    os.makedirs(ckpt_path, exist_ok=True)
                    model.save_pretrained(ckpt_path)
                    tokenizer.save_pretrained(ckpt_path)
                    logger.info(f"Checkpoint saved: {ckpt_path}")
    
    # Final save
    final_path = os.path.join(checkpoint_dir, "final_model")
    model.save_pretrained(final_path)
    tokenizer.save_pretrained(final_path)
    logger.info(f"Final model saved: {final_path}")
    logger.info("TRAINING COMPLETE")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.exception("Training failed!")
        sys.exit(1)
