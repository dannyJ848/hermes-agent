#!/usr/bin/env python3
"""
Franken V8 Modular Training — Partitioned by Graft Groups
===========================================================

Partitions:
  - core: embeddings, decoder layers, norm, lm_head, aux FC (always loaded)
  - graft_mtp4: MTP-4 multi-token prediction
  - graft_pard: PARD parallel decoder
  - graft_tree: Tree Attention + Early Exit
  - graft_spec: SSD + DART + LTD speculative decoding group

Each partition trains independently, checkpoints saved separately.
Final assembly merges all partitions into one state dict.

Usage:
  python3 train_franken_v8_modular.py --partition core --batch-id 2 ...
  python3 train_franken_v8_modular.py --partition graft_mtp4 --batch-id 2 ...
  python3 train_franken_v8_modular.py --assemble --output final.pt
"""

import os
import sys
import json
import time
import random
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, List

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# =============================================================================
# CONSTANTS (match vllm_compatible.py)
# =============================================================================
VOCAB_SIZE = 248320
HIDDEN_SIZE = 5120
NUM_HIDDEN_LAYERS = 8
NUM_ATTENTION_HEADS = 32
NUM_KEY_VALUE_HEADS = 4
HEAD_DIM = 160
INTERMEDIATE_SIZE = 13824
RMS_NORM_EPS = 1e-6
NUM_AUX_LAYERS = 5
AUX_LAYER_IDS = [1, 19, 36]

# =============================================================================
# CORE MODULES (copied from vllm_compatible.py)
# =============================================================================

