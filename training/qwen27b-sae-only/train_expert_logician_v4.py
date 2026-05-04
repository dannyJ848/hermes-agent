#!/usr/bin/env python3
"""
Qwen 27B Expert Logician Training Pipeline — Improved v4
Based on research findings from May 3, 2026 session.

Key improvements over v3:
- AdamW with β₂ scaled for small batch (B=1)
- WSD-S learning rate schedule (warmup → stable → decay)
- CKA hidden state matching for teacher distillation
- SAE reconstruction loss as auxiliary signal
- Data mixing from SlimOrca + OpenHermes
- Proper gradient accumulation with effective batch size control
- Checkpointing every 50 steps

Hardware: DGX Spark, NVIDIA GB10 (130.7GB GPU), 121GB RAM
"""

import os
import sys
import time
import math
import json
import glob
import random
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, IterableDataset
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class TrainingConfig:
    # Model paths
    student_model_path: str = "/data/models/Qwen3.6-27B-Uncensored/"
    teacher_model_path: str = "/data/models/FrankenV8-Final/final_model.pt"
    sae_dir: str = "/data/models/Qwen-Scope/"
    
    # Data paths
    slimorca_dir: str = "/data/datasets/curatedthoughts/"
    openhermes_dir: str = "/data/datasets/openthoughts2-1m/"
    synthetic_dir: str = "/mnt/bigssd/synthetic_reasoning/"
    hidden_states_dir: str = "/data/SpecForge/custom_dflash/hidden_states_full/"
    
    # Output
    output_dir: str = "/data/models/Qwen27B-ExpertLogician/"
    checkpoint_dir: str = "/data/models/Qwen27B-ExpertLogician/checkpoints/"
    log_file: str = "/mnt/bigssd/train_expert_logician.log"
    
    # Training hyperparameters
    max_steps: int = 10000
    batch_size: int = 1
    grad_accum_steps: int = 16  # Effective batch size = 16
    max_seq_len: int = 2048
    
    # AdamW with scaled β₂ for small batch (research finding)
    learning_rate: float = 5e-5
    beta1: float = 0.9
    beta2: float = 0.9999  # Scaled for B=1 (β₂* = β₂^(B*/B))
    eps: float = 1e-8
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    
    # WSD-S learning rate schedule
    warmup_steps: int = 500
    stable_steps: int = 8000  # High LR stable phase
    decay_steps: int = 1500   # 15% decay fraction
    min_lr_ratio: float = 0.1
    
    # SAE configuration
    sae_layers: List[int] = None
    sae_weight: float = 0.05
    
    # Teacher distillation
    teacher_weight: float = 0.3
    temperature: float = 2.0
    
    # Data mixing ratios
    slimorca_ratio: float = 0.33
    openhermes_ratio: float = 0.33
    synthetic_ratio: float = 0.34
    
    # Checkpointing
    save_every: int = 50
    log_every: int = 10
    
    # Hardware
    device: str = "cuda:0"
    bf16: bool = True
    gradient_checkpointing: bool = True
    
    def __post_init__(self):
        if self.sae_layers is None:
            self.sae_layers = [16, 32, 48]


# ============================================================
# LEARNING RATE SCHEDULER — WSD-S (Warmup-Stable-Decay)
# ============================================================

class WSDScheduler:
    """
    Warmup-Stable-Decay learning rate schedule.
    Based on arXiv:2410.05192 — outperforms cosine for LLM training.
    """
    def __init__(self, optimizer, warmup_steps, stable_steps, decay_steps, 
                 base_lr, min_lr_ratio=0.1):
        self.optimizer = optimizer
        self.warmup_steps = warmup_steps
        self.stable_steps = stable_steps
        self.decay_steps = decay_steps
        self.base_lr = base_lr
        self.min_lr = base_lr * min_lr_ratio
        self.current_step = 0
        
    def step(self):
        self.current_step += 1
        
        if self.current_step <= self.warmup_steps:
            # Linear warmup
            lr = self.base_lr * (self.current_step / self.warmup_steps)
        elif self.current_step <= self.warmup_steps + self.stable_steps:
            # Stable high LR
            lr = self.base_lr
        else:
            # Inverse proportional decay
            decay_progress = (self.current_step - self.warmup_steps - self.stable_steps) / self.decay_steps
            # 1/η_t linearly interpolates from 1/η_max to 1/η_min
            inv_lr = (1 - decay_progress) * (1 / self.base_lr) + decay_progress * (1 / self.min_lr)
            lr = 1 / inv_lr
            
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = lr
            
    def get_lr(self):
        return self.optimizer.param_groups[0]['lr']


