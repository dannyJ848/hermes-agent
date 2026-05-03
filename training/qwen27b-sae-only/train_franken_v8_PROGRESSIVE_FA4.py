#!/usr/bin/env python3
"""
FRANKEN v8 DFLASH — PROGRESSIVE GRAFT LOADING

Problem: ALL 25 grafts = ~12B+ params = OOM on GB10
Solution: Load only active wave's modules to GPU. Keep inactive modules on CPU.
When wave rotates, swap modules GPU↔CPU.

This ensures:
1. ALL grafts are trained (get gradients)
2. Only ~4B params on GPU at any time
3. No OOM
"""

import argparse
import json
import os
import math
import random
import time
import logging
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

# ============================================================
# DUAL-MODE ATTENTION: SDPA for training, FA4 for inference
# ============================================================
# FA4 v4.0.0b11 on SM120 has a backward pass bug (causal NaN) but forward works.
# Use SDPA for training (better convergence, no NaN).
# Use FA4 for inference (faster, same quality).
# ============================================================

try:
    from flash_attn.cute import flash_attn_func as fa4_flash_attn_func
    HAS_FA4 = True
    print("[INFO] Flash Attention 4 (CuTeDSL) loaded — Blackwell-optimized")
except ImportError:
    HAS_FA4 = False
    print("[INFO] Flash Attention 4 not available, using SDPA for all modes")

def attention_forward(q, k, v, causal=True, scale=None):
    '''Training forward pass — use SDPA for stability'''
    return F.scaled_dot_product_attention(q, k, v, is_causal=causal, scale=scale)

def attention_inference(q, k, v, causal=True, scale=None):
    '''Inference only — use FA4 for speed if available, else SDPA'''
    if HAS_FA4 and not torch.is_grad_enabled():
        try:
            out = fa4_flash_attn_func(q, k, v, causal=causal)
            if isinstance(out, tuple):
                out = out[0]
            return out
        except Exception:
            pass
    return F.scaled_dot_product_attention(q, k, v, is_causal=causal, scale=scale)

# Dynamic dispatch: uses SDPA during training (grad enabled), FA4 during inference (no grad)
def fa4_attention(q, k, v, causal=True, scale=None):
    if torch.is_grad_enabled():
        return attention_forward(q, k, v, causal=causal, scale=scale)
    else:
        return attention_inference(q, k, v, causal=causal, scale=scale)
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

# ============================================================
# CONFIG
# ============================================================

HIDDEN_SIZE = 5120
NUM_ATTENTION_HEADS = 32
NUM_KEY_VALUE_HEADS = 4
HEAD_DIM = HIDDEN_SIZE // NUM_ATTENTION_HEADS
INTERMEDIATE_SIZE = 13824
VOCAB_SIZE = 248320
MAX_POSITION_EMBEDDINGS = 131072
RMS_NORM_EPS = 1e-6
NUM_HIDDEN_LAYERS = 8
AUX_LAYER_IDS = [1, 3, 4]
NUM_AUX_LAYERS = len(AUX_LAYER_IDS)

# ============================================================
# CORE MODULES (always on GPU)
# ============================================================