class AdaptiveRMSNorm(nn.Module):
    def __init__(self, hidden_size, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.eps = eps
        self.scale = nn.Parameter(torch.ones(1))
        self.shift = nn.Parameter(torch.zeros(1))
    def forward(self, hidden_states):
        variance = hidden_states.pow(2).mean(-1, keepdim=True)
        hidden_states = hidden_states * torch.rsqrt(variance + self.eps)
        return hidden_states * (self.weight * self.scale + self.shift)

class SwiGLUMLP(nn.Module):
    def __init__(self, hidden_size, intermediate_size, dropout=0.1):
        super().__init__()
        self.gate_up_proj = nn.Linear(hidden_size, 2 * intermediate_size, bias=False)
        self.down_proj = nn.Linear(intermediate_size, hidden_size, bias=False)
        self.dropout = nn.Dropout(dropout)
    def forward(self, x):
        gate_up = self.gate_up_proj(x)
        gate, up = gate_up.chunk(2, dim=-1)
        return self.down_proj(self.dropout(nn.functional.silu(gate) * up))

class GatedAttention(nn.Module):
    def __init__(self, hidden_size, num_heads, num_kv_heads, head_dim, dropout=0.1):
        super().__init__()
        self.num_heads = num_heads
        self.num_kv_heads = num_kv_heads
        self.head_dim = head_dim
        q_size = num_heads * head_dim
        kv_size = num_kv_heads * head_dim
        self.qkv_proj = nn.Linear(hidden_size, q_size + 2 * kv_size, bias=False)
        self.o_proj = nn.Linear(q_size, hidden_size, bias=False)
        self.q_norm = AdaptiveRMSNorm(head_dim, eps=1e-6)
        self.k_norm = AdaptiveRMSNorm(head_dim, eps=1e-6)
        self.gate = nn.Parameter(torch.zeros(1))
        self.dropout = nn.Dropout(dropout)
    def forward(self, hidden_states, attention_mask=None):
        bsz, seq_len, _ = hidden_states.shape
        qkv = self.qkv_proj(hidden_states)
        q_size = self.num_heads * self.head_dim
        kv_size = self.num_kv_heads * self.head_dim
        q, k, v = qkv.split([q_size, kv_size, kv_size], dim=-1)
        q = q.view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(bsz, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        v = v.view(bsz, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        # q_norm and k_norm expect [batch, heads, seq_len, head_dim]
        # They operate on the last dim (head_dim) via mean(-1, keepdim=True)
        q = self.q_norm(q)
        k = self.k_norm(k)
        # Simplified attention — repeat KV heads to match Q heads for GQA
        if self.num_heads != self.num_kv_heads:
            # Repeat k,v heads: [batch, kv_heads, seq, head_dim] -> [batch, num_heads, seq, head_dim]
            k = k.repeat_interleave(self.num_heads // self.num_kv_heads, dim=1)
            v = v.repeat_interleave(self.num_heads // self.num_kv_heads, dim=1)
        scores = torch.matmul(q, k.transpose(-2, -1)) / (self.head_dim ** 0.5)
        if attention_mask is not None:
            scores = scores + attention_mask
        attn = torch.softmax(scores, dim=-1)
        attn = self.dropout(attn)
        out = torch.matmul(attn, v)
        out = out.transpose(1, 2).contiguous().view(bsz, seq_len, q_size)
        return hidden_states * torch.sigmoid(self.gate) + self.o_proj(out)

class FrankenV8DecoderLayer(nn.Module):
    def __init__(self, layer_idx, hidden_size, num_heads, num_kv_heads, head_dim, intermediate_size, dropout=0.1):
        super().__init__()
        self.self_attn = GatedAttention(hidden_size, num_heads, num_kv_heads, head_dim, dropout)
        self.mlp = SwiGLUMLP(hidden_size, intermediate_size, dropout)
        self.input_layernorm = AdaptiveRMSNorm(hidden_size, eps=1e-6)
        self.post_attention_layernorm = AdaptiveRMSNorm(hidden_size, eps=1e-6)
        # Highway connection (Graft 8)
        self.highway_alpha = nn.Parameter(torch.tensor(0.5))
        self.highway_beta = nn.Parameter(torch.tensor(0.5))
    def forward(self, hidden_states, attention_mask=None):
        # Pre-norm with highway
        normed = self.input_layernorm(hidden_states)
        attn_out = self.self_attn(normed, attention_mask)
        hidden_states = self.highway_alpha * hidden_states + self.highway_beta * attn_out
        # MLP with highway
        normed2 = self.post_attention_layernorm(hidden_states)
        mlp_out = self.mlp(normed2)
        hidden_states = self.highway_alpha * hidden_states + self.highway_beta * mlp_out
        return hidden_states

# =============================================================================
# CORE MODEL (always loaded)
# =============================================================================

class FrankenV8Core(nn.Module):
    """Core Franken V8 — embeddings, layers, norm, lm_head, aux FC."""
    def __init__(self, vocab_size=VOCAB_SIZE, hidden_size=HIDDEN_SIZE, num_layers=NUM_HIDDEN_LAYERS,
                 num_heads=NUM_ATTENTION_HEADS, num_kv_heads=NUM_KEY_VALUE_HEADS, head_dim=HEAD_DIM,
                 intermediate_size=INTERMEDIATE_SIZE, num_aux_layers=NUM_AUX_LAYERS, dropout=0.1):
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_aux_layers = num_aux_layers
        self.use_aux = num_aux_layers > 0
        self.embed_tokens = nn.Embedding(vocab_size, hidden_size)
        self.layers = nn.ModuleList([
            FrankenV8DecoderLayer(i, hidden_size, num_heads, num_kv_heads, head_dim, intermediate_size, dropout)
            for i in range(num_layers)
        ])
        self.norm = AdaptiveRMSNorm(hidden_size, eps=RMS_NORM_EPS)
        if self.use_aux:
            self.fc = nn.Linear(hidden_size * num_aux_layers, hidden_size, bias=False)
            self.hidden_norm = AdaptiveRMSNorm(hidden_size, eps=RMS_NORM_EPS)
        self.lm_head = nn.Linear(hidden_size, vocab_size, bias=False)
        self._init_weights()
    def _init_weights(self):
        for name, p in self.named_parameters():
            if 'embed' in name or 'lm_head' in name:
                nn.init.normal_(p, mean=0, std=0.02)
            elif 'qkv_proj' in name or 'o_proj' in name:
                nn.init.xavier_uniform_(p)
            elif 'gate_up_proj' in name or 'down_proj' in name:
                nn.init.xavier_uniform_(p)
            elif 'norm' in name and 'weight' in name:
                nn.init.ones_(p)
            elif 'fc' in name:
                nn.init.xavier_uniform_(p, gain=0.1)
    def forward(self, input_ids, aux_hidden_states=None, attention_mask=None, return_hidden=False):
        hidden_states = self.embed_tokens(input_ids)
        for layer in self.layers:
            hidden_states = layer(hidden_states, attention_mask)
        hidden_states = self.norm(hidden_states)
        if self.use_aux and aux_hidden_states is not None:
            # aux_hidden_states: [batch, num_aux_layers, seq_len, hidden_size]
            bsz, num_aux, seq_len, hid = aux_hidden_states.shape
            aux_flat = aux_hidden_states.permute(0, 2, 1, 3).contiguous().view(bsz, seq_len, -1)
            # Match dtype to model
            aux_flat = aux_flat.to(hidden_states.dtype)
            combined = self.fc(aux_flat)
            combined = self.hidden_norm(combined)
            hidden_states = hidden_states + combined
        logits = self.lm_head(hidden_states)
        if return_hidden:
            return {'logits': logits, 'hidden_states': hidden_states}
        return {'logits': logits}
    def get_weight_shapes(self):
        shapes = {}
        shapes['embed_tokens.weight'] = (self.vocab_size, self.hidden_size)
        shapes['lm_head.weight'] = (self.vocab_size, self.hidden_size)
        shapes['norm.weight'] = (self.hidden_size,)
        for i in range(self.num_layers):
            prefix = f'layers.{i}'
            shapes[f'{prefix}.self_attn.qkv_proj.weight'] = (NUM_ATTENTION_HEADS * HEAD_DIM + 2 * NUM_KEY_VALUE_HEADS * HEAD_DIM, self.hidden_size)
            shapes[f'{prefix}.self_attn.o_proj.weight'] = (self.hidden_size, NUM_ATTENTION_HEADS * HEAD_DIM)
            shapes[f'{prefix}.self_attn.q_norm.weight'] = (HEAD_DIM,)
            shapes[f'{prefix}.self_attn.k_norm.weight'] = (HEAD_DIM,)
            shapes[f'{prefix}.mlp.gate_up_proj.weight'] = (2 * INTERMEDIATE_SIZE, self.hidden_size)
            shapes[f'{prefix}.mlp.down_proj.weight'] = (self.hidden_size, INTERMEDIATE_SIZE)
            shapes[f'{prefix}.input_layernorm.weight'] = (self.hidden_size,)
            shapes[f'{prefix}.post_attention_layernorm.weight'] = (self.hidden_size,)
        if self.use_aux:
            shapes['fc.weight'] = (self.hidden_size, self.hidden_size * self.num_aux_layers)
            shapes['hidden_norm.weight'] = (self.hidden_size,)
        return shapes

# =============================================================================
# GRAFT MODULES (loaded one at a time)
# =============================================================================

class MTP4Module(nn.Module):
    """Graft 6: Multi-Token Prediction (4 tokens ahead)."""
    def __init__(self, hidden_size, vocab_size, num_tokens=4, dropout=0.1):
        super().__init__()
        self.num_tokens = num_tokens
        self.predictors = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size, bias=True),
                nn.SiLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size, vocab_size, bias=True)
            ) for _ in range(num_tokens)
        ])
    def forward(self, hidden_states):
        return [pred(hidden_states) for pred in self.predictors]

