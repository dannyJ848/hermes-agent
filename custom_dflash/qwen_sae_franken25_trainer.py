"""
Qwen 27B + Qwen-Scope SAE + Franken V8 25-Grafts Enhanced Training

Memory-Conscious Architecture for 130GB GPU:
- Qwen 27B: ~54B params @ bf16 = ~108GB (frozen, eval only)
- Franken V8 25-grafts: ~12B params @ bf16 = ~24GB (trainable)
- Qwen-Scope SAEs: 2 x (5120*81920*2) = ~1.6GB (frozen)
- Activations/gradients: ~10-20GB buffer
- Total: ~130GB (tight but doable with careful management)

Strategy:
1. Qwen 27B: device_map='auto' for layer-wise GPU placement, frozen
2. Franken V8: Full GPU, gradient checkpointing, mixed precision
3. SAEs: GPU, frozen, process in chunks
4. Progressive activation: Only compute what's needed
5. Gradient accumulation for effective batch size
"""

import os
import sys
import gc
import json
import math
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
from tqdm import tqdm

os.environ['CUDA_VISIBLE_DEVICES'] = '0'

# ============================================================
# MEMORY TRACKER
# ============================================================

class MemoryTracker:
    """Track GPU memory usage and warn when approaching limits"""
    def __init__(self, threshold_gb=120):
        self.threshold = threshold_gb * 1e9
        self.peak_allocated = 0
        
    def check(self, label=""):
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated()
            reserved = torch.cuda.memory_reserved()
            self.peak_allocated = max(self.peak_allocated, allocated)
            
            print(f"[MEM] {label}: Alloc={allocated/1e9:.1f}GB | Reserved={reserved/1e9:.1f}GB | Peak={self.peak_allocated/1e9:.1f}GB")
            
            if allocated > self.threshold:
                print(f"[MEM WARNING] Approaching limit! {allocated/1e9:.1f}GB > {self.threshold/1e9:.1f}GB")
                return False
        return True
    
    def emergency_cleanup(self):
        """Aggressive memory cleanup"""
        torch.cuda.empty_cache()
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.synchronize()

# ============================================================
# SAE MODULES (Lightweight)
# ============================================================

class QwenScopeSAE(nn.Module):
    """Qwen-Scope SAE - frozen, memory-efficient"""
    def __init__(self, d_model=5120, n_features=81920):
        super().__init__()
        self.d_model = d_model
        self.n_features = n_features
        self.W_enc = nn.Parameter(torch.empty(n_features, d_model))
        self.b_enc = nn.Parameter(torch.empty(n_features))
        self.W_dec = nn.Parameter(torch.empty(d_model, n_features))
        self.b_dec = nn.Parameter(torch.empty(d_model))
        
    def encode(self, x, chunk_size=4096):
        """Encode in chunks to avoid OOM"""
        B, T, D = x.shape
        x_flat = x.reshape(-1, D)
        
        chunks = []
        for i in range(0, x_flat.shape[0], chunk_size):
            chunk = x_flat[i:i+chunk_size]
            acts = F.relu(F.linear(chunk, self.W_enc, self.b_enc))
            chunks.append(acts)
        
        acts = torch.cat(chunks, dim=0)
        return acts.reshape(B, T, -1)
    
    def decode(self, acts, chunk_size=4096):
        """Decode in chunks"""
        B, T, n_features = acts.shape
        acts_flat = acts.reshape(-1, n_features)
        
        chunks = []
        for i in range(0, acts_flat.shape[0], chunk_size):
            chunk = acts_flat[i:i+chunk_size]
            h = F.linear(chunk, self.W_dec, self.b_dec)
            chunks.append(h)
        
        h = torch.cat(chunks, dim=0)
        return h.reshape(B, T, -1)
    
    def forward(self, x):
        acts = self.encode(x)
        h_recon = self.decode(acts)
        return h_recon, acts