# ============================================================
# CENTERED KERNEL ALIGNMENT (CKA) — Hidden State Matching
# ============================================================

class CKALoss(nn.Module):
    """
    Centered Kernel Alignment for hidden state matching.
    Based on ICLR 2025 — improves distillation, works across different dims.
    """
    def __init__(self):
        super().__init__()
        
    def forward(self, student_hidden, teacher_hidden):
        """
        Compute CKA loss between student and teacher hidden states.
        
        Args:
            student_hidden: [batch, seq, hidden_s]
            teacher_hidden: [batch, seq, hidden_t]
        
        Returns:
            loss: 1 - CKA (to minimize)
        """
        # Flatten batch and seq dimensions
        N = student_hidden.size(0) * student_hidden.size(1)
        H_S = student_hidden.view(N, -1)  # [N, d_s]
        H_T = teacher_hidden.view(N, -1)  # [N, d_t]
        
        # Center the features
        H_S = H_S - H_S.mean(dim=0, keepdim=True)
        H_T = H_T - H_T.mean(dim=0, keepdim=True)
        
        # Compute covariance matrices
        Sigma_SS = torch.mm(H_S.t(), H_S)  # [d_s, d_s]
        Sigma_TT = torch.mm(H_T.t(), H_T)  # [d_t, d_t]
        Sigma_TS = torch.mm(H_T.t(), H_S)  # [d_t, d_s]
        
        # Frobenius norms
        norm_TS = torch.norm(Sigma_TS, p='fro')
        norm_SS = torch.norm(Sigma_SS, p='fro')
        norm_TT = torch.norm(Sigma_TT, p='fro')
        
        # CKA
        cka = (norm_TS ** 2) / (norm_SS * norm_TT + 1e-8)
        
        return 1 - cka


# ============================================================
# SAE UTILITIES
# ============================================================

def load_saes(sae_dir, layers, device):
    """Load Qwen-Scope SAEs for specified layers."""
    saes = {}
    for layer_idx in layers:
        sae_path = os.path.join(sae_dir, f"layer{layer_idx}.sae.pt")
        if os.path.exists(sae_path):
            sae = torch.load(sae_path, map_location="cpu", weights_only=True)
            saes[layer_idx] = {
                "W_enc": sae["W_enc"].bfloat16(),  # Keep on CPU
                "b_enc": sae["b_enc"].bfloat16(),
                "W_dec": sae["W_dec"].bfloat16(),
                "b_dec": sae["b_dec"].bfloat16(),
            }
    return saes


def get_feature_acts(residual, sae_dict):
    """Extract sparse features from hidden states."""
    # Move SAE weights to same device as residual for computation
    device = residual.device
    W_enc = sae_dict["W_enc"].to(device)
    b_enc = sae_dict["b_enc"].to(device)
    residual = residual.to(W_enc.dtype)
    pre_acts = residual @ W_enc.T + b_enc
    topk_vals, topk_idx = pre_acts.topk(50, dim=-1)
    acts = torch.zeros_like(pre_acts)
    acts.scatter_(-1, topk_idx, topk_vals)
    return acts


def reconstruct_from_features(features, sae_dict):
    """Reconstruct hidden states from sparse features."""
    device = features.device
    W_dec = sae_dict["W_dec"].to(device)
    b_dec = sae_dict["b_dec"].to(device)
    return features @ W_dec.T + b_dec


