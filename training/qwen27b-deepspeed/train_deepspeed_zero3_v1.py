#!/usr/bin/env python3
"""
Qwen 27B Expert Logician Training — DeepSpeed ZeRO-3 Offload v1
Uses DeepSpeed ZeRO-3 with CPU offloading for full fine-tuning.

Key features:
- ZeRO-3 partitions parameters, gradients, optimizer states across GPU+CPU
- Offloads optimizer states AND parameters to CPU
- Enables 27B full fine-tuning on single 130GB GPU + 128GB RAM
- Memory footprint: ~27GB GPU (model shards) + ~81GB CPU (optimizer + params)

Based on DeepSpeed ZeRO-3 Offload tutorial:
https://www.deepspeed.ai/2021/03/07/zero3-offload.html
"""

import os
import sys
import json
import logging
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

import torch
import torch.nn.functional as F

# DeepSpeed
try:
    import deepspeed
    from deepspeed.ops.adam import DeepSpeedCPUAdam
except ImportError:
    print("ERROR: deepspeed not installed. Run: pip install deepspeed")
    sys.exit(1)

# Transformers
try:
    from transformers import (
        AutoModelForCausalLM, AutoTokenizer,
        get_cosine_schedule_with_warmup
    )
except ImportError:
    print("ERROR: transformers not installed")
    sys.exit(1)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class TrainConfig:
    # Model paths
    student_model_path: str = "/data/models/Qwen3.6-27B-Uncensored/"
    teacher_model_path: str = "/data/models/FrankenV8-Final/final_model.pt"
    sae_dir: str = "/data/models/Qwen-Scope/"
    
    # Data paths
    curatedthoughts_dir: str = "/data/datasets/curatedthoughts/"
    openthoughts_dir: str = "/data/datasets/openthoughts2-1m/"
    
    # DeepSpeed config
    deepspeed_config: str = "ds_config_zero3_offload.json"
    
    # Training
    max_steps: int = 10000
    batch_size: int = 1
    grad_accum_steps: int = 16
    max_seq_len: int = 2048
    
    # SAE
    sae_layers: List[int] = None
    sae_weight: float = 0.05
    
    # Checkpointing
    save_every: int = 500
    checkpoint_dir: str = "/data/SpecForge/custom_dflash/checkpoints/"
    
    def __post_init__(self):
        if self.sae_layers is None:
            self.sae_layers = [16, 32, 48]


# ============================================================
# SAE UTILITIES
# ============================================================

def load_sae(sae_dir: str, layer_idx: int, device: str = "cpu"):
    """Load a single SAE for a specific layer."""
    sae_path = Path(sae_dir) / f"sae_layer_{layer_idx}.pt"
    if not sae_path.exists():
        logging.warning(f"SAE not found: {sae_path}")
        return None
    
    try:
        sae = torch.load(sae_path, map_location=device)
        logging.info(f"Loaded SAE for layer {layer_idx}")
        return sae
    except Exception as e:
        logging.warning(f"Failed to load SAE layer {layer_idx}: {e}")
        return None


# ============================================================
# STREAMING DATASET
# ============================================================

class StreamingReasoningDataset(torch.utils.data.IterableDataset):
    """Memory-efficient streaming dataset."""
    
    def __init__(self, config: TrainConfig, tokenizer):
        self.config = config
        self.tokenizer = tokenizer
        self.files = []
        self._discover_files()
        logging.info(f"Streaming dataset: {len(self.files)} files")
    
    def _discover_files(self):
        for dir_path in [self.config.curatedthoughts_dir, self.config.openthoughts_dir]:
            if os.path.exists(dir_path):
                for f in os.listdir(dir_path):
                    if f.endswith('.parquet'):
                        self.files.append(os.path.join(dir_path, f))
    
    def _format_conversation(self, data: dict) -> str:
        if 'conversations' in data and isinstance(data['conversations'], list):
            convs = data['conversations']
            if isinstance(convs, (list, tuple)) and len(convs) > 0:
                if isinstance(convs[0], dict) and 'value' in convs[0]:
                    return "\n".join([c['value'] for c in convs if 'value' in c])
                elif isinstance(convs[0], str):
                    return "\n".join(convs)
        
        if 'messages' in data and isinstance(data['messages'], list):
            msgs = data['messages']
            if isinstance(msgs, list) and len(msgs) > 0:
                if isinstance(msgs[0], dict) and 'content' in msgs[0]:
                    return "\n".join([m['content'] for m in msgs if 'content' in m])
        
        if 'problem' in data and 'solution' in data:
            return f"Problem: {data['problem']}\nSolution: {data['solution']}"
        
        if 'question' in data and 'answer' in data:
            return f"Question: {data['question']}\nAnswer: {data['answer']}"
        
        if 'question' in data:
            return f"<question>\n{data['question']}\n</question>"
        
        return str(data)
    
    def __iter__(self):
        import pandas as pd
        step = 0
        
        while True:
            for pf in self.files:
                try:
                    df = pd.read_parquet(pf)
                    for _, row in df.iterrows():
                        text = self._format_conversation(row.to_dict())
                        tokens = self.tokenizer(text, truncation=True,
                                              max_length=self.config.max_seq_len,
                                              return_tensors="pt")
                        yield {
                            'input_ids': tokens['input_ids'].squeeze(0),
                            'labels': tokens['input_ids'].squeeze(0).clone(),
                            'step': step,
                        }
                        step += 1
                except Exception as e:
                    logging.warning(f"Failed to stream {pf}: {e}")
            
            if not self.files:
                logging.error("No data files found!")
                yield {
                    'input_ids': torch.tensor([1, 2, 3]),
                    'labels': torch.tensor([1, 2, 3]),
                    'step': step,
                }
                step += 1


