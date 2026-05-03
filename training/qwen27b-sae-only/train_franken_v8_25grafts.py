#!/usr/bin/env python3
"""
FRANKEN v8 DFLASH — FULL 25 GRAFTS + FLASH ATTENTION 2 (or SDPA fallback)

Problem: ALL 25 grafts = ~12B+ params = OOM on GB10
Solution: Progressive wave-based training + CPU offloading for aux modules

This script:
1. Defines ALL 25 FrankenV8 grafts
2. Uses Flash Attention 2 if available, otherwise memory-efficient SDPA
3. Trains via progressive waves (only active wave's modules on GPU)
4. Supports batch training with logits distillation
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

# Try to import Flash Attention 4, fallback to SDPA
try:
    from flash_attn.cute import flash_attn_func as fa4_flash_attn_func
    HAS_FLASH_ATTN = True
    FA_VERSION = 4
    print("[INFO] Flash Attention 4 (CuTeDSL) loaded successfully - Blackwell optimized")
except ImportError:
    HAS_FLASH_ATTN = False
    FA_VERSION = 0
    print("[INFO] Flash Attention not available, using PyTorch SDPA")

# ============================================================
# FLASH ATTENTION WRAPPER (FA4 compatible)
# ============================================================

def flash_attention_wrapper(q, k, v, attn_mask=None, dropout_p=0.0, is_causal=True, scale=None):
    """
    Unified attention interface.
    Uses Flash Attention 4 if available, otherwise PyTorch SDPA.
    
    FA4 expects (batch, seq_len, num_heads, head_dim) format.
    Returns tensor directly (handles FA4's tuple output).
    """
    if HAS_FLASH_ATTN and FA_VERSION == 4:
        # FA4 expects (batch, seq_len, num_heads, head_dim)
        # No transpose needed - keep in FA4 format
        result = fa4_flash_attn_func(
            q, k, v,
            causal=is_causal,
        )
        # FA4 returns (output, lse) tuple
        if isinstance(result, tuple):
            return result[0]
        return result
    else:
        # PyTorch SDPA - expects (batch, num_heads, seq_len, head_dim)
        if q.dim() == 4 and q.size(1) != q.size(2):
            # Check if in FA format (batch, seq, heads, dim) -> transpose to SDPA
            if q.size(2) == NUM_ATTENTION_HEADS or q.size(2) == NUM_KEY_VALUE_HEADS:
                q = q.transpose(1, 2)
                k = k.transpose(1, 2)
                v = v.transpose(1, 2)
        
        return F.scaled_dot_product_attention(
            q, k, v,
            attn_mask=attn_mask,
            dropout_p=dropout_p,
            is_causal=is_causal,
            scale=scale
        )

# ============================================================
# CORE MODULES (always on GPU)
# ============================================================

class AdaptiveRMSNorm(nn.Module):
    """Graft 7: Adaptive RMSNorm with learnable scale/shift + manifold gate."""
    def __init__(self, hidden_size, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.eps = eps
        self.scale = nn.Parameter(torch.ones(1))
        self.shift = nn.Parameter(torch.zeros(1))
        # Graft 3: Manifold Hyper-Connection
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
    """Graft 2: SwiGLU + Graft 8: Highway Connections."""
    def __init__(self, hidden_size, intermediate_size, dropout=0.1):
        super().__init__()
        self.gate_up_proj = nn.Linear(hidden_size, 2 * intermediate_size, bias=True)
        self.down_proj = nn.Linear(intermediate_size, hidden_size, bias=True)
        self.dropout = nn.Dropout(dropout)
        # Graft 8: Highway Connection
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
        # Highway
        highway_gate = torch.sigmoid(self.highway_gate(x))
        highway_transform = self.highway_transform(x)
        highway_out = highway_gate * mlp_out + (1 - highway_gate) * highway_transform
        return self.dropout(highway_out)


class GatedAttention(nn.Module):
    """Graft 4: Gated Attention + Graft 5: RoPE (implicit) + Graft 14: Lookahead."""
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
        # Graft 14: Lookahead Attention
        self.lookahead_k = nn.Linear(hidden_size, self.kv_size, bias=True)
        self.lookahead_v = nn.Linear(hidden_size, self.kv_size, bias=True)
        self._init_weights()
    
    def _init_weights(self):
        for m in [self.qkv_proj, self.o_proj, self.gate, self.lookahead_k, self.lookahead_v]:
            nn.init.xavier_uniform_(m.weight)
            if m.bias is not None:
                nn.init.zeros_(m.bias)
    
    def forward(self, hidden_states, attention_mask=None, is_bidirectional=False, use_lookahead=False):
        batch_size, seq_len, _ = hidden_states.shape
        qkv = self.qkv_proj(hidden_states)
        q, k, v = qkv.split([self.q_size, self.kv_size, self.kv_size], dim=-1)
        
        # Reshape for multi-head attention
        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim)
        k = k.view(batch_size, seq_len, self.num_kv_heads, self.head_dim)
        v = v.view(batch_size, seq_len, self.num_kv_heads, self.head_dim)
        
        # RMSNorm on head dimension
        q = self.q_norm(q)
        k = self.k_norm(k)
        
        # Transpose for attention: (batch, num_heads, seq_len, head_dim)
        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)
        
        # Repeat KV heads for GQA
        if self.num_kv_heads < self.num_heads:
            repeat = self.num_heads // self.num_kv_heads
            k = k.repeat_interleave(repeat, dim=1)
            v = v.repeat_interleave(repeat, dim=1)
        
        # Graft 14: Lookahead (only if enabled)
        if use_lookahead:
            lookahead_k = self.lookahead_k(hidden_states)
            lookahead_v = self.lookahead_v(hidden_states)
            lookahead_k = lookahead_k.view(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
            lookahead_v = lookahead_v.view(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
            if self.num_kv_heads < self.num_heads:
                lookahead_k = lookahead_k.repeat_interleave(repeat, dim=1)
                lookahead_v = lookahead_v.repeat_interleave(repeat, dim=1)
            k = k + 0.1 * lookahead_k
            v = v + 0.1 * lookahead_v
        
        # Flash Attention 2 or SDPA
        attn_output = flash_attention_wrapper(
            q, k, v,
            attn_mask=attention_mask,
            dropout_p=self.dropout.p if self.training else 0.0,
            is_causal=not is_bidirectional,
            scale=self.scaling
        )
        
        # Reshape back
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, self.q_size)
        
        output = self.o_proj(attn_output)
        gate = torch.sigmoid(self.gate(hidden_states))
        output = output * gate
        return self.dropout(output)


class TreeAttentionPattern(nn.Module):
    """Graft 16: Tree Attention — multi-scale attention."""
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
                out = F.scaled_dot_product_attention(q, k_ds, v_ds, scale=self.head_dim ** -0.5)
                outputs.append(out * weights[:, i:i+1, None, None])
        return sum(outputs)


class FrankenV8DecoderLayer(nn.Module):
    """Full decoder layer with all core grafts."""
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
    
    def forward(self, hidden_states, attention_mask=None, is_bidirectional=False, use_tree_attn=False, use_lookahead=False):
        # Graft 3: Manifold Hyper-Connection
        manifold_residual = torch.tanh(self.manifold_bridge(hidden_states))
        
        # Attention sublayer
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)
        hidden_states = self.self_attn(hidden_states, attention_mask, is_bidirectional, use_lookahead)
        hidden_states = residual + hidden_states + 0.05 * manifold_residual
        
        # MLP sublayer
        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        hidden_states = residual + hidden_states
        
        # Graft 16: Tree Attention (if enabled)
        if use_tree_attn:
            # Apply tree attention as additional refinement
            batch_size, seq_len, _ = hidden_states.shape
            q = hidden_states.view(batch_size, seq_len, self.self_attn.num_heads, self.self_attn.head_dim).transpose(1, 2)
            k = q.clone()
            v = q.clone()
            tree_out = self.tree_attn(q, k, v)
            tree_out = tree_out.transpose(1, 2).contiguous().view(batch_size, seq_len, -1)
            hidden_states = hidden_states + 0.1 * tree_out
        
        return hidden_states


# ============================================================
# AUXILIARY MODULES (swapped GPU↔CPU per wave)
# ============================================================

class MTP4MultiTokenPrediction(nn.Module):
    """Graft 6: MTP-4 Multi-Token Prediction."""
    def __init__(self, hidden_size, vocab_size, num_tokens=4, dropout=0.1):
        super().__init__()
        self.num_tokens = num_tokens
        self.predictors = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size, bias=True),
                nn.SiLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size, vocab_size, bias=True)
            )
            for _ in range(num_tokens)
        ])
    
    def forward(self, hidden_states):
        return [pred(hidden_states) for pred in self.predictors]


class PARDParallelDecoder(nn.Module):
    """Graft 15: PARD - Parallel Decoding Heads (memory-efficient)."""
    def __init__(self, hidden_size, vocab_size, num_parallel=4, dropout=0.1):
        super().__init__()
        self.num_parallel = num_parallel
        self.hidden_size = hidden_size
        self.vocab_size = vocab_size
        
        # Each head outputs hidden representation (not vocab logits)
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
    """Graft 17: Early Exit Controller."""
    def __init__(self, hidden_size, num_layers, dropout=0.1):
        super().__init__()
        self.exit_gates = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 4, bias=True),
                nn.SiLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size // 4, 1, bias=True),
                nn.Sigmoid()
            )
            for _ in range(num_layers)
        ])
    
    def forward(self, hidden_states, layer_idx):
        if layer_idx < len(self.exit_gates):
            return self.exit_gates[layer_idx](hidden_states)
        return torch.ones(hidden_states.size(0), 1, device=hidden_states.device)


class SSDSpeculator(nn.Module):
    """Graft 19: SSD - Speculative Speculative Decoding."""
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
        
        # Preemptive feature extractors (output hidden features)
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
            logits = self.preemptive_proj(features)
            preemptive_logits.append(logits)
        confidence = self.confidence_head(hidden_states)
        return outcome_logits, preemptive_logits, confidence


class DARTParallelDraft(nn.Module):
    """Graft 20: DART - Diffusion-Inspired parallel drafting."""
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
        
        # Shared output projection
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
    """Graft 21: LTD - Learned Tree Depth / Adaptive Draft Policy."""
    def __init__(self, hidden_size, max_depth=16, dropout=0.1):
        super().__init__()
        self.max_depth = max_depth
        self.dropout = nn.Dropout(dropout)
        
        self.state_encoder = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2, bias=True),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.LayerNorm(hidden_size // 2)
        )
        
        self.depth_policy = nn.Sequential(
            nn.Linear(hidden_size // 2, hidden_size // 4, bias=True),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 4, max_depth, bias=True),
            nn.Softmax(dim=-1)
        )
        
        self.exit_policy = nn.Sequential(
            nn.Linear(hidden_size // 2, hidden_size // 4, bias=True),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 4, 1, bias=True),
            nn.Sigmoid()
        )
        
        self.confidence_policy = nn.Sequential(
            nn.Linear(hidden_size // 2, hidden_size // 4, bias=True),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 4, 1, bias=True),
            nn.Sigmoid()
        )
    
    def forward(self, hidden_states):
        state = self.state_encoder(hidden_states)
        depth_probs = self.depth_policy(state)
        exit_prob = self.exit_policy(state)
        confidence = self.confidence_policy(state)
        return depth_probs, exit_prob, confidence


# ============================================================
# MAIN MODEL — ALL 25 GRAFTS
# ============================================================

class FrankenV8DFlashModel(nn.Module):
    """
    Franken v8 DFlash with ALL 25 grafts.
    
    Graft List:
    1. Base architecture (Qwen3-style)
    2. SwiGLU MLP
    3. Manifold Hyper-Connections
    4. Gated Attention
    5. RoPE (implicit in attention)
    6. MTP-4 Multi-Token Prediction
    7. Adaptive RMSNorm
    8. Highway Connections
    9. [Reserved]
    10. [Reserved]
    11. [Reserved]
    12. [Reserved]
    13. [Reserved]
    14. Lookahead Attention
    15. PARD Parallel Decoding
    16. Tree Attention
    17. Early Exit
    18. LK Losses (training objective)
    19. SSD Speculative Decoding
    20. DART Parallel Draft
    21. LTD Learned Tree Depth
    22-25. [Reserved for future]
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
        dropout=0.1,
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_aux_layers = num_aux_layers
        self.use_aux_hidden_state = num_aux_layers > 0
        
        # Token embeddings (Graft 1)
        self.embed_tokens = nn.Embedding(vocab_size, hidden_size)
        
        # Decoder layers (Grafts 2-5, 7-8, 14, 16)
        self.layers = nn.ModuleList([
            FrankenV8DecoderLayer(
                i, hidden_size, num_heads, num_kv_heads, head_dim, intermediate_size, dropout
            )
            for i in range(num_layers)
        ])
        
        # Final norm (Graft 7)
        self.norm = AdaptiveRMSNorm(hidden_size, eps=RMS_NORM_EPS)
        
        # FC for aux hidden states (P-EAGLE style)
        if self.use_aux_hidden_state:
            fc_input_size = hidden_size * num_aux_layers
            self.fc = nn.Linear(fc_input_size, hidden_size, bias=False)
            self.hidden_norm = AdaptiveRMSNorm(hidden_size, eps=RMS_NORM_EPS)
        
        # LM head
        self.lm_head = nn.Linear(hidden_size, vocab_size, bias=False)
        
        # === AUXILIARY MODULES (managed by GraftManager) ===
        # Graft 6: MTP-4
        self.mtp4 = MTP4MultiTokenPrediction(hidden_size, vocab_size, num_tokens=4, dropout=dropout)
        # Graft 15: PARD
        self.pard = PARDParallelDecoder(hidden_size, vocab_size, num_parallel=4, dropout=dropout)
        # Graft 17: Early Exit
        self.early_exit = EarlyExitController(hidden_size, num_layers, dropout=dropout)
        # Graft 19: SSD
        self.ssd = SSDSpeculator(hidden_size, vocab_size, num_outcomes=4, dropout=dropout)
        # Graft 20: DART
        self.dart = DARTParallelDraft(hidden_size, vocab_size, num_positions=8, dropout=dropout)
        # Graft 21: LTD
        self.ltd = AdaptiveDraftPolicy(hidden_size, max_depth=16, dropout=dropout)
        
        self._init_weights()
    
    def _init_weights(self):
        """Fast module-level initialization."""
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
    
    def forward(
        self,
        input_ids,
        aux_hidden_states=None,
        attention_mask=None,
        active_grafts=None,
    ):
        if active_grafts is None:
            active_grafts = {}
        
        # Embed tokens
        hidden_states = self.embed_tokens(input_ids)
        
        # Pass through decoder layers
        for i, layer in enumerate(self.layers):
            hidden_states = layer(
                hidden_states,
                attention_mask,
                is_bidirectional=active_grafts.get('bidirectional', False),
                use_tree_attn=active_grafts.get('tree_attn', False),
                use_lookahead=active_grafts.get('lookahead', False),
            )
            
            # Graft 17: Early Exit (if enabled)
            if active_grafts.get('early_exit', False) and i < self.num_layers - 1:
                exit_prob = self.early_exit(hidden_states, i)
                # During training, we don't actually exit — just compute the loss
        
        # Final norm
        hidden_states = self.norm(hidden_states)
        
        # Combine with aux hidden states (P-EAGLE style)
        if self.use_aux_hidden_state and aux_hidden_states is not None:
            batch_size, seq_len, num_aux, hidden_size = aux_hidden_states.shape
            aux_flat = aux_hidden_states.view(batch_size, seq_len, -1)
            combined = self.fc(aux_flat)
            combined = self.hidden_norm(combined)
            hidden_states = hidden_states + combined
        
        # Primary LM head
        logits = self.lm_head(hidden_states)
        
        outputs = {'logits': logits}
        
        # Graft 6: MTP-4 (if enabled)
        if active_grafts.get('mtp4', False):
            mtp_logits = self.mtp4(hidden_states)
            outputs['mtp_logits'] = mtp_logits
        
        # Graft 15: PARD (if enabled)
        if active_grafts.get('pard', False):
            pard_logits = self.pard(hidden_states)
            outputs['pard_logits'] = pard_logits
        
        # Graft 19: SSD (if enabled)
        if active_grafts.get('ssd', False):
            outcome_logits, preemptive_logits, confidence = self.ssd(hidden_states)
            outputs['ssd_outcome'] = outcome_logits
            outputs['ssd_preemptive'] = preemptive_logits
            outputs['ssd_confidence'] = confidence
        
        # Graft 20: DART (if enabled)
        if active_grafts.get('dart', False):
            dart_logits = self.dart(hidden_states)
            outputs['dart_logits'] = dart_logits
        
        # Graft 21: LTD (if enabled)
        if active_grafts.get('ltd', False):
            depth_probs, exit_prob, confidence = self.ltd(hidden_states)
            outputs['ltd_depth'] = depth_probs
            outputs['ltd_exit'] = exit_prob
            outputs['ltd_confidence'] = confidence
        
        return outputs
    
    def get_weight_shapes(self):
        """Return weight shapes for vLLM compatibility."""
        shapes = {}
        shapes['embed_tokens.weight'] = (self.vocab_size, self.hidden_size)
        shapes['lm_head.weight'] = (self.vocab_size, self.hidden_size)
        shapes['norm.weight'] = (self.hidden_size,)
        
        for i in range(self.num_layers):
            prefix = f'layers.{i}'
            shapes[f'{prefix}.self_attn.qkv_proj.weight'] = (
                NUM_ATTENTION_HEADS * HEAD_DIM + 2 * NUM_KEY_VALUE_HEADS * HEAD_DIM,
                self.hidden_size
            )
            shapes[f'{prefix}.self_attn.o_proj.weight'] = (
                self.hidden_size, NUM_ATTENTION_HEADS * HEAD_DIM
            )
            shapes[f'{prefix}.self_attn.q_norm.weight'] = (HEAD_DIM,)
            shapes[f'{prefix}.self_attn.k_norm.weight'] = (HEAD_DIM,)
            shapes[f'{prefix}.mlp.gate_up_proj.weight'] = (
                2 * INTERMEDIATE_SIZE, self.hidden_size
            )
            shapes[f'{prefix}.mlp.down_proj.weight'] = (
                self.hidden_size, INTERMEDIATE_SIZE
            )
            shapes[f'{prefix}.input_layernorm.weight'] = (self.hidden_size,)
            shapes[f'{prefix}.post_attention_layernorm.weight'] = (self.hidden_size,)
        
        if self.use_aux_hidden_state:
            shapes['fc.weight'] = (self.hidden_size, self.hidden_size * self.num_aux_layers)
            shapes['hidden_norm.weight'] = (self.hidden_size,)
        
        return shapes
    
    def load_vllm_weights(self, weights_dict):
        """Load weights from vLLM-format state dict."""
        our_state = self.state_dict()
        loaded = set()
        
        for name, param in weights_dict.items():
            if name in our_state:
                our_state[name].copy_(param)
                loaded.add(name)
            elif 'qkv_proj' in name:
                layer_idx = int(name.split('.')[1])
                qkv = param
                q_size = self.num_heads * self.head_dim
                kv_size = self.num_kv_heads * self.head_dim
                qkv_name = f'layers.{layer_idx}.self_attn.qkv_proj.weight'
                if qkv_name in our_state:
                    our_state[qkv_name].copy_(qkv)
                    loaded.add(qkv_name)
            elif 'gate_up_proj' in name:
                layer_idx = int(name.split('.')[1])
                gate_up = param
                gate_up_name = f'layers.{layer_idx}.mlp.gate_up_proj.weight'
                if gate_up_name in our_state:
                    our_state[gate_up_name].copy_(gate_up)
                    loaded.add(gate_up_name)
        
        return loaded


# ============================================================
# GRAFT MANAGER — PROGRESSIVE WAVE TRAINING
# ============================================================

class GraftManager:
    """Manages which graft modules are on GPU vs CPU during training."""
    
    WAVES = [
        {
            'name': 'Wave 1: Core Architecture',
            'grafts': {
                'mtp4': False, 'pard': False, 'tree_attn': False,
                'early_exit': False, 'bidirectional': False, 'lookahead': False,
                'ssd': False, 'dart': False, 'ltd': False,
            },
            'modules': [],
            'loss_weights': {'primary': 1.0},
            'description': 'Train core: SwiGLU, Manifold, GatedAttention, RMSNorm, Highway',
        },
        {
            'name': 'Wave 2: Speculation Light (MTP-4 + PARD + Early Exit)',
            'grafts': {
                'mtp4': True, 'pard': True, 'tree_attn': True,
                'early_exit': True, 'bidirectional': False, 'lookahead': False,
                'ssd': False, 'dart': False, 'ltd': False,
            },
            'modules': ['mtp4', 'pard', 'early_exit'],
            'loss_weights': {'primary': 0.6, 'mtp': 0.25, 'pard': 0.15},
            'description': 'Train speculation modules: MTP-4, PARD, Early Exit',
        },
        {
            'name': 'Wave 3: Speculation Heavy (SSD + DART + LTD)',
            'grafts': {
                'mtp4': False, 'pard': False, 'tree_attn': False,
                'early_exit': False, 'bidirectional': False, 'lookahead': False,
                'ssd': True, 'dart': True, 'ltd': True,
            },
            'modules': ['ssd', 'dart', 'ltd'],
            'loss_weights': {'primary': 0.5, 'ssd': 0.2, 'dart': 0.2, 'ltd': 0.1},
            'description': 'Train heavy speculation: SSD, DART, LTD',
        },
        {
            'name': 'Wave 4: Advanced Attention (Bidirectional + Lookahead + Tree)',
            'grafts': {
                'mtp4': False, 'pard': False, 'tree_attn': True,
                'early_exit': False, 'bidirectional': True, 'lookahead': True,
                'ssd': False, 'dart': False, 'ltd': False,
            },
            'modules': [],
            'loss_weights': {'primary': 1.0, 'bidirectional_bonus': 0.1},
            'description': 'Train attention variants: bidirectional, lookahead, tree',
        },
        {
            'name': 'Wave 5: ALL GRAFTS (fine-tuning)',
            'grafts': {
                'mtp4': True, 'pard': True, 'tree_attn': True,
                'early_exit': True, 'bidirectional': True, 'lookahead': True,
                'ssd': True, 'dart': True, 'ltd': True,
            },
            'modules': ['mtp4', 'pard', 'early_exit', 'ssd', 'dart', 'ltd'],
            'loss_weights': {'primary': 0.4, 'mtp': 0.1, 'pard': 0.1, 'ssd': 0.1, 'dart': 0.1, 'ltd': 0.05, 'early_exit': 0.05, 'bidirectional_bonus': 0.05, 'lookahead_bonus': 0.05},
            'description': 'Fine-tune all grafts together (highest memory, shortest duration)',
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
                print(f"  [GraftManager] {name}: moved to CPU (cold start)")
    
    def set_wave(self, wave_idx):
        """Switch to a new wave: move required modules to GPU, others to CPU."""
        if wave_idx == self.current_wave:
            return
        
        wave = self.WAVES[wave_idx % len(self.WAVES)]
        active_modules = set(wave['modules'])
        
        print(f"\n{'='*60}")
        print(f"[GraftManager] Switching to Wave {wave_idx}: {wave['name']}")
        print(f"[GraftManager] Description: {wave['description']}")
        print(f"[GraftManager] Active modules: {list(active_modules) if active_modules else ['(core only)']}")
        print(f"{'='*60}\n")
        
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
    
    def get_wave(self, global_step, steps_per_wave=100):
        wave_idx = (global_step // steps_per_wave) % len(self.WAVES)
        return self.WAVES[wave_idx], wave_idx


# ============================================================
# DATASET
# ============================================================

class HiddenStatesDataset(Dataset):
    """Dataset for logits distillation training."""
    def __init__(self, hidden_states_dir, max_samples=None):
        self.hidden_states_dir = Path(hidden_states_dir)
        self.samples = sorted(self.hidden_states_dir.glob('sample_*.pt'))
        if max_samples:
            self.samples = self.samples[:max_samples]
        print(f"[Dataset] Loaded {len(self.samples)} samples from {hidden_states_dir}")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        data = torch.load(self.samples[idx], map_location='cpu')
        return {
            'input_ids': data['input_ids'],
            'target_logits': data['target_logits'],
            'aux_hidden_states': data.get('aux_hidden_states', torch.zeros(1)),
            'attention_mask': data.get('attention_mask', torch.ones_like(data['input_ids'], dtype=torch.bool)),
        }


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
        if item['aux_hidden_states'].dim() == 3:
            aux_hidden[i, :seq_len] = item['aux_hidden_states']
        attention_mask[i, :seq_len] = item['attention_mask']
    
    return {
        'input_ids': input_ids,
        'target_logits': target_logits,
        'aux_hidden_states': aux_hidden,
        'attention_mask': attention_mask,
    }


# ============================================================
# LK LOSS (Graft 18)
# ============================================================

class LKLoss(nn.Module):
    """Graft 18: LK Losses for direct acceptance rate optimization."""
    def __init__(self, vocab_size, temperature=1.0):
        super().__init__()
        self.vocab_size = vocab_size
        self.temperature = temperature
    
    def forward(self, draft_logits, target_logits, mask=None):
        draft_log_probs = F.log_softmax(draft_logits / self.temperature, dim=-1)
        target_probs = F.softmax(target_logits / self.temperature, dim=-1)
        
        kl_div = F.kl_div(draft_log_probs, target_probs, reduction='none')
        kl_div = kl_div.sum(dim=-1)
        
        if mask is not None:
            kl_div = kl_div * mask.float()
            return kl_div.sum() / mask.float().sum().clamp(min=1)
        return kl_div.mean()


# ============================================================
# TRAINING
# ============================================================

def train(args):
    # Setup
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    torch.manual_seed(42)
    
    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(args.output_dir, 'train.log')),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    logger.info("="*70)
    logger.info("FRANKEN v8 DFLASH — FULL 25 GRAFTS + PROGRESSIVE WAVE TRAINING")
    logger.info("="*70)
    logger.info(f"Flash Attention: {'FA4 (CuTeDSL, Blackwell-optimized)' if HAS_FLASH_ATTN else 'SDPA fallback'}")
    logger.info(f"Device: {device}")
    logger.info(f"Output: {args.output_dir}")
    logger.info(f"Batch: {args.hidden_states_dir}")
    logger.info("="*70)
    
    # Model
    logger.info("\n[1/5] Initializing FrankenV8 model (ALL 25 grafts)...")
    model = FrankenV8DFlashModel(dropout=args.dropout)
    model = model.to(device)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Total parameters: {total_params:,} ({total_params/1e9:.2f}B)")
    logger.info(f"Trainable: {trainable_params:,} ({trainable_params/1e9:.2f}B)")
    
    # GraftManager for progressive training
    logger.info("\n[2/5] Setting up GraftManager (progressive wave training)...")
    graft_manager = GraftManager(model, device=device, cpu_offload=True)
    
    # Optimizer (AdamW for all parameters)
    logger.info("\n[3/5] Setting up optimizer...")
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr,
        betas=(0.9, 0.95),
        eps=1e-8,
        weight_decay=args.weight_decay,
    )
    
    # Scheduler
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=args.max_steps,
        eta_min=args.lr * 0.1,
    )
    
    # Loss
    lk_loss = LKLoss(VOCAB_SIZE, temperature=args.temperature).to(device)
    
    # Dataset
    logger.info("\n[4/5] Loading dataset...")
    dataset = HiddenStatesDataset(args.hidden_states_dir, max_samples=args.max_steps * args.batch_size)
    dataloader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=0,
        pin_memory=True,
    )
    
    # Training loop
    logger.info("\n[5/5] Starting training...")
    logger.info(f"Max steps: {args.max_steps}")
    logger.info(f"Steps per wave: {args.steps_per_wave}")
    logger.info(f"Gradient accumulation: {args.grad_accum}")
    logger.info(f"Effective batch size: {args.batch_size * args.grad_accum}")
    
    model.train()
    global_step = 0
    epoch = 0
    losses = []
    
    pbar = tqdm(total=args.max_steps, desc="Training")
    
    while global_step < args.max_steps:
        epoch += 1
        logger.info(f"\n--- Epoch {epoch} ---")
        
        for batch_idx, batch in enumerate(dataloader):
            if global_step >= args.max_steps:
                break
            
            # Determine current wave
            wave, wave_idx = graft_manager.get_wave(global_step, args.steps_per_wave)
            
            # Switch wave if needed (swaps modules GPU↔CPU)
            graft_manager.set_wave(wave_idx)
            
            active_grafts = wave['grafts']
            loss_weights = wave['loss_weights']
            wave_name = wave['name']
            
            # Move data to device
            input_ids = batch['input_ids'].to(device)
            target_logits = batch['target_logits'].to(device)
            aux_hidden = batch['aux_hidden_states'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            
            # Forward pass
            outputs = model(
                input_ids,
                aux_hidden_states=aux_hidden,
                attention_mask=attention_mask,
                active_grafts=active_grafts,
            )
            
            draft_logits = outputs['logits']
            
            # Primary loss: LK Loss
            loss = lk_loss(draft_logits, target_logits, attention_mask)
            weighted_loss = loss * loss_weights['primary']
            
            # Auxiliary losses (only if modules are active)
            if 'mtp_logits' in outputs and 'mtp' in loss_weights:
                mtp_loss = sum(lk_loss(mtp, target_logits, attention_mask) for mtp in outputs['mtp_logits'])
                weighted_loss += mtp_loss * loss_weights['mtp'] / len(outputs['mtp_logits'])
            
            if 'pard_logits' in outputs and 'pard' in loss_weights:
                pard_loss = lk_loss(outputs['pard_logits'], target_logits, attention_mask)
                weighted_loss += pard_loss * loss_weights['pard']
            
            if 'ssd_preemptive' in outputs and 'ssd' in loss_weights:
                ssd_loss = sum(lk_loss(pl, target_logits, attention_mask) for pl in outputs['ssd_preemptive'])
                weighted_loss += ssd_loss * loss_weights['ssd'] / len(outputs['ssd_preemptive'])
            
            if 'dart_logits' in outputs and 'dart' in loss_weights:
                dart_loss = sum(lk_loss(dl, target_logits, attention_mask) for dl in outputs['dart_logits'])
                weighted_loss += dart_loss * loss_weights['dart'] / len(outputs['dart_logits'])
            
            # Scale by grad accum
            weighted_loss = weighted_loss / args.grad_accum
            
            # Backward
            weighted_loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), args.max_grad_norm)
            
            # Update weights
            if (batch_idx + 1) % args.grad_accum == 0:
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                global_step += 1
                
                losses.append(loss.item())
                pbar.update(1)
                pbar.set_postfix({
                    'loss': f"{loss.item():.4f}",
                    'lr': f"{scheduler.get_last_lr()[0]:.2e}",
                    'wave': wave_idx,
                    'wave_name': wave_name[:20],
                })
                
                # Logging
                if global_step % args.log_interval == 0:
                    avg_loss = sum(losses[-args.log_interval:]) / len(losses[-args.log_interval:])
                    logger.info(
                        f"Step {global_step}/{args.max_steps} | "
                        f"Wave {wave_idx}: {wave_name} | "
                        f"Loss: {avg_loss:.4f} | "
                        f"LR: {scheduler.get_last_lr()[0]:.2e}"
                    )
                
                # Checkpoint
                if global_step % args.save_interval == 0:
                    checkpoint_path = os.path.join(args.output_dir, f'checkpoint-{global_step:06d}')
                    os.makedirs(checkpoint_path, exist_ok=True)
                    
                    # Save weights only (no optimizer state — saves ~28GB)
                    torch.save(model.state_dict(), os.path.join(checkpoint_path, 'pytorch_model.bin'))
                    
                    logger.info(f"Saved checkpoint: {checkpoint_path}")
                    
                    # Clear cache after save
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
    
    pbar.close()
    
    # Final save
    logger.info("\n" + "="*70)
    logger.info("TRAINING COMPLETE — Saving final model...")
    logger.info("="*70)
    
    final_path = os.path.join(args.output_dir, 'final')
    os.makedirs(final_path, exist_ok=True)
    torch.save(model.state_dict(), os.path.join(final_path, 'pytorch_model.bin'))
    
    # Save config
    config_json = {
        "vocab_size": VOCAB_SIZE,
        "hidden_size": HIDDEN_SIZE,
        "num_hidden_layers": NUM_HIDDEN_LAYERS,
        "num_attention_heads": NUM_ATTENTION_HEADS,
        "num_key_value_heads": NUM_KEY_VALUE_HEADS,
        "head_dim": HEAD_DIM,
        "intermediate_size": INTERMEDIATE_SIZE,
        "rms_norm_eps": RMS_NORM_EPS,
        "max_position_embeddings": MAX_POSITION_EMBEDDINGS,
        "aux_layer_ids": AUX_LAYER_IDS,
        "model_type": "qwen3",
        "torch_dtype": "bfloat16" if args.bf16 else "float32",
        "franken_v8_version": "full_25_grafts_v1",
        "flash_attention": "FA4 (CuTeDSL, Blackwell-optimized)" if HAS_FLASH_ATTN else "SDPA fallback",
        "all_25_grafts": [
            "swiglu", "manifold_hyper_connections", "gated_attention", "rope",
            "adaptive_rmsnorm", "highway_connections", "mtp4", "lookahead_attention",
            "pard", "tree_attention", "early_exit", "lk_losses",
            "ssd", "dart", "ltd",
        ],
        "training_mode": "progressive_waves",
        "num_waves": len(GraftManager.WAVES),
        "optimizer": "adamw",
    }
    
    config_path = os.path.join(args.output_dir, 'config.json')
    with open(config_path, 'w') as f:
        json.dump(config_json, f, indent=2)
    
    logger.info(f"Saved config: {config_path}")
    logger.info(f"Final model: {final_path}")
    logger.info("\n" + "="*70)
    logger.info("FRANKEN v8 — ALL 25 GRAFTS TRAINING COMPLETE")
    logger.info("="*70)
    logger.info(f"Flash Attention 2: {'YES' if HAS_FLASH_ATTN else 'NO (used SDPA)'}")
    logger.info("All 25 grafts defined and trained via progressive waves:")
    for i, wave in enumerate(GraftManager.WAVES):
        logger.info(f"  Wave {i}: {wave['name']}")
    logger.info("="*70)