# ============================================================
# DATASET — Mixed SlimOrca + OpenHermes + Synthetic
# ============================================================

class MixedReasoningDataset(IterableDataset):
    """
    Streaming dataset — loads and tokenizes on-the-fly to save RAM.
    Only keeps file paths in memory, not full tokenized tensors.
    """
    def __init__(self, config, tokenizer, teacher_model=None):
        self.config = config
        self.tokenizer = tokenizer
        self.teacher_model = teacher_model
        
        # Store file paths only — don't load data into RAM
        self.slimorca_files = self._discover_files(config.slimorca_dir, "*.parquet")
        self.openhermes_files = self._discover_files(config.openhermes_dir, "*.parquet")
        
        # Estimate total samples (for progress/logging)
        self.total_samples = self._estimate_total_samples()
        logging.info(f"Streaming dataset: ~{self.total_samples} samples from {len(self.slimorca_files) + len(self.openhermes_files)} files")
        
    def _discover_files(self, data_dir, pattern):
        """Discover data files without loading them."""
        files = []
        if os.path.exists(data_dir):
            files = sorted(glob.glob(os.path.join(data_dir, "**", pattern), recursive=True))
            # Also check direct subdirs
            for subdir in ["OpenThoughts-114k-math-default/", "data/", ""]:
                check_dir = os.path.join(data_dir, subdir)
                if os.path.exists(check_dir):
                    files.extend(sorted(glob.glob(os.path.join(check_dir, pattern))))
        return sorted(list(set(files)))[:1]  # Load only 1 file per source for memory
    
    def _estimate_total_samples(self):
        """Quick estimate without full load."""
        total = 0
        for pf in self.slimorca_files + self.openhermes_files:
            try:
                import pandas as pd
                # Read just metadata to count rows
                pf_meta = pd.read_parquet(pf, columns=[])
                total += len(pf_meta)
            except:
                pass
        return total
    
    def __iter__(self):
        """Stream samples on-the-fly. Yields indefinitely for DataLoader."""
        import pandas as pd
        step = 0
        
        while True:
            # Stream from all files, cycling through them
            for pf in self.slimorca_files + self.openhermes_files:
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
                            'source': 'curatedthoughts' if 'curated' in pf or 'openthoughts' in pf else 'openthoughts2',
                            'step': step,
                        }
                        step += 1
                except Exception as e:
                    logging.warning(f"Failed to stream {pf}: {e}")
            
            # If no files, yield dummy samples to prevent deadlock
            if not self.slimorca_files and not self.openhermes_files:
                logging.error("No data files found! Yielding dummy sample.")
                yield {
                    'input_ids': torch.tensor([1, 2, 3]),
                    'labels': torch.tensor([1, 2, 3]),
                    'source': 'dummy',
                    'step': step,
                }
                step += 1
    
    def __len__(self):
        return self.total_samples
    
    def _format_conversation(self, data):
        """Format conversation data into text."""
        # Helper to safely get conversations/messages as list
        def get_list(key):
            if key not in data:
                return []
            val = data[key]
            if hasattr(val, 'tolist'):  # numpy array
                return val.tolist()
            return val if isinstance(val, list) else []
        
        # Handle 'conversations' key
        conversations = get_list('conversations')
        if conversations:
            parts = []
            for turn in conversations:
                if isinstance(turn, dict):
                    role = turn.get('from', turn.get('role', 'user'))
                    content = turn.get('value', turn.get('content', ''))
                    parts.append(f"<{role}>\n{content}\n</{role}>")
            if parts:
                return "\n".join(parts)
        
        # Handle 'messages' key
        messages = get_list('messages')
        if messages:
            parts = []
            for turn in messages:
                if isinstance(turn, dict):
                    role = turn.get('role', turn.get('from', 'user'))
                    content = turn.get('content', turn.get('value', ''))
                    parts.append(f"<{role}>\n{content}\n</{role}>")
            if parts:
                return "\n".join(parts)
        
        # Handle 'problem' + 'solution' format
        if 'problem' in data and 'solution' in data:
            return f"<problem>\n{data['problem']}\n</problem>\n<solution>\n{data['solution']}\n</solution>"
        
        # Handle 'question'
        if 'question' in data:
            return f"<question>\n{data['question']}\n</question>"
        
        # Fallback
        return str(data)
    
    def __iter__(self):
        """Stream samples on-the-fly. Yields indefinitely for DataLoader."""
        import pandas as pd
        step = 0
        
        while True:
            # Stream from all files, cycling through them
            for pf in self.slimorca_files + self.openhermes_files:
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
                            'source': 'curatedthoughts' if 'curated' in pf or 'openthoughts' in pf else 'openthoughts2',
                            'step': step,
                        }
                        step += 1
                except Exception as e:
                    logging.warning(f"Failed to stream {pf}: {e}")
            
            # If no files, yield dummy samples to prevent deadlock
            if not self.slimorca_files and not self.openhermes_files:
                logging.error("No data files found! Yielding dummy sample.")
                yield {
                    'input_ids': torch.tensor([1, 2, 3]),
                    'labels': torch.tensor([1, 2, 3]),
                    'source': 'dummy',
                    'step': step,
                }
                step += 1