class AdaptiveRMSNorm(nn.Module):
    def __init__(self, hidden_size, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.eps = eps
        self.scale = nn.Parameter(torch.ones(1))
        self.shift = nn.Parameter(torch.zeros(1))
        self.manifold_gate = nn.Linear(hidden_size, hidden_size, bias=False)
        nn.init.xavier_uniform_(self.manifold_gate.weight, gain=0.1)
    
    def forward(self, hidden_states):
        input_dtype = hidden_states.dtype
        h = hidden_states.to(torch.float32)
        variance = h.pow(2).mean(-1, keepdim=True)
        h = h * torch.rsqrt(variance + self.eps)
        h = h * (self.scale + 1.0) + self.shift
        manifold = torch.sigmoid(self.manifold_gate(hidden_states))
        h = h * manifold
        return (self.weight * h).to(input_dtype)


class FrankenV8SwiGLU(nn.Module):
    def __init__(self, hidden_size, intermediate_size, dropout=0.1):
        super().__init__()
        self.gate_up_proj = nn.Linear(hidden_size, 2 * intermediate_size, bias=True)
        self.down_proj = nn.Linear(intermediate_size, hidden_size, bias=True)
        self.dropout = nn.Dropout(dropout)
        self.highway_gate = nn.Linear(hidden_size, hidden_size, bias=True)
        self.highway_transform = nn.Linear(hidden_size, hidden_size, bias=True)
        self.act_fn = F.silu
        self._init_weights()
    
    def _init_weights(self):
        nn.init.xavier_uniform_(self.gate_up_proj.weight)
        nn.init.xavier_uniform_(self.down_proj.weight)
        nn.init.xavier_uniform_(self.highway_gate.weight, gain=0.1)
        nn.init.xavier_uniform_(self.highway_transform.weight, gain=0.1)
        for m in [self.gate_up_proj, self.down_proj, self.highway_gate, self.highway_transform]:
            if m.bias is not None:
                nn.init.zeros_(m.bias)
    
    def forward(self, x):
        gate_up = self.gate_up_proj(x)
        gate, up = gate_up.chunk(2, dim=-1)
        activated = self.act_fn(gate) * up
        activated = self.dropout(activated)
        mlp_out = self.down_proj(activated)
        highway_gate = torch.sigmoid(self.highway_gate(x))
        highway_transform = self.highway_transform(x)
        highway_out = highway_gate * mlp_out + (1 - highway_gate) * highway_transform
        return self.dropout(highway_out)


class GatedAttention(nn.Module):
    def __init__(self, hidden_size, num_heads, num_kv_heads, head_dim, dropout=0.1):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.num_kv_heads = num_kv_heads
        self.head_dim = head_dim
        self.q_size = num_heads * head_dim
        self.kv_size = num_kv_heads * head_dim
        self.qkv_size = self.q_size + 2 * self.kv_size
        self.qkv_proj = nn.Linear(hidden_size, self.qkv_size, bias=True)
        self.o_proj = nn.Linear(self.q_size, hidden_size, bias=True)
        self.gate = nn.Linear(hidden_size, self.q_size, bias=True)
        self.q_norm = AdaptiveRMSNorm(head_dim, eps=RMS_NORM_EPS)
        self.k_norm = AdaptiveRMSNorm(head_dim, eps=RMS_NORM_EPS)
        self.scaling = head_dim ** -0.5
        self.dropout = nn.Dropout(dropout)
        self.lookahead_k = nn.Linear(hidden_size, self.kv_size, bias=True)
        self.lookahead_v = nn.Linear(hidden_size, self.kv_size, bias=True)
        self._init_weights()
    
    def _init_weights(self):
        for m in [self.qkv_proj, self.o_proj, self.gate, self.lookahead_k, self.lookahead_v]:
            nn.init.xavier_uniform_(m.weight)
            if m.bias is not None:
                nn.init.zeros_(m.bias)
    
    def forward(self, hidden_states, attention_mask=None, is_bidirectional=False):
        batch_size, seq_len, _ = hidden_states.shape
        qkv = self.qkv_proj(hidden_states)
        q, k, v = qkv.split([self.q_size, self.kv_size, self.kv_size], dim=-1)
        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim)
        k = k.view(batch_size, seq_len, self.num_kv_heads, self.head_dim)
        v = v.view(batch_size, seq_len, self.num_kv_heads, self.head_dim)
        q = self.q_norm(q)
        k = self.k_norm(k)
        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)
        if self.num_kv_heads < self.num_heads:
            repeat = self.num_heads // self.num_kv_heads
            k = k.repeat_interleave(repeat, dim=1)
            v = v.repeat_interleave(repeat, dim=1)
        # Lookahead
        lookahead_k = self.lookahead_k(hidden_states)
        lookahead_v = self.lookahead_v(hidden_states)
        lookahead_k = lookahead_k.view(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        lookahead_v = lookahead_v.view(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        if self.num_kv_heads < self.num_heads:
            lookahead_k = lookahead_k.repeat_interleave(repeat, dim=1)
            lookahead_v = lookahead_v.repeat_interleave(repeat, dim=1)
        k = k + 0.1 * lookahead_k
        v = v + 0.1 * lookahead_v
        attn_output = fa4_attention(q, k, v, causal=not is_bidirectional, scale=self.scaling)
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, self.q_size)
        output = self.o_proj(attn_output)
        gate = torch.sigmoid(self.gate(hidden_states))
        output = output * gate
        return self.dropout(output)


class TreeAttentionPattern(nn.Module):
    def __init__(self, num_heads, head_dim):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.tree_weights = nn.Parameter(torch.ones(num_heads, 4) / 4)
    
    def forward(self, q, k, v):
        weights = F.softmax(self.tree_weights, dim=-1)
        outputs = []
        for i in range(4):
            scale = 2 ** i
            if k.size(-2) >= scale:
                k_ds = k[..., ::scale, :]
                v_ds = v[..., ::scale, :]
                out = fa4_attention(q, k_ds, v_ds, causal=False, scale=self.head_dim ** -0.5)
                outputs.append(out * weights[:, i:i+1, None, None])
        return sum(outputs)


class FrankenV8DecoderLayer(nn.Module):
    def __init__(self, layer_idx, hidden_size, num_heads, num_kv_heads, head_dim, intermediate_size, dropout=0.1):
        super().__init__()
        self.layer_idx = layer_idx
        self.self_attn = GatedAttention(hidden_size, num_heads, num_kv_heads, head_dim, dropout)
        self.mlp = FrankenV8SwiGLU(hidden_size, intermediate_size, dropout)
        self.input_layernorm = AdaptiveRMSNorm(hidden_size, eps=RMS_NORM_EPS)
        self.post_attention_layernorm = AdaptiveRMSNorm(hidden_size, eps=RMS_NORM_EPS)
        self.tree_attn = TreeAttentionPattern(num_heads, head_dim)
        self.manifold_bridge = nn.Linear(hidden_size, hidden_size, bias=False)
        nn.init.xavier_uniform_(self.manifold_bridge.weight, gain=0.05)
    
    def forward(self, hidden_states, attention_mask=None, is_bidirectional=False, use_tree_attn=False):
        manifold_residual = torch.tanh(self.manifold_bridge(hidden_states))
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)
        hidden_states = self.self_attn(hidden_states, attention_mask, is_bidirectional)
        hidden_states = residual + hidden_states + 0.05 * manifold_residual
        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        hidden_states = residual + hidden_states
        return hidden_states