class PARDModule(nn.Module):
    """Graft 15: Parallel Decoding heads."""
    def __init__(self, hidden_size, vocab_size, num_parallel=4, dropout=0.1):
        super().__init__()
        self.heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2, bias=True),
                nn.SiLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size // 2, vocab_size, bias=True)
            ) for _ in range(num_parallel)
        ])
    def forward(self, hidden_states):
        return [head(hidden_states) for head in self.heads]

class TreeAttnModule(nn.Module):
    """Graft 16: Tree Attention Pattern."""
    def __init__(self, num_heads, head_dim):
        super().__init__()
        self.pattern_proj = nn.Linear(head_dim, head_dim, bias=False)
    def forward(self, q, k, v):
        q = self.pattern_proj(q)
        scores = torch.matmul(q, k.transpose(-2, -1)) / (q.shape[-1] ** 0.5)
        attn = torch.softmax(scores, dim=-1)
        return torch.matmul(attn, v)

class EarlyExitModule(nn.Module):
    """Graft 17: Early Exit Controller."""
    def __init__(self, hidden_size, num_layers, dropout=0.1):
        super().__init__()
        self.gates = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 4, bias=True),
                nn.SiLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size // 4, 1, bias=True),
                nn.Sigmoid()
            ) for _ in range(num_layers)
        ])
    def forward(self, hidden_states, layer_idx):
        return self.gates[layer_idx](hidden_states)

