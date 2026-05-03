#!/usr/bin/env python3
"""
Phase 2: Train VLLM-Compatible DFlash Draft Model for Qwen3.6-27B

This script trains a draft model that can be loaded DIRECTLY into vLLM's
DFlashQwen3ForCausalLM without any weight conversion.

Architecture matches vLLM exactly:
- head_dim = 160 (5120/32)
- num_heads = 32, num_kv_heads = 4 (GQA)
- SwiGLU MLP (gate_up_proj + down_proj)
- Fused QKV projection
- RMSNorm (compatible with vLLM)
- Correct key names for vLLM weight loading

Uses existing hidden states from /data/SpecForge/custom_dflash/hidden_states_full/
"""

import argparse
import json
import os
import math
import random
import time
import logging
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
from transformers import AutoTokenizer

# ============================================================
# CONFIGURATION
# ============================================================

# Qwen3.6-27B architecture (MUST match vLLM expectations)
HIDDEN_SIZE = 5120
NUM_ATTENTION_HEADS = 32
NUM_KEY_VALUE_HEADS = 4
HEAD_DIM = HIDDEN_SIZE // NUM_ATTENTION_HEADS  # 160
INTERMEDIATE_SIZE = 13824
VOCAB_SIZE = 152064
MAX_POSITION_EMBEDDINGS = 131072
RMS_NORM_EPS = 1e-6

# Draft model config
NUM_HIDDEN_LAYERS = 8  # Draft model depth (can be tuned)
AUX_LAYER_IDS = [1, 19, 36]  # Which target layers to use as aux hidden states
NUM_AUX_LAYERS = len(AUX_LAYER_IDS)

# Training config
DEFAULT_LR = 0.0001
DEFAULT_BATCH_SIZE = 4
DEFAULT_MAX_LENGTH = 4096
DEFAULT_EPOCHS = 1
DEFAULT_STEPS = 10000
DEFAULT_WARMUP_STEPS = 500
DEFAULT_GRAD_ACCUM = 2

# Paths
DEFAULT_HIDDEN_STATES_DIR = "/data/SpecForge/custom_dflash/hidden_states_full"
DEFAULT_OUTPUT_DIR = "/data/models/Qwen3.6-27B-DFlash-vLLM-Compatible"
DEFAULT_TARGET_MODEL = "/data/models/Qwen3.6-27B-Uncensored"

# ============================================================
# VLLM-COMPATIBLE ARCHITECTURE
# ============================================================

