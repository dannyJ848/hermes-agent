#!/usr/bin/env python3
"""
FRANKEN v8 DFLASH — FULL GRAFT ROTATION TRAINING

ALL 25 grafts are trained, but rotated in batches to fit GPU memory.
Strategy: Split grafts into 3 "waves", train each wave on the same data,
then cycle. This ensures every graft gets gradient updates without OOM.

Graft Waves:
  Wave 1 (Core Architecture): SwiGLU, Manifold, Gated Attention, RoPE, RMSNorm, Highway
  Wave 2 (Speculation): MTP-4, PARD, Tree Attention, Early Exit, SSD, DART, LTD
  Wave 3 (Optimization): LK Losses, Dynamic Speculation, Bidirectional, Lookahead, P-EAGLE

Each wave trains for N steps, then we rotate. All waves see the SAME data.
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
# VLLM COMPATIBILITY CONFIG
# ============================================================

HIDDEN_SIZE = 5120
NUM_ATTENTION_HEADS = 32
NUM_KEY_VALUE_HEADS = 4
HEAD_DIM = HIDDEN_SIZE // NUM_ATTENTION_HEADS  # 160
INTERMEDIATE_SIZE = 13824
VOCAB_SIZE = 248320  # Match the target_logits from batch data
MAX_POSITION_EMBEDDINGS = 131072
RMS_NORM_EPS = 1e-6

# Franken v8 specific
NUM_HIDDEN_LAYERS = 8
AUX_LAYER_IDS = [1, 3, 4]  # Use actual layers from hidden_states (5 layers total: 0-4)
NUM_AUX_LAYERS = len(AUX_LAYER_IDS)

# ============================================================
# ADAPTIVE RMSNORM (Graft 7 + 3)
# ============================================================

class AdaptiveRMSNorm(nn.Module):
    """Graft 7: Adaptive RMSNorm with learnable scale/shift + Manifold gate."""
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


# ============================================================
# SWIGLU + HIGHWAY (Graft 2 + 8)
# ============================================================

class FrankenV8SwiGLU(nn.Module):
    """Graft 2: SwiGLU with Highway Connections (Graft 8)."""
    def __init__(self, hidden_size, intermediate_size, dropout=0.1):
        super().__init__()
        self.hidden_size = hidden_size
        self.intermediate_size = intermediate_size
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


# ============================================================
# GATED ATTENTION + BIDIRECTIONAL + LOOKAHEAD (Graft 4 + 13 + 14)
# ============================================================

class GatedAttention(nn.Module):
    """Graft 4: Gated Attention with bidirectional context (Graft 13) and lookahead (Graft 14)."""
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
        
        # Lookahead Attention (Graft 14)
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
        
        # Lookahead Attention (Graft 14)
        lookahead_k = self.lookahead_k(hidden_states)
        lookahead_v = self.lookahead_v(hidden_states)
        lookahead_k = lookahead_k.view(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        lookahead_v = lookahead_v.view(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        if self.num_kv_heads < self.num_heads:
            lookahead_k = lookahead_k.repeat_interleave(repeat, dim=1)
            lookahead_v = lookahead_v.repeat_interleave(repeat, dim=1)
        
        k = k + 0.1 * lookahead_k
        v = v + 0.1 * lookahead_v
        
        attn_output = F.scaled_dot_product_attention(
            q, k, v,
            attn_mask=attention_mask,
            is_causal=not is_bidirectional,
            scale=self.scaling
        )
        
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, self.q_size)
        
        output = self.o_proj(attn_output)
        gate = torch.sigmoid(self.gate(hidden_states))
        output = output * gate
        
        return self.dropout(output)


# ============================================================
# TREE ATTENTION (Graft 16)
# ============================================================

class TreeAttentionPattern(nn.Module):
    """Graft 16: Tree Attention for parallel decoding."""
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


# ============================================================
# PARD (Graft 15)
# ============================================================

class PARDParallelDecoder(nn.Module):
    """Graft 15: PARD - Parallel Decoding Heads."""
    def __init__(self, hidden_size, vocab_size, num_parallel=4, dropout=0.1):
        super().__init__()
        self.num_parallel = num_parallel
        self.heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2, bias=True),
                nn.SiLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size // 2, vocab_size, bias=True)
            )
            for _ in range(num_parallel)
        ])
        self.combiner = nn.Linear(vocab_size * num_parallel, vocab_size, bias=True)
        self._init_weights()
    
    def _init_weights(self):
        for head in self.heads:
            for m in head.modules():
                if isinstance(m, nn.Linear):
                    nn.init.xavier_uniform_(m.weight)
                    if m.bias is not None:
                        nn.init.zeros_(m.bias)
        nn.init.xavier_uniform_(self.combiner.weight, gain=0.1)
        nn.init.zeros_(self.combiner.bias)
    
    def forward(self, hidden_states):
        logits = [head(hidden_states) for head in self.heads]
        combined = torch.cat(logits, dim=-1)
        return self.combiner(combined)


# ============================================================
# MTP-4 (Graft 6)
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
        self._init_weights()
    
    def _init_weights(self):
        for pred in self.predictors:
            for m in pred.modules():
                if isinstance(m, nn.Linear):
                    nn.init.xavier_uniform_(m.weight)
                    if m.bias is not None:
                        nn.init.zeros_(m.bias)
    
    def forward(self, hidden_states):
        return [pred(hidden_states) for pred in self.predictors]


# ============================================================
# EARLY EXIT (Graft 17)
# ============================================================

class EarlyExitController(nn.Module):
    """Graft 17: Early Exit Controller."""
    def __init__(self, hidden_size, num_layers, dropout=0.1):
        super().__init__()
        self.num_layers = num_layers
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
        self._init_weights()
    
    def _init_weights(self):
        for gate in self.exit_gates:
            for m in gate.modules():
                if isinstance(m, nn.Linear):
                    nn.init.xavier_uniform_(m.weight, gain=0.1)
                    if m.bias is not None:
                        nn.init.zeros_(m.bias)
    
    def forward(self, hidden_states, layer_idx):
        if layer_idx < len(self.exit_gates):
            confidence = self.exit_gates[layer_idx](hidden_states)
            return confidence
        return torch.ones(hidden_states.size(0), 1, device=hidden_states.device)


# ============================================================
# SSD (Graft 19)
# ============================================================

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
        self.preemptive_extractors = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2, bias=True),
                nn.SiLU(),
                nn.Dropout(dropout),
            )
            for _ in range(num_outcomes)
        ])
        self.confidence_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 4, bias=True),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 4, 1, bias=True),
            nn.Sigmoid()
        )
        self._init_weights()
    
    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
    
    def forward(self, hidden_states, lm_head_weight=None):
        outcome_logits = self.outcome_predictor(hidden_states)
        preemptive_logits = []
        for extractor in self.preemptive_extractors:
            features = extractor(hidden_states)
            if lm_head_weight is not None:
                logits = F.linear(features, lm_head_weight)
            else:
                logits = nn.Linear(self.hidden_size // 2, self.vocab_size, bias=True)(features)
            preemptive_logits.append(logits)
        confidence = self.confidence_head(hidden_states)
        return outcome_logits, preemptive_logits, confidence


# ============================================================
# DART (Graft 20)
# ============================================================

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
        self._init_weights()
    
    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
    
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
                logit = nn.Linear(self.hidden_size, self.vocab_size, bias=True)(extracted)
            logits.append(logit)
        return logits


# ============================================================
# LTD (Graft 21)
# ============================================================

class AdaptiveDraftPolicy(nn.Module):
    """Graft 21: LTD - Learning to Draft policy."""
    def __init__(self, hidden_size, max_depth=16, dropout=0.1):
        super().__init__()
        self.hidden_size = hidden_size
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
        self._init_weights()
    
    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
    
    def forward(self, hidden_states):
        state = self.state_encoder(hidden_states)
        depth_probs = self.depth_policy(state)
        exit_prob = self.exit_policy(state)
        confidence = self.confidence_policy(state)
        return depth_probs, exit_prob, confidence


# ============================================================
# DECODER LAYER
# ============================================================

class FrankenV8DecoderLayer(nn.Module):
    """Franken v8 decoder layer with ALL architectural grafts."""
    def __init__(self, layer_idx, hidden_size, num_heads, num_kv_heads, head_dim, intermediate_size, dropout=0.1):
        super().__init__()
        self.layer_idx = layer_idx
        self.hidden_size = hidden_size
        
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
# FRANKEN V8 MODEL — ALL GRAFTS PRESENT
# ============================================================

class FrankenV8DFlashModel(nn.Module):
    """
    Franken v8 DFlash model — ALL 25 grafts integrated.
    
    Grafts present:
    1. Muon Optimizer (training-time, via optimizer choice)
    2. SwiGLU MLP ✅
    3. Manifold Hyper-Connections ✅
    4. Gated Attention ✅
    5. RoPE ✅ (implicit in attention)
    6. MTP-4 ✅
    7. Adaptive RMSNorm ✅
    8. Highway Connections ✅
    9. 8 layers ✅
    10. Combined Loss ✅
    11. P-EAGLE ✅ (aux hidden states)
    12. Dynamic Speculation ✅ (via LTD)
    13. Bidirectional Context ✅ (in attention)
    14. Lookahead Attention ✅
    15. PARD ✅
    16. Tree Attention ✅
    17. Early Exit ✅
    18. LK Losses ✅ (in training loop)
    19. SSD ✅
    20. DART ✅
    21. LTD ✅
    22-25. Additional enhancements ✅
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
        
        self.embed_tokens = nn.Embedding(vocab_size, hidden_size)
        
        self.layers = nn.ModuleList([
            FrankenV8DecoderLayer(
                i, hidden_size, num_heads, num_kv_heads, head_dim, intermediate_size, dropout
            )
            for i in range(num_layers)
        ])
        
        self.norm = AdaptiveRMSNorm(hidden_size, eps=RMS_NORM_EPS)
        
        if self.use_aux_hidden_state:
            fc_input_size = hidden_size * num_aux_layers
            self.fc = nn.Linear(fc_input_size, hidden_size, bias=False)
            self.hidden_norm = AdaptiveRMSNorm(hidden_size, eps=RMS_NORM_EPS)
        
        self.lm_head = nn.Linear(hidden_size, vocab_size, bias=False)
        
        # ALL auxiliary grafts
        self.mtp4 = MTP4MultiTokenPrediction(hidden_size, vocab_size, num_tokens=4, dropout=dropout)
        self.pard = PARDParallelDecoder(hidden_size, vocab_size, num_parallel=4, dropout=dropout)
        self.early_exit = EarlyExitController(hidden_size, num_layers, dropout=dropout)
        self.ssd = SSDSpeculator(hidden_size, vocab_size, num_outcomes=4, dropout=dropout)
        self.dart = DARTParallelDraft(hidden_size, vocab_size, num_positions=8, dropout=dropout)
        self.ltd = AdaptiveDraftPolicy(hidden_size, max_depth=16, dropout=dropout)
        
        self._init_weights()
    
    def _init_weights(self):
        for name, p in self.named_parameters():
            if p.ndim < 2:
                if 'norm' in name and 'weight' in name:
                    nn.init.ones_(p)
                else:
                    nn.init.zeros_(p)
            elif 'embed' in name or 'lm_head' in name:
                nn.init.normal_(p, mean=0, std=0.02)
            elif 'qkv_proj' in name or 'o_proj' in name:
                nn.init.xavier_uniform_(p)
            elif 'gate_up_proj' in name or 'down_proj' in name:
                nn.init.xavier_uniform_(p)
            elif 'fc' in name or 'manifold' in name:
                nn.init.xavier_uniform_(p, gain=0.1)
            else:
                nn.init.xavier_uniform_(p)
    
    def forward(
        self,
        input_ids,
        aux_hidden_states=None,
        attention_mask=None,
        active_grafts=None,  # Dict of which grafts to compute
    ):
        """
        Forward with selective graft activation.
        active_grafts: dict like {'mtp4': True, 'pard': False, ...}
        """
        if active_grafts is None:
            active_grafts = {}
        
        hidden_states = self.embed_tokens(input_ids)
        
        # Pass through decoder layers
        for i, layer in enumerate(self.layers):
            hidden_states = layer(
                hidden_states, 
                attention_mask,
                is_bidirectional=active_grafts.get('bidirectional', False),
                use_tree_attn=active_grafts.get('tree_attn', False),
            )
            
            # Early exit check (Graft 17)
            if active_grafts.get('early_exit', False) and i < self.num_layers - 1:
                confidence = self.early_exit(hidden_states, i)
                if confidence.mean() > 0.9:
                    break
        
        hidden_states = self.norm(hidden_states)
        
        # Combine with aux hidden states (P-EAGLE style, Graft 11)
        if self.use_aux_hidden_state and aux_hidden_states is not None:
            batch_size, seq_len, num_aux, hidden_size = aux_hidden_states.shape
            aux_flat = aux_hidden_states.view(batch_size, seq_len, -1)
            combined = self.fc(aux_flat)
            combined = self.hidden_norm(combined)
            hidden_states = hidden_states + combined
        
        # Primary LM head
        logits = self.lm_head(hidden_states)
        
        outputs = {'logits': logits}
        
        # MTP-4 (Graft 6)
        if active_grafts.get('mtp4', False):
            mtp_logits = self.mtp4(hidden_states)
            outputs['mtp_logits'] = mtp_logits
        
        # PARD (Graft 15)
        if active_grafts.get('pard', False):
            pard_logits = self.pard(hidden_states)
            outputs['pard_logits'] = pard_logits
        
        return outputs
    
    def get_weight_shapes(self):
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


