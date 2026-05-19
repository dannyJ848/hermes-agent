#!/usr/bin/env python3
"""
STABLE LoRA + SAE + Teacher Distillation Training Config
Verified on DGX Spark (130GB unified memory) with Qwen3.6-27B
Rank 256 is the sweet spot — higher ranks OOM during backward pass.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class TrainConfig:
    """Configuration for stable training on DGX Spark."""
    
    # Model paths
    student_model_path: str = "/data/models/Qwen3.6-27B/"
    teacher_model_path: str = "/data/models/FrankenV8-Final/"
    output_dir: str = "/data/SpecForge/custom_dflash/checkpoints"
    log_file: str = "/mnt/bigssd/train_v2_max1000.log"
    
    # LoRA config — RANK 256 IS THE SWEET SPOT
    lora_r: int = 256          # DO NOT exceed — backward pass OOMs above this
    lora_alpha: int = 512      # 2x rank (standard ratio)
    lora_dropout: float = 0.05
    target_modules: list = None
    
    # Training config
    max_steps: int = 10000      # User requested 10k (was 1000)
    batch_size: int = 1
    grad_accum_steps: int = 4   # Effective batch = 4
    lr: float = 5e-5
    max_grad_norm: float = 1.0
    
    # Memory optimization
    gradient_checkpointing: bool = True   # MANDATORY on unified memory
    use_8bit_adam: bool = True          # Saves ~2GB vs standard AdamW
    
    # Loss components — ALL THREE ACTIVE
    use_sae: bool = True                # SAE feature MSE loss
    use_teacher_distillation: bool = True   # Hidden state MSE vs teacher
    ce_weight_start: float = 0.99
    ce_weight_end: float = 0.90
    distill_weight_start: float = 0.20
    distill_weight_end: float = 0.30
    sae_weight_start: float = 0.05
    sae_weight_end: float = 0.10
    
    # SAE config
    sae_layers: list = None     # e.g., [16, 32]
    sae_feature_dim: int = 1024
    
    # Checkpointing
    save_every: int = 100       # Save every N steps
    resume_from: Optional[str] = None  # e.g., "/data/SpecForge/custom_dflash/checkpoints/checkpoint_step_100"
    
    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = [
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"
            ]
        if self.sae_layers is None:
            self.sae_layers = [16, 32]


# ============================================================
# MEMORY MANAGEMENT UTILITIES
# ============================================================

import torch
import gc

def clear_cache_before_backward():
    """CRITICAL: Call this immediately before loss.backward()"""
    torch.cuda.empty_cache()
    gc.collect()
    torch.cuda.synchronize()

def safe_checkpoint_save(model, optimizer, step, output_dir):
    """Save checkpoint with CPU offload to prevent OOM during save."""
    import os
    checkpoint_path = f"{output_dir}/checkpoint_step_{step}"
    os.makedirs(checkpoint_path, exist_ok=True)
    
    # Move to CPU before saving
    state_dict = {k: v.cpu() for k, v in model.state_dict().items()}
    torch.save(state_dict, f"{checkpoint_path}/adapter_model.safetensors")
    
    # Skip optimizer state — saves ~30GB and often incompatible on resume
    # torch.save(optimizer.state_dict(), f"{checkpoint_path}/optimizer.pt")
    
    torch.cuda.empty_cache()
    return checkpoint_path


# ============================================================
# LAUNCH SCRIPT TEMPLATE
# ============================================================
"""
#!/bin/bash
cd /data/SpecForge/custom_dflash

export MAX_STEPS=10000
export PYTHONUNBUFFERED=1

# Kill any existing training
pkill -f train_lora_sae_teacher_v1.py
sleep 2

# Start training in background
python3 -u train_lora_sae_teacher_v1.py >> /mnt/bigssd/train_v2_max1000.log 2>&1 &
NEW_PID=$!
echo $NEW_PID > /mnt/bigssd/train_v2.pid
echo "Started training PID: $NEW_PID"

# Quick verification
sleep 5
ps -p $NEW_PID -o pid,etime,pcpu,stat,vsz,rss
"""


# ============================================================
# MONITORING COMMANDS
# ============================================================
"""
# Check if process is alive
ps -p $(cat /mnt/bigssd/train_v2.pid) -o pid,etime,pcpu,stat,vsz,rss

# Check latest steps
grep 'Step ' /mnt/bigssd/train_v2_max1000.log | tail -5

# Check for steps >100 (indicates progress past checkpoint resume)
grep -E 'Step 10[1-9]|Step 11[0-9]' /mnt/bigssd/train_v2_max1000.log | tail -3

# Check backward pass completion
grep 'Backward pass complete' /mnt/bigssd/train_v2_max1000.log | tail -3

# Tail log
tail -20 /mnt/bigssd/train_v2_max1000.log
"""