class SSDModule(nn.Module):
    """Graft 19: Speculative Speculative Decoding."""
    def __init__(self, hidden_size, vocab_size, dropout=0.1):
        super().__init__()
        self.draft_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2, bias=True),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, vocab_size, bias=True)
        )
    def forward(self, hidden_states):
        return self.draft_head(hidden_states)

class DARTModule(nn.Module):
    """Graft 20: Diffusion-Inspired Drafting."""
    def __init__(self, hidden_size, vocab_size, num_steps=4, dropout=0.1):
        super().__init__()
        self.num_steps = num_steps
        self.noise_scale = nn.Parameter(torch.linspace(0.1, 0.5, num_steps))
        self.denoiser = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size + vocab_size, hidden_size, bias=True),
                nn.SiLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size, vocab_size, bias=True)
            ) for _ in range(num_steps)
        ])
    def forward(self, hidden_states, logits):
        results = []
        for i, denoise in enumerate(self.denoiser):
            noise = torch.randn_like(logits) * self.noise_scale[i]
            combined = torch.cat([hidden_states, logits + noise], dim=-1)
            results.append(denoise(combined))
        return results

class LTDModule(nn.Module):
    """Graft 21: Learning to Draft policy."""
    def __init__(self, hidden_size):
        super().__init__()
        self.policy = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2, bias=True),
            nn.SiLU(),
            nn.Linear(hidden_size // 2, 3, bias=True)  # 3 actions: spec, verify, fallback
        )
        self.value = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2, bias=True),
            nn.SiLU(),
            nn.Linear(hidden_size // 2, 1, bias=True)
        )
    def forward(self, hidden_states):
        return self.policy(hidden_states), self.value(hidden_states)

# =============================================================================
# DATASET
# =============================================================================

class HiddenStatesDataset(Dataset):
    def __init__(self, hidden_states_dir, max_samples=None):
        self.hidden_states_dir = Path(hidden_states_dir)
        self.files = sorted(self.hidden_states_dir.glob("*.pt"))
        if max_samples:
            self.files = self.files[:max_samples]
        if not self.files:
            raise ValueError(f"No .pt files found in {hidden_states_dir}")
    def __len__(self):
        return len(self.files)
    def __getitem__(self, idx):
        data = torch.load(self.files[idx], map_location='cpu')
        return {
            'input_ids': data['input_ids'].long(),
            'target_logits': data['target_logits'],
            'aux_hidden_states': data.get('hidden_states', None),
        }