# ============================================================
# TRAINING LOOP
# ============================================================

def train(config: TrainConfig):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    logging.info("=" * 70)
    logging.info("QWEN 27B EXPERT LOGICIAN — DeepSpeed ZeRO-3 Offload v1")
    logging.info("=" * 70)
    logging.info(f"Max steps: {config.max_steps}")
    logging.info(f"Batch size: {config.batch_size}, Grad accum: {config.grad_accum_steps}")
    logging.info(f"DeepSpeed config: {config.deepspeed_config}")
    
    # Load tokenizer
    logging.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(config.student_model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load model WITH DeepSpeed, not before
    logging.info("Loading student model (Qwen 3.6-27B)...")
    
    # Create model on meta device first (no memory allocation)
    with deepspeed.zero.Init(config_dict_or_path=config.deepspeed_config):
        model = AutoModelForCausalLM.from_pretrained(
            config.student_model_path,
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
        )
    
    # Enable gradient checkpointing
    model.gradient_checkpointing_enable()
    
    # Load SAEs
    saes = {}
    for layer_idx in config.sae_layers:
        sae = load_sae(config.sae_dir, layer_idx, device="cpu")
        if sae is not None:
            saes[layer_idx] = sae
    
    # Dataset
    logging.info("Loading streaming dataset...")
    dataset = StreamingReasoningDataset(config, tokenizer)
    
    # Initialize DeepSpeed
    logging.info("Initializing DeepSpeed ZeRO-3 Offload...")
    
    # Create DeepSpeed config if not exists
    if not os.path.exists(config.deepspeed_config):
        ds_config = {
            "bf16": {"enabled": True},
            "zero_optimization": {
                "stage": 3,
                "offload_optimizer": {
                    "device": "cpu",
                    "pin_memory": True
                },
                "offload_param": {
                    "device": "cpu",
                    "pin_memory": True
                },
                "overlap_comm": True,
                "contiguous_gradients": True,
                "sub_group_size": 1e9,
                "reduce_bucket_size": "auto",
                "stage3_prefetch_bucket_size": "auto",
                "stage3_param_persistence_threshold": "auto",
                "stage3_max_live_parameters": 1e9,
                "stage3_max_reuse_distance": 1e9,
                "stage3_gather_16bit_weights_on_model_save": True
            },
            "gradient_accumulation_steps": config.grad_accum_steps,
            "gradient_clipping": 1.0,
            "steps_per_print": 10,
            "train_batch_size": 16,
            "train_micro_batch_size_per_gpu": 1,
            "gradient_accumulation_steps": 16,
            "optimizer": {
                "type": "AdamW",
                "params": {
                    "lr": 5e-5,
                    "betas": [0.9, 0.999],
                    "eps": 1e-8,
                    "weight_decay": 0.01
                }
            },
            "scheduler": {
                "type": "WarmupCosineLR",
                "params": {
                    "warmup_min_lr": 0,
                    "warmup_max_lr": 5e-5,
                    "warmup_num_steps": 500,
                    "total_num_steps": config.max_steps
                }
            }
        }
        with open(config.deepspeed_config, 'w') as f:
            json.dump(ds_config, f, indent=2)
        logging.info(f"Created DeepSpeed config: {config.deepspeed_config}")
    
    # Initialize DeepSpeed engine
    model_engine, optimizer, _, _ = deepspeed.initialize(
        model=model,
        model_parameters=model.parameters(),
        config=config.deepspeed_config,
    )
    
    logging.info("DeepSpeed engine initialized")
    logging.info(f"Model device: {model_engine.device}")
    
    # Training state
    global_step = 0
    accumulated_loss = 0.0
    
    # Checkpoint directory
    os.makedirs(config.checkpoint_dir, exist_ok=True)
    
    logging.info("=" * 70)
    logging.info("STARTING TRAINING")
    logging.info("=" * 70)
    
    model_engine.train()
    
    for batch in dataset:
        if global_step >= config.max_steps:
            break
        
        # Move batch to device
        input_ids = batch['input_ids'].to(model_engine.device)
        labels = batch['labels'].to(model_engine.device)
        
        # Forward pass
        outputs = model_engine(input_ids=input_ids, labels=labels)
        loss = outputs.loss
        
        # Backward pass (DeepSpeed handles gradient accumulation)
        model_engine.backward(loss)
        
        # Step (DeepSpeed handles grad accum internally)
        model_engine.step()
        
        accumulated_loss += loss.item()
        
        # Logging
        if global_step % 10 == 0:
            current_lr = optimizer.param_groups[0]['lr']
            avg_loss = accumulated_loss / min(10, global_step + 1)
            logging.info(
                f"Step {global_step}/{config.max_steps} | "
                f"Loss: {avg_loss:.4f} | LR: {current_lr:.2e}"
            )
            accumulated_loss = 0.0
        
        # Checkpoint
        if global_step % config.save_every == 0 and global_step > 0:
            checkpoint_path = os.path.join(
                config.checkpoint_dir,
                f"checkpoint_step_{global_step}"
            )
            model_engine.save_checkpoint(checkpoint_path)
            logging.info(f"Saved checkpoint: {checkpoint_path}")
        
        global_step += 1
    
    # Final save
    final_path = os.path.join(config.checkpoint_dir, "final_model")
    model_engine.save_checkpoint(final_path)
    logging.info(f"Training complete! Final model saved to {final_path}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    config = TrainConfig()
    
    if os.environ.get("MAX_STEPS"):
        config.max_steps = int(os.environ.get("MAX_STEPS"))
    
    train(config)