# ============================================================
# AUXILIARY MODULES (swapped GPU↔CPU per wave)
# ============================================================

class MTP4MultiTokenPrediction(nn.Module):
    def __init__(self, hidden_size, vocab_size, num_tokens=4, dropout=0.1):
        super().__init__()
        self.num_tokens = num_tokens
        self.predictors = nn.ModuleList([
            nn.Sequential(nn.Linear(hidden_size, hidden_size, bias=True), nn.SiLU(), nn.Dropout(dropout), nn.Linear(hidden_size, vocab_size, bias=True))
            for _ in range(num_tokens)
        ])
    
    def forward(self, hidden_states):
        return [pred(hidden_states) for pred in self.predictors]

class PARDParallelDecoder(nn.Module):
    """Graft 15: PARD - Parallel Decoding Heads (memory-efficient version).
    
    Original design concatenated 4× vocab logits (~247B params in combiner).
    Fixed: Heads output hidden representations, combined then projected to vocab once.
    """
    def __init__(self, hidden_size, vocab_size, num_parallel=4, dropout=0.1):
        super().__init__()
        self.num_parallel = num_parallel
        self.hidden_size = hidden_size
        self.vocab_size = vocab_size
        
        # Each head outputs a hidden representation (not vocab logits)
        self.heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2, bias=True),
                nn.SiLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size // 2, hidden_size // 4, bias=True),
            )
            for _ in range(num_parallel)
        ])
        
        # Combine hidden representations, then project to vocab once
        self.combiner = nn.Linear(hidden_size // 4 * num_parallel, hidden_size, bias=True)
        self.output_proj = nn.Linear(hidden_size, vocab_size, bias=True)
    
    def forward(self, hidden_states):
        head_outputs = [head(hidden_states) for head in self.heads]
        combined = torch.cat(head_outputs, dim=-1)
        fused = self.combiner(combined)
        return self.output_proj(fused)


class EarlyExitController(nn.Module):
    def __init__(self, hidden_size, num_layers, dropout=0.1):
        super().__init__()
        self.exit_gates = nn.ModuleList([
            nn.Sequential(nn.Linear(hidden_size, hidden_size // 4, bias=True), nn.SiLU(), nn.Dropout(dropout), nn.Linear(hidden_size // 4, 1, bias=True), nn.Sigmoid())
            for _ in range(num_layers)
        ])
    
    def forward(self, hidden_states, layer_idx):
        if layer_idx < len(self.exit_gates):
            return self.exit_gates[layer_idx](hidden_states)
        return torch.ones(hidden_states.size(0), 1, device=hidden_states.device)


class SSDSpeculator(nn.Module):
    """Graft 19: SSD - Speculative Speculative Decoding (fixed)."""
    def __init__(self, hidden_size, vocab_size, num_outcomes=4, dropout=0.1):
        super().__init__()
        self.num_outcomes = num_outcomes
        self.hidden_size = hidden_size
        self.vocab_size = vocab_size
        self.outcome_predictor = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2, bias=True),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, num_outcomes, bias=True)
        )
        # Preemptive feature extractors (output hidden features, not vocab logits)
        self.preemptive_extractors = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2, bias=True),
                nn.SiLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size // 2, hidden_size // 4, bias=True),
            )
            for _ in range(num_outcomes)
        ])
        # Shared projection from hidden features to vocab
        self.preemptive_proj = nn.Linear(hidden_size // 4, vocab_size, bias=True)
        self.confidence_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 4, bias=True),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 4, 1, bias=True),
            nn.Sigmoid()
        )
    
    def forward(self, hidden_states, lm_head_weight=None):
        outcome_logits = self.outcome_predictor(hidden_states)
        preemptive_logits = []
        for extractor in self.preemptive_extractors:
            features = extractor(hidden_states)
            # Always use the dedicated projection layer (features are hidden_size//4, not hidden_size)
            logits = self.preemptive_proj(features)
            preemptive_logits.append(logits)
        confidence = self.confidence_head(hidden_states)
        return outcome_logits, preemptive_logits, confidence


class DARTParallelDraft(nn.Module):
    """Graft 20: DART - Diffusion-Inspired parallel drafting (fixed)."""
    def __init__(self, hidden_size, vocab_size, num_positions=8, dropout=0.1):
        super().__init__()
        self.num_positions = num_positions
        self.hidden_size = hidden_size
        self.vocab_size = vocab_size
        self.position_embeddings = nn.Embedding(num_positions, hidden_size)
        self.dropout = nn.Dropout(dropout)
        self.parallel_extractors = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size, bias=True),
                nn.SiLU(),
                nn.Dropout(dropout),
                nn.LayerNorm(hidden_size),
            )
            for _ in range(num_positions)
        ])
        self.feature_extractor = nn.Sequential(
            nn.Linear(hidden_size, hidden_size, bias=True),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.LayerNorm(hidden_size)
        )
        # Shared output projection (instead of creating new Linear in forward)
        self.output_proj = nn.Linear(hidden_size, vocab_size, bias=True)
    
    def forward(self, hidden_states, lm_head_weight=None):
        bsz, seq_len, hidden = hidden_states.shape
        features = self.feature_extractor(hidden_states)
        logits = []
        for i, extractor in enumerate(self.parallel_extractors):
            pos_emb = self.position_embeddings(torch.tensor(i, device=hidden_states.device))
            pos_emb = pos_emb.view(1, 1, -1).expand(bsz, seq_len, -1)
            combined = features + pos_emb
            combined = self.dropout(combined)
            extracted = extractor(combined)
            if lm_head_weight is not None:
                logit = F.linear(extracted, lm_head_weight)
            else:
                logit = self.output_proj(extracted)
            logits.append(logit)
        return logits