def collate_fn(batch):
    # Pad to max length in batch
    max_len = max(b['input_ids'].shape[0] for b in batch)
    vocab_size = batch[0]['target_logits'].shape[-1]
    
    input_ids = torch.full((len(batch), max_len), 0, dtype=torch.long)
    target_logits = torch.full((len(batch), max_len, vocab_size), 0.0, dtype=torch.float32)
    aux = None
    
    if batch[0]['aux_hidden_states'] is not None:
        aux_shape = batch[0]['aux_hidden_states'].shape
        # aux_hidden_states shape: [num_aux_layers, seq_len, hidden_size]
        num_aux = aux_shape[0]
        hidden_size = aux_shape[2]
        aux = torch.full((len(batch), num_aux, max_len, hidden_size), 0.0, dtype=torch.float32)
    
    for i, b in enumerate(batch):
        seq_len = b['input_ids'].shape[0]
        input_ids[i, :seq_len] = b['input_ids']
        target_logits[i, :seq_len] = b['target_logits']
        if aux is not None:
            aux[i, :, :seq_len] = b['aux_hidden_states']
    
    return {
        'input_ids': input_ids,
        'target_logits': target_logits,
        'aux_hidden_states': aux,
    }

# =============================================================================
# TRAINING LOGIC
# =============================================================================