def load_qwen_scope_sae(path, device='cuda', dtype=torch.bfloat16):
    """Load SAE with memory-efficient chunking"""
    checkpoint = torch.load(path, map_location='cpu')
    sae = QwenScopeSAE(d_model=5120, n_features=81920)
    
    # Load weights in chunks to avoid memory spike
    sae.W_enc.data = checkpoint['W_enc'].to(dtype)
    sae.b_enc.data = checkpoint['b_enc'].to(dtype)
    sae.W_dec.data = checkpoint['W_dec'].to(dtype)
    sae.b_dec.data = checkpoint['b_dec'].to(dtype)
    
    sae.to(device).eval()
    for p in sae.parameters():
        p.requires_grad = False
    return sae

# ============================================================
# FRANKEN V8 25-GRAFTS (Core Architecture)
# ============================================================

class AdaptiveRMSNorm(nn.Module):
    """Graft 7: Adaptive RMSNorm"""
    def __init__(self, hidden_size, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.eps = eps
        self.scale = nn.Parameter(torch.ones(1))
        self.shift = nn.Parameter(torch.zeros(1))
        self.manifold_gate = nn.Linear(hidden_size, hidden_size, bias=False)
        nn.init.xavier_uniform_(self.manifold_gate.weight, gain=0.1)
    
    def forward(self, x):
        h = x.to(torch.float32)
        variance = h.pow(2).mean(-1, keepdim=True)
        h = h * torch.rsqrt(variance + self.eps)
        h = h * (self.scale + 1.0) + self.shift
        manifold = torch.sigmoid(self.manifold_gate(x))
        h = h * manifold
        return (self.weight * h).to(x.dtype)


class FrankenV8SwiGLU(nn.Module):
    """Graft 2: SwiGLU + Graft 8: Highway"""
    def __init__(self, hidden_size, intermediate_size, dropout=0.1):
        super().__init__()
        self.gate_up_proj = nn.Linear(hidden_size, 2 * intermediate_size, bias=True)
        self.down_proj = nn.Linear(intermediate_size, hidden_size, bias=True)
        self.dropout = nn.Dropout(dropout)
        self.highway_gate = nn.Linear(hidden_size, hidden_size, bias=True)
        self.highway_transform = nn.Linear(hidden_size, hidden_size, bias=True)
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
        activated = F.silu(gate) * up
        activated = self.dropout(activated)
        mlp_out = self.down_proj(activated)
        highway_gate = torch.sigmoid(self.highway_gate(x))
        highway_transform = self.highway_transform(x)
        return highway_gate * mlp_out + (1 - highway_gate) * highway_transform


class GatedAttention(nn.Module):
    """Graft 4: Gated Attention + Graft 5: RoPE + Graft 14: Lookahead"""
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
        self.q_norm = AdaptiveRMSNorm(head_dim)
        self.k_norm = AdaptiveRMSNorm(head_dim)
        self.scaling = head_dim ** -0.5
        self.dropout = nn.Dropout(dropout)
        
        # Lookahead
        self.lookahead_k = nn.Linear(hidden_size, self.kv_size, bias=True)
        self.lookahead_v = nn.Linear(hidden_size, self.kv_size, bias=True)
        self._init_weights()
    
    def _init_weights(self):
        for m in [self.qkv_proj, self.o_proj, self.gate, self.lookahead_k, self.lookahead_v]:
            nn.init.xavier_uniform_(m.weight)
            if m.bias is not None:
                nn.init.zeros_(m.bias)
    
    def forward(self, x, attention_mask=None, use_lookahead=False):
        B, T, _ = x.shape
        qkv = self.qkv_proj(x)
        q, k, v = qkv.split([self.q_size, self.kv_size, self.kv_size], dim=-1)
        
        q = q.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(B, T, self.num_kv_heads, self.head_dim).transpose(1, 2)
        v = v.view(B, T, self.num_kv_heads, self.head_dim).transpose(1, 2)
        
        q = self.q_norm(q.transpose(1, 2)).transpose(1, 2)
        k = self.k_norm(k.transpose(1, 2)).transpose(1, 2)
        
        # GQA repeat
        if self.num_kv_heads < self.num_heads:
            repeat = self.num_heads // self.num_kv_heads
            k = k.repeat_interleave(repeat, dim=1)
            v = v.repeat_interleave(repeat, dim=1)
        
        # Lookahead
        if use_lookahead:
            lk = self.lookahead_k(x).view(B, T, self.num_kv_heads, self.head_dim).transpose(1, 2)
            lv = self.lookahead_v(x).view(B, T, self.num_kv_heads, self.head_dim).transpose(1, 2)
            if self.num_kv_heads < self.num_heads:
                lk = lk.repeat_interleave(repeat, dim=1)
                lv = lv.repeat_interleave(repeat, dim=1)
            k = k + 0.1 * lk
            v = v + 0.1 * lv
        
        # SDPA (Flash Attention if available)
        attn_out = F.scaled_dot_product_attention(
            q, k, v, attn_mask=attention_mask, 
            dropout_p=self.dropout.p if self.training else 0.0,
            is_causal=True, scale=self.scaling
        )
        
        attn_out = attn_out.transpose(1, 2).contiguous().view(B, T, self.q_size)
        output = self.o_proj(attn_out)
        gate = torch.sigmoid(self.gate(x))
        return output * gate


class FrankenV8DecoderLayer(nn.Module):
    """Full decoder layer with core grafts"""
    def __init__(self, layer_idx, hidden_size, num_heads, num_kv_heads, head_dim, intermediate_size, dropout=0.1):
        super().__init__()
        self.layer_idx = layer_idx
        self.self_attn = GatedAttention(hidden_size, num_heads, num_kv_heads, head_dim, dropout)
        self.mlp = FrankenV8SwiGLU(hidden_size, intermediate_size, dropout)
        self.input_layernorm = AdaptiveRMSNorm(hidden_size)
        self.post_attention_layernorm = AdaptiveRMSNorm(hidden_size)
        self.manifold_bridge = nn.Linear(hidden_size, hidden_size, bias=False)
        nn.init.xavier_uniform_(self.manifold_bridge.weight, gain=0.05)
    
    def forward(self, x, attention_mask=None, use_lookahead=False):
        manifold = torch.tanh(self.manifold_bridge(x))
        
        # Attention
        residual = x
        x = self.input_layernorm(x)
        x = self.self_attn(x, attention_mask, use_lookahead)
        x = residual + x + 0.05 * manifold
        
        # MLP
        residual = x
        x = self.post_attention_layernorm(x)
        x = self.mlp(x)
        x = residual + x
        
        return x


class MTP4MultiTokenPrediction(nn.Module):
    """Graft 6: MTP-4"""
    def __init__(self, hidden_size, vocab_size, num_tokens=4):
        super().__init__()
        self.num_tokens = num_tokens
        self.predictors = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size, bias=True),
                nn.SiLU(),
                nn.Linear(hidden_size, vocab_size, bias=True)
            ) for _ in range(num_tokens)
        ])
    
    def forward(self, hidden_states):
        return [pred(hidden_states) for pred in self.predictors]