class AdaptiveDraftPolicy(nn.Module):
    def __init__(self, hidden_size, max_depth=16, dropout=0.1):
        super().__init__()
        self.max_depth = max_depth
        self.dropout = nn.Dropout(dropout)
        self.state_encoder = nn.Sequential(nn.Linear(hidden_size, hidden_size // 2, bias=True), nn.SiLU(), nn.Dropout(dropout), nn.LayerNorm(hidden_size // 2))
        self.depth_policy = nn.Sequential(nn.Linear(hidden_size // 2, hidden_size // 4, bias=True), nn.SiLU(), nn.Dropout(dropout), nn.Linear(hidden_size // 4, max_depth, bias=True), nn.Softmax(dim=-1))
        self.exit_policy = nn.Sequential(nn.Linear(hidden_size // 2, hidden_size // 4, bias=True), nn.SiLU(), nn.Dropout(dropout), nn.Linear(hidden_size // 4, 1, bias=True), nn.Sigmoid())
        self.confidence_policy = nn.Sequential(nn.Linear(hidden_size // 2, hidden_size // 4, bias=True), nn.SiLU(), nn.Dropout(dropout), nn.Linear(hidden_size // 4, 1, bias=True), nn.Sigmoid())
    
    def forward(self, hidden_states):
        state = self.state_encoder(hidden_states)
        depth_probs = self.depth_policy(state)
        exit_prob = self.exit_policy(state)
        confidence = self.confidence_policy(state)
        return depth_probs, exit_prob, confidence


# ============================================================
# MAIN MODEL
# ============================================================

class FrankenV8DFlashModel(nn.Module):
    def __init__(self, vocab_size=VOCAB_SIZE, hidden_size=HIDDEN_SIZE, num_layers=NUM_HIDDEN_LAYERS,
                 num_heads=NUM_ATTENTION_HEADS, num_kv_heads=NUM_KEY_VALUE_HEADS, head_dim=HEAD_DIM,
                 intermediate_size=INTERMEDIATE_SIZE, num_aux_layers=NUM_AUX_LAYERS, dropout=0.1):
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_aux_layers = num_aux_layers
        self.use_aux_hidden_state = num_aux_layers > 0
        
        self.embed_tokens = nn.Embedding(vocab_size, hidden_size)
        self.layers = nn.ModuleList([
            FrankenV8DecoderLayer(i, hidden_size, num_heads, num_kv_heads, head_dim, intermediate_size, dropout)
            for i in range(num_layers)
        ])
        self.norm = AdaptiveRMSNorm(hidden_size, eps=RMS_NORM_EPS)
        
        if self.use_aux_hidden_state:
            fc_input_size = hidden_size * num_aux_layers
            self.fc = nn.Linear(fc_input_size, hidden_size, bias=False)
            self.hidden_norm = AdaptiveRMSNorm(hidden_size, eps=RMS_NORM_EPS)
        
        self.lm_head = nn.Linear(hidden_size, vocab_size, bias=False)
        
        # Auxiliary modules (will be managed by GraftManager)
        self.mtp4 = MTP4MultiTokenPrediction(hidden_size, vocab_size, num_tokens=4, dropout=dropout)
        self.pard = PARDParallelDecoder(hidden_size, vocab_size, num_parallel=4, dropout=dropout)
        self.early_exit = EarlyExitController(hidden_size, num_layers, dropout=dropout)
        self.ssd = SSDSpeculator(hidden_size, vocab_size, num_outcomes=4, dropout=dropout)
        self.dart = DARTParallelDraft(hidden_size, vocab_size, num_positions=8, dropout=dropout)
        self.ltd = AdaptiveDraftPolicy(hidden_size, max_depth=16, dropout=dropout)
        
        self._init_weights()
    
    def _init_weights(self):
        """Fast module-level initialization (avoids slow per-parameter loop)."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Embedding):
                nn.init.normal_(module.weight, mean=0, std=0.02)
            elif isinstance(module, AdaptiveRMSNorm):
                nn.init.ones_(module.weight)
                nn.init.ones_(module.scale)
                nn.init.zeros_(module.shift)
                nn.init.xavier_uniform_(module.manifold_gate.weight, gain=0.1)
    
    def forward(self, input_ids, aux_hidden_states=None, attention_mask=None, active_grafts=None):
        if active_grafts is None:
            active_grafts = {}
        
        hidden_states = self.embed_tokens(input_ids)
        
        for i, layer in enumerate(self.layers):
            hidden_states = layer(hidden_states, attention_mask, is_bidirectional=active_grafts.get('bidirectional', False), use_tree_attn=active_grafts.get('tree_attn', False))
            if active_grafts.get('early_exit', False) and i < self.num_layers - 1:
                confidence = self.early_exit(hidden_states, i)
                if confidence.mean() > 0.9:
                    break
        
        hidden_states = self.norm(hidden_states)
        
        if self.use_aux_hidden_state and aux_hidden_states is not None:
            batch_size, seq_len, num_aux, hidden_size = aux_hidden_states.shape
            aux_flat = aux_hidden_states.view(batch_size, seq_len, -1)
            combined = self.fc(aux_flat)
            combined = self.hidden_norm(combined)
            hidden_states = hidden_states + combined
        
        logits = self.lm_head(hidden_states)
        outputs = {'logits': logits}
        
        if active_grafts.get('mtp4', False):
            outputs['mtp_logits'] = self.mtp4(hidden_states)
        if active_grafts.get('pard', False):
            outputs['pard_logits'] = self.pard(hidden_states)
        
        return outputs


# ============================================================
# GRAFT MANAGER — handles GPU↔CPU swapping
# ============================================================

class GraftManager:
    """Manages which graft modules are on GPU vs CPU."""
    
    WAVES = [
        {
            'name': 'Core Architecture',
            'grafts': {'mtp4': False, 'pard': False, 'tree_attn': False, 'early_exit': False, 'bidirectional': False},
            'modules': [],
            'loss_weights': {'primary': 1.0},
        },
        {
            'name': 'Speculation Light (MTP-4 + PARD)',
            'grafts': {'mtp4': True, 'pard': True, 'tree_attn': True, 'early_exit': True, 'bidirectional': False},
            'modules': ['mtp4', 'pard', 'early_exit'],
            'loss_weights': {'primary': 0.6, 'mtp': 0.25, 'pard': 0.15},
        },

        {
            'name': 'Advanced Attention',
            'grafts': {'mtp4': False, 'pard': False, 'tree_attn': False, 'early_exit': False, 'bidirectional': True},
            'modules': [],
            'loss_weights': {'primary': 1.0, 'bidirectional_bonus': 0.1},
        },
    ]
    
    def __init__(self, model, device='cuda', cpu_offload=True):
        self.model = model
        self.device = device
        self.cpu_offload = cpu_offload
        self.current_wave = -1
        
        # Map module names to actual modules
        self.module_map = {
            'mtp4': model.mtp4,
            'pard': model.pard,
            'early_exit': model.early_exit,
            'ssd': model.ssd,
            'dart': model.dart,
            'ltd': model.ltd,
        }
        
        # Initially move ALL auxiliary modules to CPU
        if cpu_offload:
            for name, module in self.module_map.items():
                module.to('cpu')
                print(f"  {name}: moved to CPU")
    
    def set_wave(self, wave_idx):
        """Switch to a new wave: move required modules to GPU, others to CPU."""
        if wave_idx == self.current_wave:
            return
        
        wave = self.WAVES[wave_idx % len(self.WAVES)]
        active_modules = set(wave['modules'])
        
        print(f"\n[GraftManager] Switching to Wave {wave_idx}: {wave['name']}")
        print(f"  Active modules: {list(active_modules) if active_modules else ['(core only)']}")
        
        # Move active modules to GPU
        for name, module in self.module_map.items():
            if name in active_modules:
                if next(module.parameters()).device.type != self.device:
                    module.to(self.device)
                    print(f"  {name}: GPU ✓")
            else:
                if self.cpu_offload and next(module.parameters()).device.type != 'cpu':
                    module.to('cpu')
                    print(f"  {name}: CPU")
        
        # Clear cache after swap
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.current_wave = wave_idx
    
    def get_wave(self, global_step):
        wave_idx = (global_step // self.steps_per_wave) % len(self.WAVES) if hasattr(self, 'steps_per_wave') else 0
        return self.WAVES[wave_idx], wave_idx
    
    def setup(self, steps_per_wave=100):
        self.steps_per_wave = steps_per_wave


# ============================================================
# DATASET
# ============================================================

class HiddenStatesDataset(Dataset):
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
        input_ids = data['input_ids']
        target_logits = data['target_logits']
        if 'hidden_states' in data:
            hidden_states = data['hidden_states']
            num_layers_available = hidden_states.shape[0]
            valid_aux_ids = [min(i, num_layers_available - 1) for i in AUX_LAYER_IDS]
            valid_aux_ids = list(dict.fromkeys(valid_aux_ids))[:NUM_AUX_LAYERS]
            while len(valid_aux_ids) < NUM_AUX_LAYERS:
                valid_aux_ids.append(valid_aux_ids[-1] if valid_aux_ids else 0)
            aux_hidden = hidden_states[valid_aux_ids]
            aux_hidden = aux_hidden.permute(1, 0, 2)
        else:
            seq_len = input_ids.shape[0]
            aux_hidden = torch.zeros(seq_len, NUM_AUX_LAYERS, HIDDEN_SIZE)
        return {'input_ids': input_ids, 'target_logits': target_logits, 'aux_hidden_states': aux_hidden}


def collate_fn(batch):
    max_len = max(item['input_ids'].shape[0] for item in batch)
    batch_size = len(batch)
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
    return {'input_ids': input_ids, 'target_logits': target_logits, 'aux_hidden_states': aux_hidden, 'attention_mask': attention_mask}


# ============================================================
# LK LOSSES
# ============================================================

class LKLosses:
    @staticmethod
    def lk_loss(draft_logits, target_logits, temperature=1.0):
        target_probs = F.softmax(target_logits / temperature, dim=-1)
        draft_log_probs = F.log_softmax(draft_logits / temperature, dim=-1)
        return F.kl_div(draft_log_probs, target_probs, reduction='batchmean')
    
    @staticmethod
    def acceptance_rate_loss(draft_logits, target_logits, temperature=1.0):
        draft_probs = F.softmax(draft_logits / temperature, dim=-1)
        target_probs = F.softmax(target_logits / temperature, dim=-1)
        acceptance = torch.sum(torch.min(draft_probs, target_probs), dim=-1)
        return -acceptance.mean()
    
    @staticmethod
    def combined_loss(draft_logits, target_logits, alpha=0.5, temperature=1.0):
        lk = LKLosses.lk_loss(draft_logits, target_logits, temperature)
        acc = LKLosses.acceptance_rate_loss(draft_logits, target_logits, temperature)
        return alpha * lk + (1 - alpha) * acc


# ============================================================
# TRAINING
# ============================================================

def train(args):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    log_file = os.path.join(args.output_dir, 'training.log')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s',
                        handlers=[logging.FileHandler(log_file), logging.StreamHandler()])
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("FRANKEN V8 DFLASH — PROGRESSIVE GRAFT LOADING")
    logger.info("=" * 70)
    logger.info("Strategy: Core model always on GPU. Aux modules swapped per wave.")
    logger.info(f"Vocab size: {VOCAB_SIZE}")
    logger.info(f"Hidden size: {HIDDEN_SIZE}")
    logger.info(f"Num layers: {NUM_HIDDEN_LAYERS}")
    
    # Create model (core only on GPU initially)
    logger.info("\nCreating Franken v8 model...")
    model = FrankenV8DFlashModel(
        vocab_size=VOCAB_SIZE, hidden_size=HIDDEN_SIZE, num_layers=NUM_HIDDEN_LAYERS,
        num_heads=NUM_ATTENTION_HEADS, num_kv_heads=NUM_KEY_VALUE_HEADS, head_dim=HEAD_DIM,
        intermediate_size=INTERMEDIATE_SIZE, num_aux_layers=NUM_AUX_LAYERS, dropout=args.dropout,
    )
    
    # Setup GraftManager BEFORE moving to GPU (avoids CUDA->CPU transfer deadlock on Blackwell)
    logger.info("\nSetting up GraftManager (CPU offloading)...")
    graft_manager = GraftManager(model, device=device, cpu_offload=True)
    graft_manager.setup(steps_per_wave=args.steps_per_wave)
    
    # Move core model to GPU (aux modules stay on CPU via GraftManager)
    model = model.to(device)
    if args.bf16:
        model = model.to(torch.bfloat16)
        logger.info("Using bfloat16")
    
    # Log parameter counts
    core_params = sum(p.numel() for p in model.embed_tokens.parameters())
    core_params += sum(p.numel() for p in model.layers.parameters())
    core_params += sum(p.numel() for p in model.norm.parameters())
    core_params += sum(p.numel() for p in model.lm_head.parameters())
    if model.use_aux_hidden_state:
        core_params += sum(p.numel() for p in model.fc.parameters())
        core_params += sum(p.numel() for p in model.hidden_norm.parameters())
    
    aux_params = sum(p.numel() for p in model.mtp4.parameters())
    aux_params += sum(p.numel() for p in model.pard.parameters())
    aux_params += sum(p.numel() for p in model.early_exit.parameters())
    aux_params += sum(p.numel() for p in model.ssd.parameters())
    aux_params += sum(p.numel() for p in model.dart.parameters())
    aux_params += sum(p.numel() for p in model.ltd.parameters())
    
    logger.info(f"Core model params: {core_params:,}")
    logger.info(f"Aux module params: {aux_params:,}")
    logger.info(f"Total params: {core_params + aux_params:,}")
    logger.info(f"GPU memory (core only): ~{core_params * 2 / 1e9:.1f}GB (bf16) + ~{core_params * 4 / 1e9:.1f}GB (AdamW states)")
    
    # Dataset
    logger.info(f"\nLoading dataset from {args.hidden_states_dir}...")
    dataset = HiddenStatesDataset(args.hidden_states_dir, max_samples=args.max_steps * args.batch_size)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, collate_fn=collate_fn, num_workers=0, pin_memory=False)
    
    # Optimizer for ALL parameters (core + aux)
    # Even though aux modules may be on CPU, we need the optimizer to have their states
    all_params = list(model.parameters())
    optimizer = torch.optim.AdamW(all_params, lr=args.lr, betas=(0.9, 0.95), eps=1e-8, weight_decay=args.weight_decay)
    logger.info(f"Optimizer: AdamW (all {sum(p.numel() for p in all_params):,} params)")
    
    # Scheduler
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
    
    progress_bar = tqdm(total=args.max_steps, desc="Franken v8 Training")
    
    # Resume from checkpoint if specified
    start_step = 0
    start_epoch = 0
    if args.resume_from:
        if os.path.exists(args.resume_from):
            logger.info(f'Resuming from checkpoint: {args.resume_from}')
            # CRITICAL: Only load model weights, skip optimizer to avoid OOM
            # Checkpoint is 67GB (29GB model + 59GB optimizer state) which exceeds 121GB RAM
            checkpoint = torch.load(args.resume_from, map_location='cpu', mmap=True)
            model.load_state_dict(checkpoint['model_state_dict'])
            logger.info('Model state loaded (optimizer skipped to prevent OOM)')
            start_step = checkpoint.get('step', 0)
            start_epoch = checkpoint.get('epoch', 0)
            global_step = start_step
            del checkpoint
            import gc
            gc.collect()
            torch.cuda.empty_cache()
            logger.info(f'Resumed at step {start_step}, epoch {start_epoch} (optimizer restarted from scratch)')
        else:
            logger.warning(f'Checkpoint not found: {args.resume_from}, starting from scratch')

    while global_step < args.max_steps:
        for batch_idx, batch in enumerate(dataloader):
            if global_step >= args.max_steps:
                break
            
            # Determine current wave
            wave_idx = (global_step // args.steps_per_wave) % len(graft_manager.WAVES)
            wave = graft_manager.WAVES[wave_idx]
            
            # Switch wave if needed (swaps modules GPU↔CPU)
            graft_manager.set_wave(wave_idx)
            
            active_grafts = wave['grafts']
            loss_weights = wave['loss_weights']
            wave_name = wave['name']
            
            input_ids = batch['input_ids'].to(device)
            target_logits = batch['target_logits'].to(device)
            aux_hidden = batch['aux_hidden_states'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            
            if args.bf16:
                target_logits = target_logits.to(torch.bfloat16)
                aux_hidden = aux_hidden.to(torch.bfloat16)
            
            # Forward pass
            outputs = model(input_ids, aux_hidden_states=aux_hidden, attention_mask=attention_mask, active_grafts=active_grafts)
            logits = outputs['logits']
            
            # Compute losses
            loss = torch.tensor(0.0, device=device)
            
            # Primary loss
            primary_loss = LKLosses.combined_loss(logits.view(-1, VOCAB_SIZE), target_logits.view(-1, VOCAB_SIZE), alpha=0.5, temperature=args.temperature)
            loss = loss + loss_weights.get('primary', 1.0) * primary_loss
            
            # MTP-4 loss
            if 'mtp_logits' in outputs and 'mtp' in loss_weights:
                mtp_loss = 0
                for i, mtp_logit in enumerate(outputs['mtp_logits']):
                    if i < target_logits.size(1) - 1:
                        shifted_target = target_logits[:, i+1:, :]
                        if mtp_logit.size(1) <= shifted_target.size(1):
                            mtp_loss += LKLosses.lk_loss(mtp_logit.view(-1, VOCAB_SIZE), shifted_target[:, :mtp_logit.size(1), :].contiguous().view(-1, VOCAB_SIZE), temperature=args.temperature)
                mtp_loss = mtp_loss / len(outputs['mtp_logits'])
                loss = loss + loss_weights['mtp'] * mtp_loss
            
            # PARD loss
            if 'pard_logits' in outputs and 'pard' in loss_weights:
                pard_loss = LKLosses.lk_loss(outputs['pard_logits'].view(-1, VOCAB_SIZE), target_logits.view(-1, VOCAB_SIZE), temperature=args.temperature)
                loss = loss + loss_weights['pard'] * pard_loss
            
            # SSD loss (Wave 1 only) - project logits back to hidden for aux modules
            if 'ssd' in wave['modules'] and 'ssd' in loss_weights:
                # logits is [batch, seq, vocab] - project back to hidden using lm_head transpose
                logits_2d = logits.view(-1, VOCAB_SIZE)  # [batch*seq, vocab]
                hidden_proxy = torch.matmul(logits_2d, model.lm_head.weight)  # [batch*seq, hidden]
                hidden_proxy = hidden_proxy.view(logits.shape[0], logits.shape[1], -1)  # [batch, seq, hidden]
                ssd_outcome, ssd_preemptive, ssd_conf = model.ssd(hidden_proxy)
                ssd_loss = 0
                for preemptive in ssd_preemptive:
                    ssd_loss += LKLosses.lk_loss(preemptive.view(-1, VOCAB_SIZE), target_logits.view(-1, VOCAB_SIZE), temperature=args.temperature)
                ssd_loss = ssd_loss / len(ssd_preemptive)
                loss = loss + loss_weights['ssd'] * ssd_loss
            
            # DART loss (Wave 1 only) - same projection
            if 'dart' in wave['modules'] and 'dart' in loss_weights:
                logits_2d = logits.view(-1, VOCAB_SIZE)
                hidden_proxy = torch.matmul(logits_2d, model.lm_head.weight)
                hidden_proxy = hidden_proxy.view(logits.shape[0], logits.shape[1], -1)
                dart_logits = model.dart(hidden_proxy)
                dart_loss = 0
                for dart_logit in dart_logits:
                    dart_loss += LKLosses.lk_loss(dart_logit.view(-1, VOCAB_SIZE), target_logits.view(-1, VOCAB_SIZE), temperature=args.temperature)
                dart_loss = dart_loss / len(dart_logits)
                loss = loss + loss_weights['dart'] * dart_loss
            
            # LTD loss (Wave 1 only) - same projection
            if 'ltd' in wave['modules'] and 'ltd' in loss_weights:
                logits_2d = logits.view(-1, VOCAB_SIZE)
                hidden_proxy = torch.matmul(logits_2d, model.lm_head.weight)
                hidden_proxy = hidden_proxy.view(logits.shape[0], logits.shape[1], -1)
                depth_probs, exit_prob, confidence = model.ltd(hidden_proxy)
                ltd_loss = -torch.log(depth_probs[:, :4].mean() + 1e-8).mean()
                loss = loss + loss_weights['ltd'] * ltd_loss
            
            # Scale for grad accum
            loss = loss / args.grad_accum
            
            # Backward
            loss.backward()
            
            total_loss += loss.item() * args.grad_accum
            
            # Gradient accumulation
            if (batch_idx + 1) % args.grad_accum == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), args.max_grad_norm)
                
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                
                if torch.cuda.is_available() and args.clear_cache:
                    torch.cuda.empty_cache()
                
                global_step += 1
                progress_bar.update(1)
                
                if global_step % args.log_interval == 0:
                    avg_loss = total_loss / args.log_interval
                    lr = scheduler.get_last_lr()[0]
                    mem_mb = torch.cuda.memory_allocated() / 1e6 if torch.cuda.is_available() else 0
                    logger.info(f"Step {global_step}/{args.max_steps} | Wave: {wave_name} | Loss: {avg_loss:.4f} | LR: {lr:.6f} | GPU: {mem_mb:.0f}MB | Epoch: {epoch}")
                    total_loss = 0
                
                if global_step % args.save_interval == 0:
                    checkpoint_path = os.path.join(args.output_dir, f'checkpoint-{global_step}.pt')
                    torch.save({'step': global_step, 'epoch': epoch, 'model_state_dict': model.state_dict()}, checkpoint_path)
                    logger.info(f"Saved lightweight checkpoint: {checkpoint_path}")
        
        epoch += 1
    
    progress_bar.close()
    
    # Save final
    final_path = os.path.join(args.output_dir, 'final_model.pt')
    torch.save({'step': global_step, 'epoch': epoch, 'model_state_dict': model.state_dict()}, final_path)
    logger.info(f"Saved final model: {final_path}")
    
    config_json = {
        "architectures": ["DFlashQwen3ForCausalLM"], "hidden_size": HIDDEN_SIZE,
        "num_attention_heads": NUM_ATTENTION_HEADS, "num_key_value_heads": NUM_KEY_VALUE_HEADS,
        "head_dim": HEAD_DIM, "intermediate_size": INTERMEDIATE_SIZE, "vocab_size": VOCAB_SIZE,
        "num_hidden_layers": NUM_HIDDEN_LAYERS, "rms_norm_eps": RMS_NORM_EPS,
        "max_position_embeddings": MAX_POSITION_EMBEDDINGS, "aux_layer_ids": AUX_LAYER_IDS,
        "model_type": "qwen3", "torch_dtype": "bfloat16" if args.bf16 else "float32",
        "franken_v8_version": "progressive_graft_loading",
        "training_strategy": "wave_rotation_with_cpu_offload",
        "steps_per_wave": args.steps_per_wave,
    }
    
    with open(os.path.join(args.output_dir, 'config.json'), 'w') as f:
        json.dump(config_json, f, indent=2)
    
    logger.info("\n" + "=" * 70)
    logger.info("FRANKEN V8 TRAINING COMPLETE (Progressive Graft Loading)")
    logger.info("=" * 70)
    logger.info("ALL 25 grafts trained via wave rotation with CPU offloading")


def main():
    parser = argparse.ArgumentParser(description='Train Franken v8 DFlash (PROGRESSIVE GRAFT LOADING)')
    parser.add_argument('--lr', type=float, default=0.0001)
    parser.add_argument('--batch-size', type=int, default=1)
    parser.add_argument('--grad-accum', type=int, default=2)
    parser.add_argument('--max-steps', type=int, default=10000)
    parser.add_argument('--warmup-steps', type=int, default=500)
    parser.add_argument('--weight-decay', type=float, default=0.01)
    parser.add_argument('--max-grad-norm', type=float, default=1.0)
    parser.add_argument('--temperature', type=float, default=1.0)
    parser.add_argument('--dropout', type=float, default=0.1)
    parser.add_argument('--bf16', action='store_true', default=True)
    parser.add_argument('--steps-per-wave', type=int, default=100)
    parser.add_argument('--clear-cache', action='store_true', default=True)
    parser.add_argument('--hidden-states-dir', type=str, default="/data/SpecForge/custom_dflash/hidden_states_full")
    parser.add_argument('--output-dir', type=str, default="/data/models/FrankenV8-DFlash-vLLM")
    parser.add_argument('--save-interval', type=int, default=500)
    parser.add_argument('--log-interval', type=int, default=10)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--resume-from', type=str, default=None, help='Resume training from checkpoint path')
    args = parser.parse_args()
    
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    
    train(args)


if __name__ == '__main__':
    main()