class VLLMCompatibleRMSNorm(nn.Module):
    """RMSNorm compatible with vLLM's RMSNorm implementation."""
    def __init__(self, hidden_size, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.variance_epsilon = eps

    def forward(self, hidden_states):
        input_dtype = hidden_states.dtype
        hidden_states = hidden_states.to(torch.float32)
        variance = hidden_states.pow(2).mean(-1, keepdim=True)
        hidden_states = hidden_states * torch.rsqrt(variance + self.variance_epsilon)
        return self.weight * hidden_states.to(input_dtype)


class VLLMCompatibleSwiGLU(nn.Module):
    """SwiGLU MLP matching vLLM's Qwen3MLP implementation.
    
    vLLM uses fused gate_up_proj: [2*intermediate_size, hidden_size]
    which is split into gate and up projections.
    """
    def __init__(self, hidden_size, intermediate_size):
        super().__init__()
        self.hidden_size = hidden_size
        self.intermediate_size = intermediate_size
        
        # Fused gate_up_proj: [2*intermediate_size, hidden_size]
        # vLLM splits this into gate and up during forward
        self.gate_up_proj = nn.Linear(hidden_size, 2 * intermediate_size, bias=False)
        self.down_proj = nn.Linear(intermediate_size, hidden_size, bias=False)
        self.act_fn = F.silu  # SwiGLU activation

    def forward(self, x):
        # vLLM-style: split gate_up_proj into gate and up
        gate_up = self.gate_up_proj(x)
        gate, up = gate_up.chunk(2, dim=-1)
        # SwiGLU: silu(gate) * up
        return self.down_proj(self.act_fn(gate) * up)


class VLLMCompatibleAttention(nn.Module):
    """Attention matching vLLM's DFlashQwen3Attention.
    
    Uses FUSED qkv_proj to match vLLM's QKVParallelLinear.
    """
    def __init__(self, hidden_size, num_heads, num_kv_heads, head_dim):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.num_kv_heads = num_kv_heads
        self.head_dim = head_dim
        
        # QKV sizes for fused projection
        self.q_size = num_heads * head_dim  # 5120
        self.kv_size = num_kv_heads * head_dim  # 640
        self.qkv_size = self.q_size + 2 * self.kv_size  # 6400
        
        # Fused QKV projection (matches vLLM's QKVParallelLinear)
        self.qkv_proj = nn.Linear(hidden_size, self.qkv_size, bias=False)
        
        # Output projection
        self.o_proj = nn.Linear(self.q_size, hidden_size, bias=False)
        
        # Per-head RMSNorm for q and k (vLLM style)
        self.q_norm = VLLMCompatibleRMSNorm(head_dim, eps=RMS_NORM_EPS)
        self.k_norm = VLLMCompatibleRMSNorm(head_dim, eps=RMS_NORM_EPS)
        
        self.scaling = head_dim ** -0.5

    def forward(self, hidden_states, attention_mask=None):
        batch_size, seq_len, _ = hidden_states.shape
        
        # Fused QKV projection
        qkv = self.qkv_proj(hidden_states)
        q, k, v = qkv.split([self.q_size, self.kv_size, self.kv_size], dim=-1)
        
        # Reshape for multi-head attention
        # Q: [batch, seq, num_heads, head_dim]
        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim)
        k = k.view(batch_size, seq_len, self.num_kv_heads, self.head_dim)
        v = v.view(batch_size, seq_len, self.num_kv_heads, self.head_dim)
        
        # Per-head RMSNorm (vLLM style)
        q = self.q_norm(q)
        k = self.k_norm(k)
        
        # Transpose for attention: [batch, num_heads, seq, head_dim]
        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)
        
        # Repeat k/v heads for GQA (grouped query attention)
        if self.num_kv_heads < self.num_heads:
            k = k.repeat_interleave(self.num_heads // self.num_kv_heads, dim=1)
            v = v.repeat_interleave(self.num_heads // self.num_kv_heads, dim=1)
        
        # Scaled dot-product attention
        attn_output = F.scaled_dot_product_attention(
            q, k, v,
            attn_mask=attention_mask,
            is_causal=True if attention_mask is None else False,
            scale=self.scaling
        )
        
        # Reshape and output projection
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, self.q_size)
        output = self.o_proj(attn_output)
        
        return output


class VLLMCompatibleDecoderLayer(nn.Module):
    """Decoder layer matching vLLM's DFlashQwen3DecoderLayer."""
    def __init__(self, hidden_size, num_heads, num_kv_heads, head_dim, intermediate_size):
        super().__init__()
        self.hidden_size = hidden_size
        
        self.self_attn = VLLMCompatibleAttention(
            hidden_size, num_heads, num_kv_heads, head_dim
        )
        self.mlp = VLLMCompatibleSwiGLU(hidden_size, intermediate_size)
        
        self.input_layernorm = VLLMCompatibleRMSNorm(hidden_size, eps=RMS_NORM_EPS)
        self.post_attention_layernorm = VLLMCompatibleRMSNorm(hidden_size, eps=RMS_NORM_EPS)

    def forward(self, hidden_states, attention_mask=None):
        # Self-attention with residual
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)
        hidden_states = self.self_attn(hidden_states, attention_mask)
        hidden_states = residual + hidden_states
        
        # MLP with residual
        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        hidden_states = residual + hidden_states
        
        return hidden_states