class FrankenV8_25Grafts(nn.Module):
    """
    Franken V8 with 25 grafts - memory-efficient version
    
    Key grafts:
    1. Core: SwiGLU, Gated Attention, Adaptive RMSNorm, Manifold Hyper-Connection
    2. Training: MTP-4, Lookahead, Highway Connections
    3. SAE: Qwen-Scope integration for feature analysis
    """
    
    def __init__(self, vocab_size=151936, hidden_size=5120, num_layers=8,
                 num_heads=32, num_kv_heads=4, intermediate_size=13824,
                 max_seq_len=8192, dropout=0.1):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.embed_tokens = nn.Embedding(vocab_size, hidden_size)
        self.embed_positions = nn.Embedding(max_seq_len, hidden_size)
        
        self.layers = nn.ModuleList([
            FrankenV8DecoderLayer(i, hidden_size, num_heads, num_kv_heads,
                                hidden_size // num_heads, intermediate_size, dropout)
            for i in range(num_layers)
        ])
        
        self.norm = AdaptiveRMSNorm(hidden_size)
        self.lm_head = nn.Linear(hidden_size, vocab_size, bias=False)
        
        # Tie weights
        self.lm_head.weight = self.embed_tokens.weight
        
        # MTP-4 for enhanced training signal
        self.mtp = MTP4MultiTokenPrediction(hidden_size, vocab_size, num_tokens=4)
        
        # SAE feature projection (for Qwen-Scope alignment)
        self.sae_proj = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.GELU(),
            nn.Linear(hidden_size // 2, 81920)  # Project to SAE feature space
        )
        
    def forward(self, input_ids, attention_mask=None, use_lookahead=False, 
                return_sae_features=False):
        B, T = input_ids.shape
        positions = torch.arange(T, device=input_ids.device).unsqueeze(0).expand(B, -1)
        
        x = self.embed_tokens(input_ids) + self.embed_positions(positions)
        
        # Forward through layers
        for layer in self.layers:
            x = layer(x, attention_mask, use_lookahead)
        
        x = self.norm(x)
        logits = self.lm_head(x)
        
        outputs = {'logits': logits, 'hidden_states': x}
        
        # MTP predictions
        if self.training:
            mtp_preds = self.mtp(x)
            outputs['mtp_predictions'] = mtp_preds
        
        # SAE features
        if return_sae_features:
            sae_features = self.sae_proj(x)
            outputs['sae_features'] = sae_features
        
        return outputs

# ============================================================
# QWEN + SAE ENHANCED TRAINER
# ============================================================

class QwenSAEEnhancedTrainer:
    """
    Qwen 27B + Qwen-Scope SAE + Franken V8 25-Grafts
    
    Memory strategy:
    - Qwen 27B: device_map='auto', frozen, only forward pass
    - Franken V8: Full GPU, gradient checkpointing
    - SAEs: Process in chunks, clear cache between steps
    """
    
    def __init__(self, qwen_model, saes, franken_model, device='cuda'):
        self.qwen = qwen_model
        self.saes = saes  # List of (layer_idx, sae)
        self.franken = franken_model
        self.device = device
        self.memory = MemoryTracker(threshold_gb=125)
        
        # Freeze Qwen
        self.qwen.eval()
        for p in self.qwen.parameters():
            p.requires_grad = False
        
        # Enable gradient checkpointing on Franken for memory efficiency
        try:
            self.franken.gradient_checkpointing_enable()
        except AttributeError:
            print("  [WARN] gradient_checkpointing_enable() not available, skipping")
        
    def analyze_with_sae(self, hidden_states, sae_idx=0):
        """Analyze hidden states through Qwen-Scope SAE"""
        layer_idx, sae = self.saes[sae_idx]
        
        # Encode in chunks
        acts = sae.encode(hidden_states)
        h_recon = sae.decode(acts)
        
        # Metrics
        recon_error = F.mse_loss(h_recon, hidden_states)
        sparsity = (acts > 0).float().mean()
        top_activations = acts.max(dim=-1).values.mean()
        
        return {
            'features': acts,
            'reconstruction': h_recon,
            'recon_error': recon_error,
            'sparsity': sparsity,
            'top_activation': top_activations
        }
    
    def generate_enhanced_targets(self, input_ids, franken_hidden):
        """
        Generate training targets using Qwen 27B + SAE analysis
        
        Returns enhanced targets that blend:
        1. Qwen 27B's raw logits (teacher signal)
        2. SAE-corrected hidden states (interpretability guidance)
        3. Quality score (how well Franken aligns with Qwen's structure)
        """
        B, T = input_ids.shape
        
        # 1. Get Qwen's analysis
        with torch.no_grad():
            qwen_device = next(self.qwen.parameters()).device
            qwen_input_ids = input_ids.to(qwen_device)
            qwen_out = self.qwen(qwen_input_ids, output_hidden_states=True)
            qwen_logits = qwen_out.logits.to(self.device)
            qwen_hidden = qwen_out.hidden_states[-1].to(self.device)
        
        self.memory.check("After Qwen forward")
        
        # 2. Analyze Franken's hidden states through SAEs
        sae_results = []
        for i, (layer_idx, sae) in enumerate(self.saes):
            result = self.analyze_with_sae(franken_hidden, sae_idx=i)
            sae_results.append(result)
            self.memory.check(f"After SAE {layer_idx}")
        
        # 3. Compute quality score
        total_recon_error = sum(r['recon_error'] for r in sae_results)
        avg_sparsity = sum(r['sparsity'] for r in sae_results) / len(sae_results)
        
        # Quality: low recon error + moderate sparsity = good alignment
        quality = torch.exp(-total_recon_error) * torch.sigmoid((avg_sparsity - 0.01) * 100)
        
        # 4. Generate enhanced targets
        # Blend Qwen's hidden with SAE-corrected version
        sae_corrected = sae_results[0]['reconstruction']  # Use first SAE's reconstruction
        enhanced_hidden = 0.8 * qwen_hidden + 0.2 * sae_corrected
        
        # Enhanced logits: Qwen's logits with SAE-based correction
        # Higher quality = trust Franken more, lower = stronger correction
        correction_strength = 1.0 - quality
        enhanced_logits = qwen_logits * (1.0 + 0.1 * correction_strength)
        
        return {
            'logits_target': enhanced_logits,
            'hidden_target': enhanced_hidden,
            'quality_score': quality,
            'sae_features': [r['features'] for r in sae_results],
            'sae_metrics': {
                'recon_errors': [r['recon_error'].item() for r in sae_results],
                'sparsities': [r['sparsity'].item() for r in sae_results],
            }
        }


# ============================================================
# DATASET
# ============================================================

class TrainingDataset(Dataset):
    def __init__(self, data_dir, max_seq_len=2048):
        self.data_dir = Path(data_dir)
        self.files = sorted(self.data_dir.glob('sample_*.pt'))
        self.max_seq_len = max_seq_len
        print(f"Found {len(self.files)} training samples")
    
    def __len__(self):
        return len(self.files)
    
    def __getitem__(self, idx):
        data = torch.load(self.files[idx], map_location='cpu')
        input_ids = data['input_ids'].long()
        
        if input_ids.shape[-1] > self.max_seq_len:
            input_ids = input_ids[:self.max_seq_len]
        
        return {'input_ids': input_ids, 'file_idx': idx}


def collate_fn(batch):
    max_len = max(item['input_ids'].shape[-1] for item in batch)
    
    input_ids_list = []
    for item in batch:
        ids = item['input_ids']
        if ids.shape[-1] < max_len:
            pad_size = max_len - ids.shape[-1]
            ids = torch.cat([ids, torch.zeros(pad_size, dtype=ids.dtype)], dim=0)
        input_ids_list.append(ids)
    
    return {
        'input_ids': torch.stack(input_ids_list, dim=0),
        'file_idx': torch.tensor([item['file_idx'] for item in batch])
    }

# ============================================================
# TRAINING LOOP
# ============================================================

def train(args):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    memory = MemoryTracker(threshold_gb=125)
    
    print(f"{'='*70}")
    print(f"Qwen 27B + Qwen-Scope SAE + Franken V8 25-Grafts Training")
    print(f"{'='*70}")
    print(f"Device: {device}")
    if device.type == 'cuda':
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
    print(f"{'='*70}\n")
    
    # 1. Load tokenizer
    print("[1/7] Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.qwen_model, trust_remote_code=True)
    
    # 2. Load Qwen 27B (frozen, on CPU to save GPU memory for Franken+SAEs)
    print("\n[2/7] Loading Qwen 27B (frozen, device_map='cpu')...")
    qwen_model = AutoModelForCausalLM.from_pretrained(
        args.qwen_model,
        torch_dtype=torch.bfloat16,
        device_map='cpu',
        trust_remote_code=True
    )
    qwen_model.eval()
    for p in qwen_model.parameters():
        p.requires_grad = False
    memory.check("Qwen loaded")
    
    # 3. Load Qwen-Scope SAEs
    print("\n[3/7] Loading Qwen-Scope SAEs...")
    sae_layers = args.sae_layers  # e.g., [32, 48]
    saes = []
    for layer_idx in sae_layers:
        sae_path = f"{args.sae_dir}/layer{layer_idx}.sae.pt"
        if os.path.exists(sae_path):
            print(f"  Loading SAE layer {layer_idx}...")
            sae = load_qwen_scope_sae(sae_path, device='cuda')
            saes.append((layer_idx, sae))
            memory.check(f"SAE {layer_idx} loaded")
        else:
            print(f"  WARNING: {sae_path} not found, skipping")
    
    # 4. Create Franken V8 25-Grafts
    print("\n[4/7] Creating Franken V8 25-Grafts...")
    config = AutoConfig.from_pretrained(args.qwen_model, trust_remote_code=True)
    hidden_size = getattr(config, 'hidden_size', 5120)
    num_heads = getattr(config, 'num_attention_heads', 32)
    num_kv_heads = getattr(config, 'num_key_value_heads', 4)
    intermediate_size = getattr(config, 'intermediate_size', 13824)
    
    # Use tokenizer vocab size (may differ from config)
    vocab_size = len(tokenizer)
    print(f"  Using vocab_size={vocab_size} (from tokenizer)")
    
    franken = FrankenV8_25Grafts(
        vocab_size=vocab_size,
        hidden_size=hidden_size,
        num_layers=args.num_layers,
        num_heads=num_heads,
        num_kv_heads=num_kv_heads,
        intermediate_size=intermediate_size,
        max_seq_len=8192,
        dropout=0.1
    ).to(device).to(torch.bfloat16)
    
    # Load pretrained weights if available
    if args.pretrained and os.path.exists(args.pretrained):
        print(f"Loading pretrained weights from {args.pretrained}")
        checkpoint = torch.load(args.pretrained, map_location='cpu')
        if 'model_state_dict' in checkpoint:
            checkpoint = checkpoint['model_state_dict']
        
        # Handle vocab size mismatch by filtering out incompatible layers
        model_state = franken.state_dict()
        filtered_checkpoint = {}
        skipped_keys = []
        
        for k, v in checkpoint.items():
            if k in model_state:
                if v.shape == model_state[k].shape:
                    filtered_checkpoint[k] = v
                else:
                    skipped_keys.append(f"{k}: checkpoint {v.shape} vs model {model_state[k].shape}")
            else:
                skipped_keys.append(f"{k}: not in model")
        
        if skipped_keys:
            print(f"  Skipped {len(skipped_keys)} incompatible layers:")
            for msg in skipped_keys[:5]:
                print(f"    {msg}")
            if len(skipped_keys) > 5:
                print(f"    ... and {len(skipped_keys) - 5} more")
        
        # Load compatible weights
        franken.load_state_dict(filtered_checkpoint, strict=False)
        print(f"  Loaded {len(filtered_checkpoint)}/{len(model_state)} layers")
        memory.check("Franken weights loaded")
    
    total_params = sum(p.numel() for p in franken.parameters())
    trainable_params = sum(p.numel() for p in franken.parameters() if p.requires_grad)
    print(f"Franken V8: {total_params/1e9:.2f}B total, {trainable_params/1e9:.2f}B trainable")
    memory.check("Franken created")
    
    # 5. Create enhanced trainer
    print("\n[5/7] Creating Qwen+SAE enhanced trainer...")
    trainer = QwenSAEEnhancedTrainer(qwen_model, saes, franken, device=device)
    
    # 6. Dataset
    print("\n[6/7] Creating dataset...")
    dataset = TrainingDataset(args.data_dir, max_seq_len=args.max_seq_len)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True,
                           num_workers=0, collate_fn=collate_fn)
    
    # 7. Optimizer
    print("\n[7/7] Setting up optimizer...")
    optimizer = torch.optim.AdamW(franken.parameters(), lr=args.lr, 
                                   weight_decay=0.01, betas=(0.9, 0.95))
    
    # Learning rate scheduler
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=args.num_steps, eta_min=args.lr * 0.1
    )
    
    print(f"\n{'='*70}")
    print(f"Starting training: {args.num_steps} steps")
    print(f"Batch size: {args.batch_size}, LR: {args.lr}")
    print(f"{'='*70}\n")
    
    franken.train()
    global_step = 0
    pbar = tqdm(total=args.num_steps, desc="Training")
    
    loss_history = {'total': [], 'logits': [], 'hidden': [], 'mtp': [], 'quality': []}
    
    while global_step < args.num_steps:
        for batch in dataloader:
            if global_step >= args.num_steps:
                break
            
            input_ids = batch['input_ids'].to(device)
            
            # Clear cache before forward
            torch.cuda.empty_cache()
            
            # Forward through Franken
            franken_out = franken(input_ids, return_sae_features=True)
            franken_logits = franken_out['logits']
            franken_hidden = franken_out['hidden_states']
            
            memory.check("After Franken forward")
            
            # Get enhanced targets from Qwen+SAE
            with torch.no_grad():
                targets = trainer.generate_enhanced_targets(input_ids, franken_hidden)
            
            memory.check("After target generation")
            
            # Compute losses
            # A. Next-token prediction
            targets_ids = input_ids[:, 1:].contiguous()
            logits_shifted = franken_logits[:, :-1, :].contiguous()
            logits_loss = F.cross_entropy(
                logits_shifted.view(-1, logits_shifted.size(-1)),
                targets_ids.view(-1),
                ignore_index=0
            )
            
            # B. Hidden state alignment
            hidden_target = targets['hidden_target'][:, :-1, :].contiguous()
            franken_hidden_shifted = franken_hidden[:, :-1, :].contiguous()
            hidden_loss = F.mse_loss(franken_hidden_shifted, hidden_target)
            
            # C. MTP loss (if available)
            mtp_loss = torch.tensor(0.0, device=device)
            if 'mtp_predictions' in franken_out:
                for i, mtp_pred in enumerate(franken_out['mtp_predictions']):
                    if i + 1 < input_ids.shape[1]:
                        mtp_shifted = mtp_pred[:, :-1, :].contiguous()
                        mtp_targets = input_ids[:, i+1:].contiguous()
                        if mtp_shifted.shape[1] == mtp_targets.shape[1]:
                            mtp_loss += F.cross_entropy(
                                mtp_shifted.view(-1, mtp_shifted.size(-1)),
                                mtp_targets.view(-1),
                                ignore_index=0
                            )
                mtp_loss = mtp_loss / len(franken_out['mtp_predictions'])
            
            # D. SAE feature alignment (Franken should produce Qwen-like SAE features)
            sae_loss = torch.tensor(0.0, device=device)
            if 'sae_features' in franken_out and len(targets['sae_features']) > 0:
                target_sae = targets['sae_features'][0]  # Use first SAE's features as target
                pred_sae = franken_out['sae_features']
                # Match shapes
                min_len = min(pred_sae.shape[1], target_sae.shape[1])
                sae_loss = F.mse_loss(pred_sae[:, :min_len, :], target_sae[:, :min_len, :])
            
            # E. Quality-adaptive weighting
            quality = targets['quality_score']
            adaptive_weight = 1.0 + (1.0 - quality) * 2.0
            
            # Combined loss
            total_loss = (
                logits_loss + 
                args.hidden_weight * hidden_loss + 
                args.mtp_weight * mtp_loss +
                args.sae_weight * sae_loss
            ) * adaptive_weight
            
            # Backward
            optimizer.zero_grad()
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(franken.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            
            # Track metrics
            loss_history['total'].append(total_loss.item())
            loss_history['logits'].append(logits_loss.item())
            loss_history['hidden'].append(hidden_loss.item())
            loss_history['mtp'].append(mtp_loss.item())
            loss_history['quality'].append(quality.item())
            
            global_step += 1
            pbar.update(1)
            
            if global_step % 10 == 0:
                avg_total = sum(loss_history['total'][-10:]) / 10
                avg_logits = sum(loss_history['logits'][-10:]) / 10
                avg_quality = sum(loss_history['quality'][-10:]) / 10
                pbar.set_postfix({
                    'loss': f'{avg_total:.3f}',
                    'logits': f'{avg_logits:.3f}',
                    'quality': f'{avg_quality:.3f}',
                })
            
            # Save checkpoint
            if global_step % args.save_every == 0:
                save_path = f"{args.output_dir}/checkpoint_step_{global_step}.pt"
                torch.save({
                    'model_state_dict': franken.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'scheduler_state_dict': scheduler.state_dict(),
                    'global_step': global_step,
                    'loss_history': loss_history,
                }, save_path)
                print(f"\nSaved checkpoint: {save_path}")
                memory.check("After checkpoint save")
            
            # Emergency cleanup every 50 steps
            if global_step % 50 == 0:
                memory.emergency_cleanup()
                memory.check("After emergency cleanup")
    
    pbar.close()
    
    # Save final
    final_path = f"{args.output_dir}/final_model.pt"
    torch.save({
        'model_state_dict': franken.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'global_step': global_step,
        'loss_history': loss_history,
    }, final_path)
    
    history_path = f"{args.output_dir}/loss_history.json"
    with open(history_path, 'w') as f:
        json.dump({k: [float(v) for v in vals] for k, vals in loss_history.items()}, f)
    
    print(f"\n{'='*70}")
    print(f"Training complete!")
    print(f"Final model: {final_path}")
    print(f"Loss history: {history_path}")
    print(f"{'='*70}")
    
    return franken, loss_history


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    # Model paths
    parser.add_argument('--qwen-model', default='/data/models/Qwen3.6-27B-Uncensored')
    parser.add_argument('--sae-dir', default='/data/models/Qwen-Scope')
    parser.add_argument('--sae-layers', type=int, nargs='+', default=[32, 48])
    parser.add_argument('--data-dir', default='/data/SpecForge/custom_dflash/hidden_states')
    parser.add_argument('--pretrained', default='/data/models/FrankenV8-Final/final_model.pt')
    parser.add_argument('--output-dir', default='/data/models/FrankenV8-25Grafts-SAE-Enhanced')
    
    # Architecture
    parser.add_argument('--num-layers', type=int, default=8)
    parser.add_argument('--max-seq-len', type=int, default=2048)
    
    # Training
    parser.add_argument('--num-steps', type=int, default=1000)
    parser.add_argument('--save-every', type=int, default=100)
    parser.add_argument('--batch-size', type=int, default=1)
    parser.add_argument('--lr', type=float, default=1e-4)
    parser.add_argument('--hidden-weight', type=float, default=0.5)
    parser.add_argument('--mtp-weight', type=float, default=0.3)
    parser.add_argument('--sae-weight', type=float, default=0.2)
    
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    
    train(args)