def train_partition(args):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger = lambda msg: print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    
    # Create output dirs
    partition_dir = Path(args.output_dir) / f"batch_{args.batch_id}" / args.partition
    partition_dir.mkdir(parents=True, exist_ok=True)
    
    logger(f"=== Training partition: {args.partition} | Batch: {args.batch_id} ===")
    logger(f"Output: {partition_dir}")
    
    # Load or create core
    core_path = Path(args.output_dir) / f"batch_{args.batch_id}" / "core" / "latest.pt"
    if core_path.exists() and not args.from_scratch:
        logger(f"Loading core from {core_path}")
        core = FrankenV8Core().to(device)
        ckpt = torch.load(core_path, map_location=device)
        core.load_state_dict(ckpt['model_state_dict'])
    else:
        logger("Creating fresh core")
        core = FrankenV8Core().to(device)
    
    if args.bf16:
        core = core.to(torch.bfloat16)
    
    # Load graft module if not core-only
    graft_module = None
    if args.partition != 'core':
        if args.partition == 'graft_mtp4':
            graft_module = MTP4Module(HIDDEN_SIZE, VOCAB_SIZE).to(device)
        elif args.partition == 'graft_pard':
            graft_module = PARDModule(HIDDEN_SIZE, VOCAB_SIZE).to(device)
        elif args.partition == 'graft_tree':
            graft_module = nn.ModuleDict({
                'tree_attn': TreeAttnModule(NUM_ATTENTION_HEADS, HEAD_DIM).to(device),
                'early_exit': EarlyExitModule(HIDDEN_SIZE, NUM_HIDDEN_LAYERS).to(device),
            })
        elif args.partition == 'graft_spec':
            graft_module = nn.ModuleDict({
                'ssd': SSDModule(HIDDEN_SIZE, VOCAB_SIZE).to(device),
                'dart': DARTModule(HIDDEN_SIZE, VOCAB_SIZE).to(device),
                'ltd': LTDModule(HIDDEN_SIZE).to(device),
            })
        else:
            raise ValueError(f"Unknown partition: {args.partition}")
        
        # Load existing graft checkpoint if available
        graft_ckpt_path = partition_dir / "latest.pt"
        if graft_ckpt_path.exists() and not args.from_scratch:
            logger(f"Loading graft from {graft_ckpt_path}")
            ckpt = torch.load(graft_ckpt_path, map_location=device)
            graft_module.load_state_dict(ckpt['graft_state_dict'])
        
        if args.bf16:
            graft_module = graft_module.to(torch.bfloat16)
    
    # Dataset
    logger(f"Loading dataset from {args.hidden_states_dir}")
    dataset = HiddenStatesDataset(args.hidden_states_dir, max_samples=args.max_steps * args.batch_size)
    dataloader = DataLoader(
        dataset, batch_size=args.batch_size, shuffle=True,
        num_workers=0, pin_memory=True, collate_fn=collate_fn
    )
    
    # Optimizer — only train active parameters
    params_to_train = list(core.parameters())
    if graft_module is not None:
        params_to_train += list(graft_module.parameters())
    
    optimizer = torch.optim.AdamW(params_to_train, lr=args.lr, weight_decay=args.weight_decay)
    
    # Training loop
    global_step = 0
    core.train()
    if graft_module:
        graft_module.train()
    
    for epoch in range(1000):  # effectively infinite, limited by max_steps
        for batch in dataloader:
            if global_step >= args.max_steps:
                break
            
            input_ids = batch['input_ids'].to(device)
            target_logits = batch['target_logits'].to(device)
            aux_hidden = batch['aux_hidden_states'].to(device) if batch['aux_hidden_states'] is not None else None
            
            # Forward
            outputs = core(input_ids, aux_hidden)
            logits = outputs['logits']
            
            # Primary loss (distillation from target)
            loss = nn.functional.kl_div(
                nn.functional.log_softmax(logits, dim=-1),
                nn.functional.softmax(target_logits, dim=-1),
                reduction='batchmean'
            )
            
            # Graft-specific losses
            if args.partition == 'graft_mtp4' and graft_module:
                # Get hidden_states from core output (single forward pass)
                outputs_with_hidden = core(input_ids, aux_hidden, return_hidden=True)
                hidden_states = outputs_with_hidden['hidden_states']
                mtp_preds = graft_module(hidden_states)
                for i, pred in enumerate(mtp_preds):
                    shift = i + 1
                    if shift < input_ids.shape[1]:
                        mtp_target = target_logits[:, shift:]
                        mtp_pred = pred[:, :-shift]
                        loss += 0.1 * nn.functional.kl_div(
                            nn.functional.log_softmax(mtp_pred, dim=-1),
                            nn.functional.softmax(mtp_target, dim=-1),
                            reduction='batchmean'
                        )
            
            elif args.partition == 'graft_pard' and graft_module:
                pard_outputs = graft_module(outputs['logits'])
                for pard_logit in pard_outputs:
                    loss += 0.05 * nn.functional.kl_div(
                        nn.functional.log_softmax(pard_logit, dim=-1),
                        nn.functional.softmax(target_logits, dim=-1),
                        reduction='batchmean'
                    )
            
            elif args.partition == 'graft_spec' and graft_module:
                ssd_logits = graft_module['ssd'](outputs['logits'])
                dart_logits = graft_module['dart'](outputs['logits'], ssd_logits)
                ltd_policy, ltd_value = graft_module['ltd'](outputs['logits'])
                loss += 0.05 * nn.functional.kl_div(
                    nn.functional.log_softmax(ssd_logits, dim=-1),
                    nn.functional.softmax(target_logits, dim=-1),
                    reduction='batchmean'
                )
            
            # Backward
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params_to_train, args.max_grad_norm)
            optimizer.step()
            optimizer.zero_grad()
            
            global_step += 1
            
            if global_step % args.log_interval == 0:
                logger(f"Step {global_step}/{args.max_steps} | Loss: {loss.item():.4f}")
            
            if global_step % args.save_interval == 0:
                save_checkpoint(core, graft_module, optimizer, global_step, epoch, partition_dir)
        
        if global_step >= args.max_steps:
            break
    
    # Final save
    save_checkpoint(core, graft_module, optimizer, global_step, epoch, partition_dir)
    logger(f"=== Partition {args.partition} complete ===")
    
    # Report size
    core_size = sum(p.numel() * p.element_size() for p in core.parameters()) / (1024**3)
    logger(f"Core size: {core_size:.2f} GB")
    if graft_module:
        graft_size = sum(p.numel() * p.element_size() for p in graft_module.parameters()) / (1024**3)
        logger(f"Graft size: {graft_size:.2f} GB")