class VLLMCompatibleDFlashModel(nn.Module):
    """Draft model matching vLLM's DFlashQwen3Model architecture.
    
    Key features:
    - Fused QKV projections
    - SwiGLU MLP
    - GQA attention
    - Correct key names for vLLM weight loading
    """
    def __init__(
        self,
        vocab_size=VOCAB_SIZE,
        hidden_size=HIDDEN_SIZE,
        num_layers=NUM_HIDDEN_LAYERS,
        num_heads=NUM_ATTENTION_HEADS,
        num_kv_heads=NUM_KEY_VALUE_HEADS,
        head_dim=HEAD_DIM,
        intermediate_size=INTERMEDIATE_SIZE,
        num_aux_layers=NUM_AUX_LAYERS,
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_aux_layers = num_aux_layers
        self.use_aux_hidden_state = num_aux_layers > 0
        
        # Token embeddings
        self.embed_tokens = nn.Embedding(vocab_size, hidden_size)
        
        # Decoder layers
        self.layers = nn.ModuleList([
            VLLMCompatibleDecoderLayer(
                hidden_size, num_heads, num_kv_heads, head_dim, intermediate_size
            )
            for _ in range(num_layers)
        ])
        
        # Final norm
        self.norm = VLLMCompatibleRMSNorm(hidden_size, eps=RMS_NORM_EPS)
        
        # FC for combining aux hidden states (if using aux features)
        if self.use_aux_hidden_state:
            fc_input_size = hidden_size * num_aux_layers
            self.fc = nn.Linear(fc_input_size, hidden_size, bias=False)
            self.hidden_norm = VLLMCompatibleRMSNorm(hidden_size, eps=RMS_NORM_EPS)
        
        # LM head (shared with embed_tokens, matching vLLM)
        self.lm_head = nn.Linear(hidden_size, vocab_size, bias=False)

    def forward(self, input_ids, aux_hidden_states=None, attention_mask=None):
        # Embed tokens
        hidden_states = self.embed_tokens(input_ids)
        
        # Pass through decoder layers
        for layer in self.layers:
            hidden_states = layer(hidden_states, attention_mask)
        
        # Final norm
        hidden_states = self.norm(hidden_states)
        
        # Combine with aux hidden states if provided
        if self.use_aux_hidden_state and aux_hidden_states is not None:
            # aux_hidden_states: [batch, seq, num_aux_layers, hidden_size]
            batch_size, seq_len, num_aux, hidden_size = aux_hidden_states.shape
            assert num_aux == self.num_aux_layers
            assert hidden_size == self.hidden_size
            
            # Flatten aux dimensions: [batch, seq, num_aux * hidden_size]
            aux_flat = aux_hidden_states.view(batch_size, seq_len, -1)
            
            # Project through FC
            combined = self.fc(aux_flat)
            combined = self.hidden_norm(combined)
            
            # Add to hidden states
            hidden_states = hidden_states + combined
        
        # LM head
        logits = self.lm_head(hidden_states)
        
        return logits

    def get_weight_shapes(self):
        """Return expected weight shapes for verification."""
        shapes = {}
        shapes['embed_tokens.weight'] = (self.vocab_size, self.hidden_size)
        shapes['lm_head.weight'] = (self.vocab_size, self.hidden_size)
        shapes['norm.weight'] = (self.hidden_size,)
        
        for i in range(self.num_layers):
            prefix = f'layers.{i}'
            shapes[f'{prefix}.self_attn.qkv_proj.weight'] = (
                NUM_ATTENTION_HEADS * HEAD_DIM + 2 * NUM_KEY_VALUE_HEADS * HEAD_DIM,
                self.hidden_size
            )  # [6400, 5120]
            shapes[f'{prefix}.self_attn.o_proj.weight'] = (
                self.hidden_size, NUM_ATTENTION_HEADS * HEAD_DIM
            )  # [5120, 5120]
            shapes[f'{prefix}.self_attn.q_norm.weight'] = (HEAD_DIM,)  # [160]
            shapes[f'{prefix}.self_attn.k_norm.weight'] = (HEAD_DIM,)  # [160]
            shapes[f'{prefix}.mlp.gate_up_proj.weight'] = (
                2 * INTERMEDIATE_SIZE, self.hidden_size
            )  # [27648, 5120]
            shapes[f'{prefix}.mlp.down_proj.weight'] = (
                self.hidden_size, INTERMEDIATE_SIZE
            )  # [5120, 13824]
            shapes[f'{prefix}.input_layernorm.weight'] = (self.hidden_size,)  # [5120]
            shapes[f'{prefix}.post_attention_layernorm.weight'] = (self.hidden_size,)  # [5120]
        
        if self.use_aux_hidden_state:
            shapes['fc.weight'] = (self.hidden_size, self.hidden_size * self.num_aux_layers)
            shapes['hidden_norm.weight'] = (self.hidden_size,)
        
        return shapes


# ============================================================
# DATASET
# ============================================================

class HiddenStatesDataset(Dataset):
    """Dataset for pre-generated hidden states."""
    def __init__(self, hidden_states_dir, max_samples=None):
        self.hidden_states_dir = Path(hidden_states_dir)
        self.files = sorted(self.hidden_states_dir.glob("*.pt"))
        
        if max_samples:
            self.files = self.files[:max_samples]
        
        print(f"Found {len(self.files)} hidden state files")
    
    def __len__(self):
        return len(self.files)
    
    def __getitem__(self, idx):
        data = torch.load(self.files[idx], map_location='cpu')
        
        # Extract components
        input_ids = data['input_ids']  # [seq_len]
        target_logits = data['target_logits']  # [seq_len, vocab_size]
        
        # Aux hidden states from specific layers
        if 'hidden_states' in data:
            hidden_states = data['hidden_states']  # [num_layers, seq_len, hidden_size]
            # Select aux layers
            aux_hidden = hidden_states[AUX_LAYER_IDS]  # [num_aux, seq_len, hidden_size]
            aux_hidden = aux_hidden.permute(1, 0, 2)  # [seq_len, num_aux, hidden_size]
        else:
            # Fallback: create dummy aux hidden states
            seq_len = input_ids.shape[0]
            aux_hidden = torch.zeros(seq_len, NUM_AUX_LAYERS, HIDDEN_SIZE)
        
        return {
            'input_ids': input_ids,
            'target_logits': target_logits,
            'aux_hidden_states': aux_hidden,
        }


def collate_fn(batch):
    """Collate function for DataLoader."""
    # Find max sequence length in batch
    max_len = max(item['input_ids'].shape[0] for item in batch)
    
    batch_size = len(batch)
    
    # Pad sequences
    input_ids = torch.full((batch_size, max_len), 0, dtype=torch.long)
    target_logits = torch.zeros(batch_size, max_len, VOCAB_SIZE)
    aux_hidden = torch.zeros(batch_size, max_len, NUM_AUX_LAYERS, HIDDEN_SIZE)
    attention_mask = torch.zeros(batch_size, max_len, dtype=torch.bool)
    
    for i, item in enumerate(batch):
        seq_len = item['input_ids'].shape[0]
        input_ids[i, :seq_len] = item['input_ids']
        target_logits[i, :seq_len] = item['target_logits']
        aux_hidden[i, :seq_len] = item['aux_hidden_states']
        attention_mask[i, :seq_len] = True
    
    return {
        'input_ids': input_ids,
        'target_logits': target_logits,
        'aux_hidden_states': aux_hidden,
        'attention_mask': attention_mask,
    }


# ============================================================
# TRAINING
# ============================================================

class MuonOptimizer(torch.optim.Optimizer):
    """Muon optimizer for 2D matrices (from DeepSeek V4)."""
    def __init__(self, params, lr=0.02, weight_decay=0.01, momentum=0.95,
                 nesterov=True, ns_steps=5, adamw_betas=(0.95, 0.98), adamw_eps=1e-8):
        defaults = dict(lr=lr, weight_decay=weight_decay, momentum=momentum,
                       nesterov=nesterov, ns_steps=ns_steps,
                       adamw_betas=adamw_betas, adamw_eps=adamw_eps)
        super().__init__(params, defaults)

    @torch.no_grad()
    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()
        
        for group in self.param_groups:
            lr = group["lr"]
            wd = group["weight_decay"]
            momentum = group["momentum"]
            nesterov = group["nesterov"]
            ns_steps = group["ns_steps"]
            
            for p in group["params"]:
                if p.grad is None:
                    continue
                
                g = p.grad
                state = self.state[p]
                
                # Weight decay
                if wd != 0:
                    p.data.mul_(1 - lr * wd)
                
                # Muon for 2D+ matrices
                if p.ndim >= 2 and p.numel() >= 2:
                    if len(state) == 0:
                        state["momentum_buffer"] = torch.zeros_like(g)
                    
                    buf = state["momentum_buffer"]
                    buf.lerp_(g, 1 - momentum)
                    
                    update = g.lerp_(buf, momentum) if nesterov else buf
                    
                    # Newton-Schulz orthogonalization
                    if update.ndim == 4:
                        update = update.view(len(update), -1)
                    
                    update = self._zeropower_via_newtonschulz5(update, steps=ns_steps)
                    update *= max(1, update.size(-2) / update.size(-1)) ** 0.5
                    
                    if update.ndim != p.ndim:
                        update = update.view(p.shape)
                    
                    p.data.add_(update, alpha=-lr)
                else:
                    # AdamW for 1D params (biases, norms)
                    if len(state) == 0:
                        state["step"] = 0
                        state["exp_avg"] = torch.zeros_like(g)
                        state["exp_avg_sq"] = torch.zeros_like(g)
                    
                    state["step"] += 1
                    exp_avg = state["exp_avg"]
                    exp_avg_sq = state["exp_avg_sq"]
                    beta1, beta2 = group["adamw_betas"]
                    eps = group["adamw_eps"]
                    
                    exp_avg.lerp_(g, 1 - beta1)
                    exp_avg_sq.lerp_(g.square(), 1 - beta2)
                    
                    bias_correction1 = 1 - beta1 ** state["step"]
                    bias_correction2 = 1 - beta2 ** state["step"]
                    
                    step_size = lr / bias_correction1
                    denom = (exp_avg_sq.sqrt() / math.sqrt(bias_correction2)).add_(eps)
                    
                    p.data.addcdiv_(exp_avg, denom, value=-step_size)
        
        return loss
    
    @staticmethod
    def _zeropower_via_newtonschulz5(G, steps=5):
        """Newton-Schulz iteration for matrix orthogonalization."""
        assert G.ndim >= 2
        a, b, c = (3.4445, -4.7750, 2.0315)
        
        X = G.bfloat16() if G.dtype == torch.float32 else G
        
        if G.size(-2) > G.size(-1):
            X = X.mT
        
        X = X / (X.norm(dim=(-2, -1), keepdim=True) + 1e-7)
        
        for _ in range(steps):
            A = X @ X.mT
            B = b * A + c * A @ A
            X = a * X + B @ X
        
        if G.size(-2) > G.size(-1):
            X = X.mT
        
        return X.to(G.dtype)


def train(args):
    """Main training loop."""
    # Setup
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Setup logging
    log_file = os.path.join(args.output_dir, 'training.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Log config
    logger.info("=" * 70)
    logger.info("VLLM-COMPATIBLE DFLASH DRAFT MODEL TRAINING")
    logger.info("=" * 70)
    logger.info(f"Hidden size: {HIDDEN_SIZE}")
    logger.info(f"Num heads: {NUM_ATTENTION_HEADS}, Num KV heads: {NUM_KEY_VALUE_HEADS}")
    logger.info(f"Head dim: {HEAD_DIM}")
    logger.info(f"Intermediate size: {INTERMEDIATE_SIZE}")
    logger.info(f"Vocab size: {VOCAB_SIZE}")
    logger.info(f"Num layers: {NUM_HIDDEN_LAYERS}")
    logger.info(f"Aux layers: {AUX_LAYER_IDS}")
    logger.info(f"Learning rate: {args.lr}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Gradient accumulation: {args.grad_accum}")
    logger.info(f"Effective batch size: {args.batch_size * args.grad_accum}")
    logger.info(f"Max steps: {args.max_steps}")
    logger.info(f"Output dir: {args.output_dir}")
    
    # Create model
    logger.info("Creating model...")
    model = VLLMCompatibleDFlashModel(
        vocab_size=VOCAB_SIZE,
        hidden_size=HIDDEN_SIZE,
        num_layers=NUM_HIDDEN_LAYERS,
        num_heads=NUM_ATTENTION_HEADS,
        num_kv_heads=NUM_KEY_VALUE_HEADS,
        head_dim=HEAD_DIM,
        intermediate_size=INTERMEDIATE_SIZE,
        num_aux_layers=NUM_AUX_LAYERS,
    )
    
    # Verify weight shapes match vLLM expectations
    weight_shapes = model.get_weight_shapes()
    logger.info("\nExpected weight shapes (vLLM compatible):")
    for name, shape in list(weight_shapes.items())[:10]:
        logger.info(f"  {name}: {shape}")
    logger.info(f"  ... and {len(weight_shapes) - 10} more")
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"\nTotal parameters: {total_params:,}")
    logger.info(f"Trainable parameters: {trainable_params:,}")
    
    # Move to device
    model = model.to(device)
    if args.bf16:
        model = model.to(torch.bfloat16)
        logger.info("Using bfloat16")
    
    # Create dataset
    logger.info(f"\nLoading dataset from {args.hidden_states_dir}...")
    dataset = HiddenStatesDataset(args.hidden_states_dir, max_samples=args.max_steps * args.batch_size)
    dataloader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=2,
        pin_memory=True,
    )
    
    # Setup optimizer
    # Separate parameters: 2D+ matrices get Muon, 1D get AdamW
    muon_params = []
    adamw_params = []
    
    for name, p in model.named_parameters():
        if p.ndim >= 2 and p.numel() >= 2:
            muon_params.append(p)
        else:
            adamw_params.append(p)
    
    optimizer = MuonOptimizer(
        [{'params': muon_params}, {'params': adamw_params}],
        lr=args.lr,
        weight_decay=args.weight_decay,
    )
    
    logger.info(f"Muon params: {sum(p.numel() for p in muon_params):,}")
    logger.info(f"AdamW params: {sum(p.numel() for p in adamw_params):,}")
    
    # Learning rate scheduler
    def lr_lambda(step):
        if step < args.warmup_steps:
            return step / args.warmup_steps
        return 0.5 * (1 + math.cos(math.pi * (step - args.warmup_steps) / (args.max_steps - args.warmup_steps)))
    
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    
    # Training loop
    logger.info("\nStarting training...")
    global_step = 0
    epoch = 0
    total_loss = 0
    
    model.train()
    
    progress_bar = tqdm(total=args.max_steps, desc="Training")
    
    while global_step < args.max_steps:
        for batch_idx, batch in enumerate(dataloader):
            if global_step >= args.max_steps:
                break
            
            # Move batch to device
            input_ids = batch['input_ids'].to(device)
            target_logits = batch['target_logits'].to(device)
            aux_hidden = batch['aux_hidden_states'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            
            if args.bf16:
                target_logits = target_logits.to(torch.bfloat16)
                aux_hidden = aux_hidden.to(torch.bfloat16)
            
            # Forward pass
            logits = model(input_ids, aux_hidden_states=aux_hidden, attention_mask=attention_mask)
            
            # Compute loss: KL divergence between draft and target logits
            # Temperature-scaled softmax
            draft_probs = F.log_softmax(logits / args.temperature, dim=-1)
            target_probs = F.softmax(target_logits / args.temperature, dim=-1)
            
            # KL divergence
            loss = F.kl_div(
                draft_probs.view(-1, VOCAB_SIZE),
                target_probs.view(-1, VOCAB_SIZE),
                reduction='batchmean'
            )
            
            # Scale for gradient accumulation
            loss = loss / args.grad_accum
            
            # Backward pass
            loss.backward()
            
            total_loss += loss.item() * args.grad_accum
            
            # Gradient accumulation
            if (batch_idx + 1) % args.grad_accum == 0:
                # Clip gradients
                torch.nn.utils.clip_grad_norm_(model.parameters(), args.max_grad_norm)
                
                # Optimizer step
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                
                global_step += 1
                progress_bar.update(1)
                
                # Logging
                if global_step % args.log_interval == 0:
                    avg_loss = total_loss / args.log_interval
                    lr = scheduler.get_last_lr()[0]
                    logger.info(
                        f"Step {global_step}/{args.max_steps} | "
                        f"Loss: {avg_loss:.4f} | "
                        f"LR: {lr:.6f} | "
                        f"Epoch: {epoch}"
                    )
                    total_loss = 0
                
                # Checkpointing
                if global_step % args.save_interval == 0:
                    checkpoint_path = os.path.join(args.output_dir, f'checkpoint-{global_step}.pt')
                    torch.save({
                        'step': global_step,
                        'epoch': epoch,
                        'model_state_dict': model.state_dict(),
                        'optimizer_state_dict': optimizer.state_dict(),
                        'scheduler_state_dict': scheduler.state_dict(),
                        'config': {
                            'hidden_size': HIDDEN_SIZE,
                            'num_attention_heads': NUM_ATTENTION_HEADS,
                            'num_key_value_heads': NUM_KEY_VALUE_HEADS,
                            'head_dim': HEAD_DIM,
                            'intermediate_size': INTERMEDIATE_SIZE,
                            'vocab_size': VOCAB_SIZE,
                            'num_hidden_layers': NUM_HIDDEN_LAYERS,
                            'aux_layer_ids': AUX_LAYER_IDS,
                        }
                    }, checkpoint_path)
                    logger.info(f"Saved checkpoint: {checkpoint_path}")
        
        epoch += 1
    
    progress_bar.close()
    
    # Save final model
    final_path = os.path.join(args.output_dir, 'final_model.pt')
    torch.save({
        'step': global_step,
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'config': {
            'hidden_size': HIDDEN_SIZE,
            'num_attention_heads': NUM_ATTENTION_HEADS,
            'num_key_value_heads': NUM_KEY_VALUE_HEADS,
            'head_dim': HEAD_DIM,
            'intermediate_size': INTERMEDIATE_SIZE,
            'vocab_size': VOCAB_SIZE,
            'num_hidden_layers': NUM_HIDDEN_LAYERS,
            'aux_layer_ids': AUX_LAYER_IDS,
        }
    }, final_path)
    logger.info(f"Saved final model: {final_path}")
    
    # Save config.json for vLLM
    config_json = {
        "architectures": ["DFlashQwen3ForCausalLM"],
        "hidden_size": HIDDEN_SIZE,
        "num_attention_heads": NUM_ATTENTION_HEADS,
        "num_key_value_heads": NUM_KEY_VALUE_HEADS,
        "head_dim": HEAD_DIM,
        "intermediate_size": INTERMEDIATE_SIZE,
        "vocab_size": VOCAB_SIZE,
        "num_hidden_layers": NUM_HIDDEN_LAYERS,
        "rms_norm_eps": RMS_NORM_EPS,
        "max_position_embeddings": MAX_POSITION_EMBEDDINGS,
        "aux_layer_ids": AUX_LAYER_IDS,
        "model_type": "qwen3",
        "torch_dtype": "bfloat16" if args.bf16 else "float32",
    }
    
    config_path = os.path.join(args.output_dir, 'config.json')
    with open(config_path, 'w') as f:
        json.dump(config_json, f, indent=2)
    logger.info(f"Saved config: {config_path}")
    
    logger.info("\n" + "=" * 70)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Model saved to: {args.output_dir}")
    logger.info("To use with vLLM, convert checkpoints to safetensors and load with:")
    logger.info("  --speculative-config '{\"method\":\"dflash\",\"model\":\"<path>\"}'")


def main():
    parser = argparse.ArgumentParser(description='Train vLLM-compatible DFlash draft model')
    
    # Model config
    parser.add_argument('--hidden-size', type=int, default=HIDDEN_SIZE)
    parser.add_argument('--num-layers', type=int, default=NUM_HIDDEN_LAYERS)
    parser.add_argument('--num-heads', type=int, default=NUM_ATTENTION_HEADS)
    parser.add_argument('--num-kv-heads', type=int, default=NUM_KEY_VALUE_HEADS)
    parser.add_argument('--intermediate-size', type=int, default=INTERMEDIATE_SIZE)
    
    # Training config
    parser.add_argument('--lr', type=float, default=DEFAULT_LR)
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument('--grad-accum', type=int, default=DEFAULT_GRAD_ACCUM)
    parser.add_argument('--max-steps', type=int, default=DEFAULT_STEPS)
    parser.add_argument('--warmup-steps', type=int, default=DEFAULT_WARMUP_STEPS)
    parser.add_argument('--weight-decay', type=float, default=0.01)
    parser.add_argument('--max-grad-norm', type=float, default=1.0)
    parser.add_argument('--temperature', type=float, default=1.0)
    parser.add_argument('--bf16', action='store_true', default=True)
    
    # Data config
    parser.add_argument('--hidden-states-dir', type=str, default=DEFAULT_HIDDEN_STATES_DIR)
    parser.add_argument('--max-length', type=int, default=DEFAULT_MAX_LENGTH)
    
    # Output config
    parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument('--save-interval', type=int, default=500)
    parser.add_argument('--log-interval', type=int, default=10)
    
    # Other
    parser.add_argument('--seed', type=int, default=42)
    
    args = parser.parse_args()
    
    # Set seed
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    
    train(args)


if __name__ == '__main__':
    main()