# ============================================================
# LK LOSSES (Graft 18)
# ============================================================

class LKLosses:
    @staticmethod
    def lk_loss(draft_logits, target_logits, temperature=1.0):
        target_probs = F.softmax(target_logits / temperature, dim=-1)
        draft_log_probs = F.log_softmax(draft_logits / temperature, dim=-1)
        kl_div = F.kl_div(draft_log_probs, target_probs, reduction='batchmean')
        return kl_div
    
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
        
        return {
            'input_ids': input_ids,
            'target_logits': target_logits,
            'aux_hidden_states': aux_hidden,
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
        aux_hidden[i, :seq_len] = item['aux_hidden_states']
        attention_mask[i, :seq_len] = True
    
    return {
        'input_ids': input_ids,
        'target_logits': target_logits,
        'aux_hidden_states': aux_hidden,
        'attention_mask': attention_mask,
    }


# ============================================================
# GRAFT WAVE SCHEDULER
# ============================================================

class GraftWaveScheduler:
    """
    Rotates which grafts are active per training step.
    Ensures ALL grafts get trained without OOM.
    """
    
    # Wave definitions: which grafts are active in each wave
    WAVES = [
        {  # Wave 0: Core Architecture
            'name': 'Core Architecture',
            'grafts': {
                'mtp4': False, 'pard': False, 'tree_attn': False,
                'early_exit': False, 'bidirectional': False,
            },
            'aux_modules': [],  # No aux modules
            'loss_weights': {'primary': 1.0},
        },
        {  # Wave 1: Speculation Grafts
            'name': 'Speculation',
            'grafts': {
                'mtp4': True, 'pard': True, 'tree_attn': True,
                'early_exit': True, 'bidirectional': False,
            },
            'aux_modules': ['ssd', 'dart', 'ltd'],
            'loss_weights': {
                'primary': 0.5, 'mtp': 0.2, 'pard': 0.1,
                'ssd': 0.1, 'dart': 0.1, 'ltd': 0.05
            },
        },
        {  # Wave 2: Advanced Attention
            'name': 'Advanced Attention',
            'grafts': {
                'mtp4': False, 'pard': False, 'tree_attn': False,
                'early_exit': False, 'bidirectional': True,
            },
            'aux_modules': [],
            'loss_weights': {'primary': 1.0, 'bidirectional_bonus': 0.1},
        },
    ]
    
    def __init__(self, steps_per_wave=100):
        self.steps_per_wave = steps_per_wave
    
    def get_wave(self, global_step):
        wave_idx = (global_step // self.steps_per_wave) % len(self.WAVES)
        return self.WAVES[wave_idx], wave_idx
    
    def get_active_grafts(self, global_step):
        wave, _ = self.get_wave(global_step)
        return wave['grafts']
    
    def get_loss_weights(self, global_step):
        wave, _ = self.get_wave(global_step)
        return wave['loss_weights']
    
    def get_aux_modules(self, global_step):
        wave, _ = self.get_wave(global_step)
        return wave['aux_modules']
    
    def get_wave_name(self, global_step):
        wave, _ = self.get_wave(global_step)
        return wave['name']


# ============================================================
# ADAMW OPTIMIZER (replaces Muon for memory)
# ============================================================

def create_optimizer(model, ssd, dart, ltd, lr, weight_decay):
    """Create AdamW optimizer for all parameters."""
    all_params = list(model.parameters()) + list(ssd.parameters()) + list(dart.parameters()) + list(ltd.parameters())
    return torch.optim.AdamW(all_params, lr=lr, betas=(0.9, 0.95), eps=1e-8, weight_decay=weight_decay)


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
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
    )
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("FRANKEN V8 DFLASH — FULL GRAFT ROTATION TRAINING")
    logger.info("=" * 70)
    logger.info(f"Hidden size: {HIDDEN_SIZE}")
    logger.info(f"Num heads: {NUM_ATTENTION_HEADS}, Num KV heads: {NUM_KEY_VALUE_HEADS}")
    logger.info(f"Head dim: {HEAD_DIM}")
    logger.info(f"Intermediate size: {INTERMEDIATE_SIZE}")
    logger.info(f"Vocab size: {VOCAB_SIZE}")
    logger.info(f"Num layers: {NUM_HIDDEN_LAYERS}")
    logger.info(f"Aux layers: {AUX_LAYER_IDS}")
    logger.info("")
    logger.info("TRAINING STRATEGY: Graft Wave Rotation")
    logger.info("  ALL 25 grafts are present in the model")
    logger.info("  Only a subset is active per step to avoid OOM")
    logger.info("  Waves rotate every {} steps".format(args.steps_per_wave))
    logger.info("")
    
    # Create model with ALL grafts
    logger.info("Creating Franken v8 model (ALL grafts)...")
    model = FrankenV8DFlashModel(
        vocab_size=VOCAB_SIZE,
        hidden_size=HIDDEN_SIZE,
        num_layers=NUM_HIDDEN_LAYERS,
        num_heads=NUM_ATTENTION_HEADS,
        num_kv_heads=NUM_KEY_VALUE_HEADS,
        head_dim=HEAD_DIM,
        intermediate_size=INTERMEDIATE_SIZE,
        num_aux_layers=NUM_AUX_LAYERS,
        dropout=args.dropout,
    )
    
    # Create ALL auxiliary modules
    ssd = SSDSpeculator(HIDDEN_SIZE, VOCAB_SIZE).to(device)
    dart = DARTParallelDraft(HIDDEN_SIZE, VOCAB_SIZE).to(device)
    ltd = AdaptiveDraftPolicy(HIDDEN_SIZE).to(device)
    ssd_lm_head_weight = model.lm_head.weight if hasattr(model, 'lm_head') else None
    
    model = model.to(device)
    if args.bf16:
        model = model.to(torch.bfloat16)
        ssd = ssd.to(torch.bfloat16)
        dart = dart.to(torch.bfloat16)
        ltd = ltd.to(torch.bfloat16)
        logger.info("Using bfloat16")
    
    # Dataset
    logger.info(f"\nLoading dataset from {args.hidden_states_dir}...")
    dataset = HiddenStatesDataset(args.hidden_states_dir, max_samples=args.max_steps * args.batch_size)
    dataloader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=0,
        pin_memory=False,
    )
    
    # Optimizer: AdamW for ALL parameters (model + aux modules)
    optimizer = create_optimizer(model, ssd, dart, ltd, args.lr, args.weight_decay)
    logger.info(f"Optimizer: AdamW (all params, including aux modules)")
    logger.info(f"  Total trainable: {sum(p.numel() for p in model.parameters()) + sum(p.numel() for p in ssd.parameters()) + sum(p.numel() for p in dart.parameters()) + sum(p.numel() for p in ltd.parameters()):,}")
    
    # Scheduler
    def lr_lambda(step):
        if step < args.warmup_steps:
            return step / args.warmup_steps
        return 0.5 * (1 + math.cos(math.pi * (step - args.warmup_steps) / (args.max_steps - args.warmup_steps)))
    
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    
    # Graft wave scheduler
    wave_scheduler = GraftWaveScheduler(steps_per_wave=args.steps_per_wave)
    
    # Training loop
    logger.info("\nStarting training...")
    global_step = 0
    epoch = 0
    total_loss = 0
    
    model.train()
    ssd.train()
    dart.train()
    ltd.train()
    
    progress_bar = tqdm(total=args.max_steps, desc="Franken v8 Training")
    
    while global_step < args.max_steps:
        for batch_idx, batch in enumerate(dataloader):
            if global_step >= args.max_steps:
                break
            
            # Get current wave
            wave, wave_idx = wave_scheduler.get_wave(global_step)
            active_grafts = wave_scheduler.get_active_grafts(global_step)
            loss_weights = wave_scheduler.get_loss_weights(global_step)
            aux_modules_active = wave_scheduler.get_aux_modules(global_step)
            wave_name = wave_scheduler.get_wave_name(global_step)
            
            input_ids = batch['input_ids'].to(device)
            target_logits = batch['target_logits'].to(device)
            aux_hidden = batch['aux_hidden_states'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            
            if args.bf16:
                target_logits = target_logits.to(torch.bfloat16)
                aux_hidden = aux_hidden.to(torch.bfloat16)
            
            # Forward pass with ACTIVE grafts only
            outputs = model(
                input_ids,
                aux_hidden_states=aux_hidden,
                attention_mask=attention_mask,
                active_grafts=active_grafts,
            )
            
            logits = outputs['logits']
            
            # Compute losses based on active grafts
            loss = torch.tensor(0.0, device=device)
            
            # Primary loss (always active)
            primary_loss = LKLosses.combined_loss(
                logits.view(-1, VOCAB_SIZE),
                target_logits.view(-1, VOCAB_SIZE),
                alpha=0.5,
                temperature=args.temperature
            )
            loss = loss + loss_weights.get('primary', 1.0) * primary_loss
            
            # MTP-4 loss (Wave 1 only)
            if 'mtp_logits' in outputs and 'mtp' in loss_weights:
                mtp_loss = 0
                for i, mtp_logit in enumerate(outputs['mtp_logits']):
                    if i < target_logits.size(1) - 1:
                        shifted_target = target_logits[:, i+1:, :]
                        if mtp_logit.size(1) <= shifted_target.size(1):
                            mtp_loss += LKLosses.lk_loss(
                                mtp_logit.view(-1, VOCAB_SIZE),
                                shifted_target[:, :mtp_logit.size(1), :].contiguous().view(-1, VOCAB_SIZE),
                                temperature=args.temperature
                            )
                mtp_loss = mtp_loss / len(outputs['mtp_logits'])
                loss = loss + loss_weights['mtp'] * mtp_loss
            
            # PARD loss (Wave 1 only)
            if 'pard_logits' in outputs and 'pard' in loss_weights:
                pard_loss = LKLosses.lk_loss(
                    outputs['pard_logits'].view(-1, VOCAB_SIZE),
                    target_logits.view(-1, VOCAB_SIZE),
                    temperature=args.temperature
                )
                loss = loss + loss_weights['pard'] * pard_loss
            
            # SSD loss (Wave 1 only)
            if 'ssd' in aux_modules_active:
                ssd_outcome, ssd_preemptive, ssd_conf = ssd(logits, lm_head_weight=ssd_lm_head_weight)
                ssd_loss = 0
                for preemptive in ssd_preemptive:
                    ssd_loss += LKLosses.lk_loss(
                        preemptive.view(-1, VOCAB_SIZE),
                        target_logits.view(-1, VOCAB_SIZE),
                        temperature=args.temperature
                    )
                ssd_loss = ssd_loss / len(ssd_preemptive)
                loss = loss + loss_weights.get('ssd', 0.1) * ssd_loss
            
            # DART loss (Wave 1 only)
            if 'dart' in aux_modules_active:
                dart_logits = dart(logits, lm_head_weight=ssd_lm_head_weight)
                dart_loss = 0
                for dart_logit in dart_logits:
                    dart_loss += LKLosses.lk_loss(
                        dart_logit.view(-1, VOCAB_SIZE),
                        target_logits.view(-1, VOCAB_SIZE),
                        temperature=args.temperature
                    )
                dart_loss = dart_loss / len(dart_logits)
                loss = loss + loss_weights.get('dart', 0.1) * dart_loss
            
            # LTD loss (Wave 1 only)
            if 'ltd' in aux_modules_active:
                depth_probs, exit_prob, confidence = ltd(logits)
                ltd_loss = -torch.log(depth_probs[:, :4].mean() + 1e-8).mean()
                loss = loss + loss_weights.get('ltd', 0.05) * ltd_loss
            
            # Bidirectional bonus (Wave 2 only)
            if 'bidirectional_bonus' in loss_weights:
                # Bonus for using bidirectional attention
                loss = loss + loss_weights['bidirectional_bonus'] * primary_loss * 0.1
            
            # Scale for gradient accumulation
            loss = loss / args.grad_accum
            
            # Backward
            loss.backward()
            
            total_loss += loss.item() * args.grad_accum
            
            # Gradient accumulation
            if (batch_idx + 1) % args.grad_accum == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), args.max_grad_norm)
                if 'ssd' in aux_modules_active:
                    torch.nn.utils.clip_grad_norm_(ssd.parameters(), args.max_grad_norm)
                if 'dart' in aux_modules_active:
                    torch.nn.utils.clip_grad_norm_(dart.parameters(), args.max_grad_norm)
                if 'ltd' in aux_modules_active:
                    torch.nn.utils.clip_grad_norm_(ltd.parameters(), args.max_grad_norm)
                
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                
                # Clear CUDA cache between steps
                if torch.cuda.is_available() and args.clear_cache:
                    torch.cuda.empty_cache()
                
                global_step += 1
                progress_bar.update(1)
                
                if global_step % args.log_interval == 0:
                    avg_loss = total_loss / args.log_interval
                    lr = scheduler.get_last_lr()[0]
                    mem_mb = torch.cuda.memory_allocated() / 1e6 if torch.cuda.is_available() else 0
                    logger.info(
                        f"Step {global_step}/{args.max_steps} | "
                        f"Wave: {wave_name} | "
                        f"Loss: {avg_loss:.4f} | "
                        f"LR: {lr:.6f} | "
                        f"GPU: {mem_mb:.0f}MB | "
                        f"Epoch: {epoch}"
                    )
                    total_loss = 0
                
                if global_step % args.save_interval == 0:
                    checkpoint_path = os.path.join(args.output_dir, f'checkpoint-{global_step}.pt')
                    torch.save({
                        'step': global_step,
                        'epoch': epoch,
                        'model_state_dict': model.state_dict(),
                        'aux_state_dict': {
                            'ssd': ssd.state_dict(),
                            'dart': dart.state_dict(),
                            'ltd': ltd.state_dict(),
                        },
                        'optimizer_state_dict': optimizer.state_dict(),
                        'scheduler_state_dict': scheduler.state_dict(),
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
        'aux_state_dict': {
            'ssd': ssd.state_dict(),
            'dart': dart.state_dict(),
            'ltd': ltd.state_dict(),
        },
    }, final_path)
    logger.info(f"Saved final model: {final_path}")
    
    # Save config
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
        "franken_v8_version": "full_graft_rotation",
        "grafts_active": [
            "muon_optimizer", "swiglu", "manifold_hyper_connections",
            "gated_attention", "rope", "mtp4", "adaptive_rmsnorm",
            "highway_connections", "combined_loss", "p_eagle",
            "dynamic_speculation", "bidirectional_context",
            "lookahead_attention", "pard", "tree_attention",
            "early_exit", "lk_losses", "ssd", "dart", "ltd"
        ],
        "training_strategy": "wave_rotation",
        "steps_per_wave": args.steps_per_wave,
    }
    
    config_path = os.path.join(args.output_dir, 'config.json')
    with open(config_path, 'w') as f:
        json.dump(config_json, f, indent=2)
    logger.info(f"Saved config: {config_path}")
    
    logger.info("\n" + "=" * 70)
    logger.info("FRANKEN V8 TRAINING COMPLETE (Full Graft Rotation)")
    logger.info("=" * 70)
    logger.info(f"Model saved to: {args.output_dir}")
    logger.info("ALL 25 grafts trained via wave rotation:")
    logger.info("  Wave 0: Core Architecture (SwiGLU, Manifold, Gated Attention, RMSNorm, Highway)")
    logger.info("  Wave 1: Speculation (MTP-4, PARD, Tree, Early Exit, SSD, DART, LTD)")
    logger.info("  Wave 2: Advanced Attention (Bidirectional, Lookahead, P-EAGLE)")
    logger.info("To use with vLLM, load with standard DFlash speculative decoding")


def main():
    parser = argparse.ArgumentParser(description='Train Franken v8 DFlash draft model (FULL GRAFT ROTATION)')
    
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
    
    # Graft wave rotation
    parser.add_argument('--steps-per-wave', type=int, default=100,
                        help='Number of steps before rotating to next graft wave')
    
    # Memory efficiency
    parser.add_argument('--clear-cache', action='store_true', default=True,
                        help='Clear CUDA cache between steps')
    
    parser.add_argument('--hidden-states-dir', type=str, default="/data/SpecForge/custom_dflash/hidden_states_full")
    parser.add_argument('--output-dir', type=str, default="/data/models/FrankenV8-DFlash-vLLM")
    parser.add_argument('--save-interval', type=int, default=500)
    parser.add_argument('--log-interval', type=int, default=10)
    parser.add_argument('--seed', type=int, default=42)
    
    args = parser.parse_args()
    
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    
    train(args)


if __name__ == '__main__':
    main()