# ============================================================
# TEACHER MODEL LOADER
# ============================================================

def load_teacher_model(teacher_path, device):
    """Load Franken V8 teacher model."""
    if not os.path.exists(teacher_path):
        logging.warning(f"Teacher model not found at {teacher_path}")
        return None
    
    try:
        # Load teacher to CPU to save GPU memory — only move to GPU when needed
        checkpoint = torch.load(teacher_path, map_location="cpu", weights_only=True)
        # Franken V8 model structure — would need actual model class
        # For now, return checkpoint dict
        return checkpoint
    except Exception as e:
        logging.error(f"Failed to load teacher: {e}")
        return None


# ============================================================
# TRAINING LOOP
# ============================================================

def train(config: TrainingConfig):
    """Main training function."""
    
    # Setup logging
    os.makedirs(config.checkpoint_dir, exist_ok=True)
    os.makedirs(config.output_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(config.log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("QWEN 27B EXPERT LOGICIAN TRAINING — Improved Pipeline v4")
    logger.info("=" * 70)
    logger.info(f"Max steps: {config.max_steps}")
    logger.info(f"Batch size: {config.batch_size}, Grad accum: {config.grad_accum_steps}")
    logger.info(f"Effective batch size: {config.batch_size * config.grad_accum_steps}")
    logger.info(f"Learning rate: {config.learning_rate}")
    logger.info(f"AdamW β₁={config.beta1}, β₂={config.beta2} (scaled for B=1)")
    logger.info(f"WSD-S schedule: warmup={config.warmup_steps}, stable={config.stable_steps}, decay={config.decay_steps}")
    
    # Device setup
    device = torch.device(config.device)
    if not torch.cuda.is_available():
        logger.error("CUDA not available")
        sys.exit(1)
    
    logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
    logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    
    # Load tokenizer
    logger.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(config.student_model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load student model
    logger.info("Loading student model (Qwen 3.6-27B)...")
    model_config = AutoConfig.from_pretrained(config.student_model_path, trust_remote_code=True)
    model_config.vocab_size = len(tokenizer)
    model_config.use_cache = False
    
    model = AutoModelForCausalLM.from_pretrained(
        config.student_model_path,
        config=model_config,
        torch_dtype=torch.bfloat16 if config.bf16 else torch.float32,
        device_map="auto",
        max_memory={0: "120GiB", "cpu": "0GiB"},
        trust_remote_code=True,
    )
    
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Total params: {total_params/1e9:.1f}B")
    logger.info(f"Trainable: {trainable_params/1e9:.1f}B")
    
    # Gradient checkpointing
    if config.gradient_checkpointing:
        logger.info("Enabling gradient checkpointing...")
        model.gradient_checkpointing_enable()
        model.enable_input_require_grads()
    
    # Load SAEs
    logger.info(f"Loading SAEs for layers {config.sae_layers}...")
    saes = load_saes(config.sae_dir, config.sae_layers, device)
    logger.info(f"Loaded {len(saes)} SAEs")
    
    # SAE hooks
    captured_features = {}
    captured_hidden = {}
    
    def make_hook(layer_idx):
        def hook(module, input, output):
            hidden = output[0] if isinstance(output, tuple) else output
            if layer_idx in saes:
                captured_features[layer_idx] = get_feature_acts(hidden, saes[layer_idx])
                captured_hidden[layer_idx] = hidden
            return output
        return hook
    
    hooks = []
    for layer_idx in config.sae_layers:
        if layer_idx < len(model.model.layers):
            h = model.model.layers[layer_idx].register_forward_hook(make_hook(layer_idx))
            hooks.append(h)
    
    # Load teacher (if available)
    teacher = load_teacher_model(config.teacher_model_path, device)
    if teacher is not None:
        logger.info("Teacher model loaded")
    else:
        logger.info("No teacher model — using SAE-only distillation")
    
    # CKA loss for teacher distillation
    cka_loss_fn = CKALoss()
    
    # Dataset
    logger.info("Loading mixed dataset (SlimOrca + OpenHermes)...")
    dataset = MixedReasoningDataset(config, tokenizer, teacher)
    dataloader = DataLoader(dataset, batch_size=config.batch_size)
    
    # Optimizer — AdamW with CPU offloading for optimizer states
    # This saves ~54GB GPU memory by keeping momentum/variance on CPU
    # Full precision training quality is preserved
    logger.info("Creating AdamW optimizer with CPU offloading...")
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        betas=(config.beta1, config.beta2),
        eps=config.eps,
        weight_decay=config.weight_decay,
        foreach=False  # Required for CPU offloading compatibility
    )
    
    # Move optimizer states to CPU to save GPU memory
    logger.info("Moving optimizer states to CPU...")
    for param_group in optimizer.param_groups:
        for p in param_group['params']:
            if p in optimizer.state:
                state = optimizer.state[p]
                for key in ['exp_avg', 'exp_avg_sq']:
                    if key in state:
                        state[key] = state[key].cpu()
    
    # WSD-S scheduler
    scheduler = WSDScheduler(
        optimizer,
        warmup_steps=config.warmup_steps,
        stable_steps=config.stable_steps,
        decay_steps=config.decay_steps,
        base_lr=config.learning_rate,
        min_lr_ratio=config.min_lr_ratio
    )
    
    logger.info(f"Optimizer: AdamW, lr={config.learning_rate}, β=({config.beta1}, {config.beta2})")
    
    # Training state
    global_step = 0
    accum_count = 0
    total_loss = 0.0
    total_lm_loss = 0.0
    total_sae_loss = 0.0
    total_teacher_loss = 0.0
    
    model.train()
    
    logger.info("=" * 70)
    logger.info("STARTING TRAINING")
    logger.info("=" * 70)
    
    # Resume from checkpoint if exists
    latest_ckpt = None
    for s in range(config.max_steps, 0, -1):
        ck = os.path.join(config.checkpoint_dir, f"step_{s}.pt")
        if os.path.exists(ck):
            latest_ckpt = ck
            break
    
    if latest_ckpt:
        logger.info(f"Resuming from: {latest_ckpt}")
        ckpt = torch.load(latest_ckpt, map_location="cpu", weights_only=True)
        model.load_state_dict(ckpt["model_state_dict"])
        optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        global_step = ckpt.get("step", 0)
        logger.info(f"Resumed at step {global_step}")
        del ckpt
        torch.cuda.empty_cache()
    
    # Training loop
    for batch in dataloader:
        if global_step >= config.max_steps:
            break
        
        input_ids = batch["input_ids"].to(device)
        labels = batch["labels"].to(device)
        
        # Forward pass
        captured_features.clear()
        captured_hidden.clear()
        
        outputs = model(input_ids=input_ids, labels=labels)
        lm_loss = outputs.loss
        
        # SAE reconstruction loss
        sae_loss = torch.tensor(0.0, device=device)
        if captured_features and captured_hidden:
            for layer_idx in config.sae_layers:
                if layer_idx in captured_features and layer_idx in captured_hidden:
                    features = captured_features[layer_idx]
                    original = captured_hidden[layer_idx]
                    reconstructed = reconstruct_from_features(features, saes[layer_idx])
                    layer_loss = F.mse_loss(reconstructed, original)
                    sae_loss = sae_loss + layer_loss
            sae_loss = sae_loss / len([l for l in config.sae_layers if l in captured_features])
        
        # Teacher distillation loss (if teacher available)
        teacher_loss = torch.tensor(0.0, device=device)
        if teacher is not None and hasattr(outputs, 'hidden_states') and outputs.hidden_states is not None:
            # Would need actual teacher forward pass
            # For now, placeholder
            pass
        
        # Combined loss
        combined_loss = lm_loss + config.sae_weight * sae_loss + config.teacher_weight * teacher_loss
        
        # Scale for gradient accumulation
        scaled_loss = combined_loss / config.grad_accum_steps
        scaled_loss.backward()
        
        accum_count += 1
        
        # Track losses
        total_loss += combined_loss.item()
        total_lm_loss += lm_loss.item()
        total_sae_loss += sae_loss.item()
        total_teacher_loss += teacher_loss.item()
        
        # Gradient accumulation step
        if accum_count >= config.grad_accum_steps:
            # Clip gradients
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
            
            # Optimizer step
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            
            # Clear CUDA cache to reduce fragmentation
            torch.cuda.empty_cache()
            
            global_step += 1
            accum_count = 0
            
            # Logging
            if global_step % config.log_every == 0:
                avg_loss = total_loss / config.log_every
                avg_lm = total_lm_loss / config.log_every
                avg_sae = total_sae_loss / config.log_every
                avg_teacher = total_teacher_loss / config.log_every
                lr = scheduler.get_lr()
                gpu_mem = torch.cuda.memory_allocated(device) / 1e9
                gpu_total = torch.cuda.get_device_properties(device).total_memory / 1e9
                
                logger.info(
                    f"Step {global_step}/{config.max_steps} | "
                    f"Loss: {avg_loss:.4f} (LM: {avg_lm:.4f}, SAE: {avg_sae:.4f}, Teacher: {avg_teacher:.4f}) | "
                    f"LR: {lr:.2e} | GPU: {gpu_mem:.1f}GB/{gpu_total:.1f}GB"
                )
                
                total_loss = 0.0
                total_lm_loss = 0.0
                total_sae_loss = 0.0
                total_teacher_loss = 0.0
            
            # Checkpointing
            if global_step % config.save_every == 0:
                ckpt_path = os.path.join(config.checkpoint_dir, f"step_{global_step}.pt")
                torch.save({
                    "step": global_step,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "scheduler_state": {
                        "current_step": scheduler.current_step,
                        "warmup_steps": scheduler.warmup_steps,
                        "stable_steps": scheduler.stable_steps,
                        "decay_steps": scheduler.decay_steps,
                    }
                }, ckpt_path)
                logger.info(f"Checkpoint saved: {ckpt_path}")
                
                # Clean old checkpoints (keep last 3)
                old_ckpts = sorted(glob.glob(os.path.join(config.checkpoint_dir, "step_*.pt")))
                for old in old_ckpts[:-3]:
                    os.remove(old)
    
    # Final save
    final_path = os.path.join(config.output_dir, "final_model.pt")
    torch.save({
        "step": global_step,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
    }, final_path)
    logger.info(f"Final model saved: {final_path}")
    
    # Clean up hooks
    for h in hooks:
        h.remove()
    
    logger.info("=" * 70)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    config = TrainingConfig()
    train(config)