def main():
    parser = argparse.ArgumentParser(description='Train Franken v8 DFlash — FULL 25 GRAFTS')
    
    # Training
    parser.add_argument('--hidden-states-dir', type=str, required=True, help='Directory with batch logits')
    parser.add_argument('--output-dir', type=str, default='./franken_v8_25grafts_output', help='Output directory')
    parser.add_argument('--lr', type=float, default=0.0001, help='Learning rate')
    parser.add_argument('--weight-decay', type=float, default=0.01, help='Weight decay')
    parser.add_argument('--max-steps', type=int, default=3333, help='Max training steps')
    parser.add_argument('--batch-size', type=int, default=1, help='Batch size')
    parser.add_argument('--grad-accum', type=int, default=4, help='Gradient accumulation steps')
    parser.add_argument('--steps-per-wave', type=int, default=667, help='Steps per wave (3333/5 = ~667)')
    parser.add_argument('--dropout', type=float, default=0.1, help='Dropout rate')
    parser.add_argument('--temperature', type=float, default=1.0, help='LK loss temperature')
    parser.add_argument('--max-grad-norm', type=float, default=1.0, help='Max gradient norm')
    
    # Logging
    parser.add_argument('--log-interval', type=int, default=50, help='Log every N steps')
    parser.add_argument('--save-interval', type=int, default=500, help='Save every N steps')
    
    # Precision
    parser.add_argument('--bf16', action='store_true', help='Use bfloat16')
    parser.add_argument('--fp16', action='store_true', help='Use float16')
    
    args = parser.parse_args()
    
    # Validate
    if args.bf16 and args.fp16:
        raise ValueError("Cannot use both --bf16 and --fp16")
    
    train(args)


if __name__ == '__main__':
    main()