def save_checkpoint(core, graft_module, optimizer, step, epoch, partition_dir):
    ckpt = {
        'step': step,
        'epoch': epoch,
        'model_state_dict': core.state_dict(),
    }
    if graft_module:
        ckpt['graft_state_dict'] = graft_module.state_dict()
    
    # Only save latest, overwrite previous to save disk space
    latest_path = partition_dir / "latest.pt"
    torch.save(ckpt, latest_path)
    print(f"Saved checkpoint: {latest_path} (step {step})")
    
    # For core partition only, also keep periodic checkpoints
    if partition_dir.name == 'core' and step % 1000 == 0:
        path = partition_dir / f"checkpoint-{step}.pt"
        torch.save(ckpt, path)
        print(f"Saved milestone checkpoint: {path}")

# =============================================================================
# ASSEMBLY
# =============================================================================

def assemble_model(args):
    """Merge all partition checkpoints into one unified state dict."""
    device = torch.device('cpu')  # Load on CPU to avoid OOM
    logger = lambda msg: print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    
    logger("=== Assembling Franken V8 from partitions ===")
    
    # Load core
    core_path = Path(args.output_dir) / f"batch_{args.batch_id}" / "core" / "latest.pt"
    logger(f"Loading core: {core_path}")
    core_ckpt = torch.load(core_path, map_location=device)
    
    # Build unified state dict
    unified = {}
    unified.update(core_ckpt['model_state_dict'])
    
    # Load each graft
    graft_partitions = ['graft_mtp4', 'graft_pard', 'graft_tree', 'graft_spec']
    for graft_name in graft_partitions:
        graft_path = Path(args.output_dir) / f"batch_{args.batch_id}" / graft_name / "latest.pt"
        if graft_path.exists():
            logger(f"Loading {graft_name}: {graft_path}")
            graft_ckpt = torch.load(graft_path, map_location=device)
            graft_state = graft_ckpt.get('graft_state_dict', {})
            # Prefix with graft name
            for key, val in graft_state.items():
                unified[f"{graft_name}.{key}"] = val
        else:
            logger(f"WARNING: {graft_name} not found, skipping")
    
    # Save unified
    output_path = Path(args.output_dir) / f"batch_{args.batch_id}" / "franken_v8_unified.pt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({'model_state_dict': unified, 'batch_id': args.batch_id}, output_path)
    
    size_gb = os.path.getsize(output_path) / (1024**3)
    logger(f"Unified model saved: {output_path}")
    logger(f"Size: {size_gb:.2f} GB")
    
    # Report layer count
    logger(f"Total keys: {len(unified)}")

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--partition', type=str, default='core',
                        choices=['core', 'graft_mtp4', 'graft_pard', 'graft_tree', 'graft_spec'])
    parser.add_argument('--batch-id', type=int, required=True)
    parser.add_argument('--hidden-states-dir', type=str, required=True)
    parser.add_argument('--output-dir', type=str, default='/data/models/FrankenV8-Modular')
    parser.add_argument('--lr', type=float, default=0.0001)
    parser.add_argument('--batch-size', type=int, default=4)
    parser.add_argument('--grad-accum', type=int, default=2)
    parser.add_argument('--max-steps', type=int, default=3000)
    parser.add_argument('--weight-decay', type=float, default=0.01)
    parser.add_argument('--max-grad-norm', type=float, default=1.0)
    parser.add_argument('--bf16', action='store_true', default=True)
    parser.add_argument('--save-interval', type=int, default=500)
    parser.add_argument('--log-interval', type=int, default=10)
    parser.add_argument('--from-scratch', action='store_true', default=False)
    parser.add_argument('--assemble', action='store_true', default=False)
    
    args = parser.parse_args()
    
    if args.assemble:
        assemble_model(args)
    else:
        train_partition(args)

if __name__ == '__main__':
    main()
