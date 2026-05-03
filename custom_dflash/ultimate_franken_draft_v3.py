#!/usr/bin/env python3
"""
ULTIMATE FRANKEN DRAFT MODEL v3 — EVERYTHING GRAFTED
For Qwen3.6-27B speculative decoding. Maximum speed.
Techniques from: DeepSeek V4, P-EAGLE, FailFast, BiTA, Llama, Mistral, GDN
"""

import argparse
import json
import os
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
from transformers import AutoTokenizer

# ============================================================
# FRANKEN GRAFT #1: Muon Optimizer (DeepSeek V4)
# ============================================================
def zeropower_via_newtonschulz5(G, steps: int = 5):
    assert G.ndim >= 2
    a, b, c = (3.4445, -4.7750, 2.0315)
    X = G.bfloat16()
    if G.size(-2) > G.size(-1):
        X = X.mT
    X = X / (X.norm(dim=(-2, -1), keepdim=True) + 1e-7)
    for _ in range(steps):
        A = X @ X.mT
        B = b * A + c * A @ A
        X = a * X + B @ X
    if G.size(-2) > G.size(-1):
        X = X.mT
    return X

class Muon(torch.optim.Optimizer):
    def __init__(self, params, lr=0.02, weight_decay=0.01, momentum=0.95,
                 nesterov=True, ns_steps=5, adamw_betas=(0.95, 0.98), adamw_eps=1e-8):
        defaults = dict(lr=lr, weight_decay=weight_decay, momentum=momentum,
                       nesterov=nesterov, ns_steps=ns_steps,
                       adamw_betas=adamw_betas, adamw_eps=adamw_eps)
        super().__init__(params, defaults)

    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()
        for group in self.param_groups:
            lr = group['lr']; wd = group['weight_decay']
            momentum = group['momentum']; nesterov = group['nesterov']
            ns_steps = group['ns_steps']
            for p in group['params']:
                if p.grad is None:
                    continue
                g = p.grad
                state = self.state[p]
                if wd != 0:
                    p.data.mul_(1 - lr * wd)
                if p.ndim >= 2 and p.numel() >= 2:
                    if len(state) == 0:
                        state['momentum_buffer'] = torch.zeros_like(g)
                    buf = state['momentum_buffer']
                    buf.lerp_(g, 1 - momentum)
                    update = g.lerp_(buf, momentum) if nesterov else buf
                    if update.ndim == 4:
                        update = update.view(len(update), -1)
                    update = zeropower_via_newtonschulz5(update, steps=ns_steps)
                    update *= max(1, update.size(-2) / update.size(-1)) ** 0.5
                    if update.ndim != p.ndim:
                        update = update.view(p.shape)
                    p.data.add_(update, alpha=-lr)
                else:
                    if len(state) == 0:
                        state['step'] = 0
                        state['exp_avg'] = torch.zeros_like(g)
                        state['exp_avg_sq'] = torch.zeros_like(g)
                    state['step'] += 1
                    exp_avg = state['exp_avg']
                    exp_avg_sq = state['exp_avg_sq']
                    beta1, beta2 = group['adamw_betas']
                    eps = group['adamw_eps']
                    exp_avg.lerp_(g, 1 - beta1)
                    exp_avg_sq.lerp_(g.square(), 1 - beta2)
                    bias_correction1 = 1 - beta1 ** state['step']
                    bias_correction2 = 1 - beta2 ** state['step']
                    step_size = lr / bias_correction1
                    denom = (exp_avg_sq.sqrt() / math.sqrt(bias_correction2)).add_(eps)
                    p.data.addcdiv_(exp_avg, denom, value=-step_size)
        return loss


# ============================================================
# FRANKEN GRAFT #2: SwiGLU (Llama)
# ============================================================
class SwiGLU(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.w1 = nn.Linear(dim, dim, bias=False)
        self.w2 = nn.Linear(dim, dim, bias=False)
        self.w3 = nn.Linear(dim, dim, bias=False)
    def forward(self, x):
        return self.w1(x) * F.silu(self.w2(x))


# ============================================================
# FRANKEN GRAFT #3: Manifold Hyper-Connections (DeepSeek V4)
# ============================================================
class ManifoldHyperConnection(nn.Module):
    def __init__(self, hidden_size: int, dropout: float = 0.0):
        super().__init__()
        self.alpha = nn.Parameter(torch.ones(1))
        self.beta = nn.Parameter(torch.zeros(1))
        self.gamma = nn.Parameter(torch.ones(1))
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()
    def forward(self, x, residual):
        denom = torch.sqrt(self.alpha**2 + self.beta**2 + 1e-6)
        out = self.gamma * (self.alpha * x + self.beta * residual) / denom
        return self.dropout(out)


# ============================================================
# FRANKEN GRAFT #4: Gated Attention (GDN-inspired)
# ============================================================
class GatedAttention(nn.Module):
    def __init__(self, num_heads: int):
        super().__init__()
        self.num_heads = num_heads
        self.gate = nn.Parameter(torch.ones(num_heads))
        self.gate_bias = nn.Parameter(torch.zeros(num_heads))
    def forward(self, attn_output, heads):
        gate = torch.sigmoid(self.gate + self.gate_bias)
        gate = gate.view(1, -1, 1, 1)
        return attn_output * gate


# ============================================================
# FRANKEN GRAFT #5: Rotary Embedding (RoPE)
# ============================================================
class RotaryEmbedding(nn.Module):
    def __init__(self, dim: int, max_seq_len: int = 262144, base: float = 10000.0):
        super().__init__()
        self.dim = dim
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer('inv_freq', inv_freq)
    def forward(self, seq_len: int, device):
        t = torch.arange(seq_len, device=device).type_as(self.inv_freq)
        freqs = torch.outer(t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        return emb.cos(), emb.sin()
    def apply_rotary_pos_emb(self, q, k, cos, sin):
        def rotate_half(x):
            x1, x2 = x[..., :x.shape[-1]//2], x[..., x.shape[-1]//2:]
            return torch.cat((-x2, x1), dim=-1)
        cos = cos.unsqueeze(1); sin = sin.unsqueeze(1)
        q_embed = (q * cos) + (rotate_half(q) * sin)
        k_embed = (k * cos) + (rotate_half(k) * sin)
        return q_embed, k_embed


# ============================================================
# FRANKEN GRAFT #6: Multi-Token Prediction (MTP-4)
# ============================================================
class MultiTokenHead(nn.Module):
    def __init__(self, hidden_size: int, vocab_size: int, num_future_tokens: int = 4):
        super().__init__()
        self.num_future_tokens = num_future_tokens
        self.heads = nn.ModuleList([
            nn.Linear(hidden_size, vocab_size, bias=False)
            for _ in range(num_future_tokens)
        ])
        self.future_proj = nn.Linear(hidden_size * num_future_tokens, hidden_size, bias=False)
    def forward(self, hidden_states):
        bsz, seq_len, hidden_size = hidden_states.shape
        logits = []
        for i, head in enumerate(self.heads):
            if i == 0:
                logits.append(head(hidden_states))
            else:
                shifted = torch.cat([
                    torch.zeros(bsz, i, hidden_size, device=hidden_states.device, dtype=hidden_states.dtype),
                    hidden_states[:, :-i, :]
                ], dim=1)
                logits.append(head(shifted))
        return logits


# ============================================================
# FRANKEN GRAFT #7: Adaptive RMSNorm
# ============================================================
class AdaptiveRMSNorm(nn.Module):
    def __init__(self, hidden_size: int, eps: float = 1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.eps = eps
        self.scale = nn.Parameter(torch.ones(1))
        self.shift = nn.Parameter(torch.zeros(1))
    def forward(self, hidden_states):
        input_dtype = hidden_states.dtype
        hidden_states = hidden_states.to(torch.float32)
        variance = hidden_states.pow(2).mean(-1, keepdim=True)
        hidden_states = hidden_states * torch.rsqrt(variance + self.eps)
        hidden_states = hidden_states * (self.scale + 1.0) + self.shift
        return (self.weight * hidden_states).to(input_dtype)


# ============================================================
# FRANKEN GRAFT #8: Highway Connections
# ============================================================
class HighwayConnection(nn.Module):
    def __init__(self, hidden_size: int):
        super().__init__()
        self.gate = nn.Linear(hidden_size, hidden_size, bias=True)
        self.transform = nn.Linear(hidden_size, hidden_size, bias=True)
    def forward(self, x, residual):
        gate = torch.sigmoid(self.gate(x))
        transform = self.transform(x)
        return gate * transform + (1 - gate) * residual


# ============================================================
# FRANKEN GRAFT #16: Dynamic Speculation Length (FailFast-inspired)
# ============================================================
class DynamicSpeculationController(nn.Module):
    """Dynamically adjusts how many tokens to predict based on confidence."""
    def __init__(self, hidden_size: int, max_tokens: int = 16):
        super().__init__()
        self.max_tokens = max_tokens
        self.confidence_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 4),
            nn.SiLU(),
            nn.Linear(hidden_size // 4, 1),
            nn.Sigmoid()
        )
    
    def forward(self, hidden_states):
        # Returns confidence score [0,1] for each position
        return self.confidence_head(hidden_states)
    
    def get_speculation_length(self, confidence_scores, threshold=0.8):
        # Count consecutive high-confidence positions
        lengths = []
        for scores in confidence_scores:
            length = 0
            for score in scores:
                if score > threshold:
                    length += 1
                else:
                    break
            lengths.append(min(length, self.max_tokens))
        return lengths


# ============================================================
# FRANKEN GRAFT #17: Bidirectional Context (BiTA-inspired)
# ============================================================
class BidirectionalContextFusion(nn.Module):
    """Fuses left-to-right and right-to-left context."""
    def __init__(self, hidden_size: int):
        super().__init__()
        self.left_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.right_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.fusion_gate = nn.Linear(hidden_size * 2, hidden_size)
    
    def forward(self, hidden_states):
        # hidden_states: [bsz, seq_len, hidden]
        bsz, seq_len, hidden = hidden_states.shape
        
        # Left-to-right
        left = self.left_proj(hidden_states)
        
        # Right-to-left (reversed)
        reversed_states = torch.flip(hidden_states, dims=[1])
        right = self.right_proj(reversed_states)
        right = torch.flip(right, dims=[1])
        
        # Fusion gate
        combined = torch.cat([left, right], dim=-1)
        gate = torch.sigmoid(self.fusion_gate(combined))
        
        return gate * left + (1 - gate) * right


# ============================================================
# FRANKEN GRAFT #18: Lookahead Attention (LongSpec-inspired)
# ============================================================
class LookaheadAttention(nn.Module):
    """Attention that can peek at future tokens for draft generation."""
    def __init__(self, hidden_size: int, num_heads: int, lookahead: int = 4):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads
        self.lookahead = lookahead
        
        self.q_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.k_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.v_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.o_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        
        # Learnable lookahead mask
        self.lookahead_gate = nn.Parameter(torch.zeros(lookahead))
    
    def forward(self, hidden_states, attention_mask=None):
        bsz, seq_len, _ = hidden_states.shape
        
        q = self.q_proj(hidden_states).view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(hidden_states).view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(hidden_states).view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Standard causal attention
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        
        # Add lookahead bias for future positions
        if seq_len > 1:
            for i in range(min(self.lookahead, seq_len - 1)):
                if i < len(self.lookahead_gate):
                    scores[:, :, :-i-1, i+1:] += self.lookahead_gate[i]
        
        if attention_mask is not None:
            scores = scores + attention_mask
        
        attn = F.softmax(scores, dim=-1)
        out = torch.matmul(attn, v)
        
        out = out.transpose(1, 2).contiguous().view(bsz, seq_len, -1)
        return self.o_proj(out)


# ============================================================
# Dataset
# ============================================================
class DFlashDataset(Dataset):
    def __init__(self, data_dir, block_size=16):
        self.data_dir = data_dir
        self.block_size = block_size
        self.files = sorted([f for f in os.listdir(data_dir) if f.endswith('.pt')])
        print(f"Loaded {len(self.files)} samples from {data_dir}")
    def __len__(self):
        return len(self.files)
    def __getitem__(self, idx):
        data = torch.load(os.path.join(self.data_dir, self.files[idx]), map_location='cpu')
        return {
            'input_ids': data['input_ids'],
            'hidden_states': data['hidden_states'],
            'seq_len': data['seq_len'],
        }

def collate_fn(batch):
    max_len = max(b['seq_len'] for b in batch)
    input_ids = torch.stack([
        torch.cat([b['input_ids'], torch.zeros(max_len - b['seq_len'], dtype=torch.long)]) 
        for b in batch
    ])
    hidden_states = torch.stack([
        torch.cat([b['hidden_states'], torch.zeros(5, max_len - b['seq_len'], 5120)], dim=1)
        for b in batch
    ])
    return {
        'input_ids': input_ids,
        'hidden_states': hidden_states,
        'seq_lens': [b['seq_len'] for b in batch],
    }


# ============================================================
# ULTIMATE FRANKEN DRAFT LAYER v3
# ============================================================
class FrankenDraftLayerV3(nn.Module):
    def __init__(self, config, layer_idx: int):
        super().__init__()
        self.hidden_size = config['hidden_size']
        self.num_heads = config['num_attention_heads']
        self.num_kv_heads = config['num_key_value_heads']
        self.head_dim = config['head_dim']
        self.num_kv_groups = self.num_heads // self.num_kv_heads
        self.layer_idx = layer_idx
        
        # QKV projections
        self.q_proj = nn.Linear(self.hidden_size, self.num_heads * self.head_dim, bias=False)
        self.k_proj = nn.Linear(self.hidden_size, self.num_kv_heads * self.head_dim, bias=False)
        self.v_proj = nn.Linear(self.hidden_size, self.num_kv_heads * self.head_dim, bias=False)
        self.o_proj = nn.Linear(self.num_heads * self.head_dim, self.hidden_size, bias=False)
        
        # FRANKEN: RoPE
        self.rope = RotaryEmbedding(self.head_dim, max_seq_len=config['max_position_embeddings'])
        
        # FRANKEN: Gated attention
        self.attn_gate = GatedAttention(self.num_heads)
        
        # FRANKEN: Lookahead attention (for draft layers)
        self.lookahead = LookaheadAttention(self.hidden_size, self.num_heads, lookahead=4) if layer_idx % 2 == 0 else None
        
        # FRANKEN: SwiGLU MLP
        self.mlp = SwiGLU(self.hidden_size)
        
        # FRANKEN: Adaptive RMSNorm
        self.input_norm = AdaptiveRMSNorm(self.hidden_size, eps=config['rms_norm_eps'])
        self.post_attn_norm = AdaptiveRMSNorm(self.hidden_size, eps=config['rms_norm_eps'])
        
        # FRANKEN: mHC residual
        self.attn_residual = ManifoldHyperConnection(self.hidden_size)
        self.mlp_residual = ManifoldHyperConnection(self.hidden_size)
        
        # FRANKEN: Highway skip (for deeper layers)
        self.highway = HighwayConnection(self.hidden_size) if layer_idx >= 2 else None
        
        # FRANKEN: Bidirectional fusion (every 3rd layer)
        self.bidirectional = BidirectionalContextFusion(self.hidden_size) if layer_idx % 3 == 0 else None
    
    def forward(self, hidden_states, target_hidden, attention_mask=None, position_ids=None):
        bsz, q_len, _ = hidden_states.size()
        kv_len = target_hidden.size(1)
        
        # FRANKEN: Bidirectional fusion
        if self.bidirectional is not None:
            hidden_states = self.bidirectional(hidden_states)
        
        # Self-attention with target hidden states as KV
        residual = hidden_states
        hidden_states = self.input_norm(hidden_states)
        
        query = self.q_proj(hidden_states).view(bsz, q_len, self.num_heads, self.head_dim).transpose(1, 2)
        key = self.k_proj(target_hidden).view(bsz, kv_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        value = self.v_proj(target_hidden).view(bsz, kv_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        
        # FRANKEN: Apply RoPE
        if position_ids is not None:
            cos, sin = self.rope(q_len, query.device)
            query, key = self.rope.apply_rotary_pos_emb(query, key, cos, sin)
        
        # GQA repeat
        key = key.repeat_interleave(self.num_kv_groups, dim=1)
        value = value.repeat_interleave(self.num_kv_groups, dim=1)
        
        # Attention
        if attention_mask is None:
            attn_output = F.scaled_dot_product_attention(query, key, value, is_causal=True)
        else:
            attn_output = F.scaled_dot_product_attention(query, key, value, is_causal=False)
        
        # FRANKEN: Gated attention
        attn_output = self.attn_gate(attn_output, query)
        
        attn_output = attn_output.transpose(1, 2).contiguous().view(bsz, q_len, -1)
        attn_output = self.o_proj(attn_output)
        
        # FRANKEN: Lookahead attention (parallel path)
        if self.lookahead is not None:
            lookahead_out = self.lookahead(residual)
            attn_output = attn_output + 0.3 * lookahead_out
        
        # FRANKEN: mHC residual
        hidden_states = self.attn_residual(attn_output, residual)
        
        # FRANKEN: Highway skip for deeper layers
        if self.highway is not None:
            hidden_states = self.highway(hidden_states, residual)
        
        # MLP
        residual = hidden_states
        hidden_states = self.post_attn_norm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        
        # FRANKEN: mHC residual for MLP
        hidden_states = self.mlp_residual(hidden_states, residual)
        
        return hidden_states


# ============================================================
# ULTIMATE FRANKEN DRAFT MODEL v3
# ============================================================
class UltimateFrankenDraftModelV3(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.hidden_size = config['hidden_size']
        self.num_layers = config['num_hidden_layers']
        self.target_layers = config['target_layer_ids']
        self.block_size = config['block_size']
        self.num_future_tokens = config.get('num_future_tokens', 4)
        
        # FC to combine target hidden states
        self.fc = nn.Linear(len(self.target_layers) * self.hidden_size, self.hidden_size, bias=False)
        self.hidden_norm = AdaptiveRMSNorm(self.hidden_size, eps=config['rms_norm_eps'])
        
        # FRANKEN: Deeper architecture
        self.layers = nn.ModuleList([
            FrankenDraftLayerV3(config, layer_idx=i)
            for i in range(self.num_layers)
        ])
        
        # FRANKEN: Multi-Token Prediction heads
        self.mtp = MultiTokenHead(self.hidden_size, config['vocab_size'], self.num_future_tokens)
        
        # FRANKEN: Dynamic speculation controller
        self.spec_controller = DynamicSpeculationController(self.hidden_size, max_tokens=16)
        
        # Final norm
        self.norm = AdaptiveRMSNorm(self.hidden_size, eps=config['rms_norm_eps'])
        
        # Shared weights (set externally)
        self.embed_tokens = None
        self.lm_head = None
    
    def set_shared_weights(self, embed_tokens, lm_head):
        self.embed_tokens = embed_tokens
        self.lm_head = lm_head
    
    def forward(self, input_ids, target_hidden_states, attention_mask=None, position_ids=None):
        hidden_states = self.embed_tokens(input_ids)
        
        # Combine target hidden states
        bsz, seq_len, _ = hidden_states.size()
        num_target_layers = target_hidden_states.size(0)
        
        target_combined = target_hidden_states.permute(1, 2, 0, 3).reshape(bsz, seq_len, -1)
        target_combined = self.fc(target_combined)
        target_combined = self.hidden_norm(target_combined)
        
        # Pass through Franken layers
        for layer in self.layers:
            hidden_states = layer(hidden_states, target_combined, attention_mask, position_ids)
        
        hidden_states = self.norm(hidden_states)
        
        # FRANKEN: Multi-Token Prediction
        mtp_logits = self.mtp(hidden_states)
        
        # FRANKEN: Dynamic speculation confidence
        spec_confidence = self.spec_controller(hidden_states)
        
        # Primary logits
        primary_logits = self.lm_head(hidden_states)
        
        return primary_logits, mtp_logits, spec_confidence


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hidden-states-dir", type=str, required=True)
    parser.add_argument("--target-model-path", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--num-epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=6e-4)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--block-size", type=int, default=16)
    parser.add_argument("--save-interval", type=int, default=500)
    parser.add_argument("--trust-remote-code", action="store_true")
    # FRANKEN: Advanced options
    parser.add_argument("--optimizer", type=str, default="muon", choices=["adamw", "muon"])
    parser.add_argument("--muon-ns-steps", type=int, default=5)
    parser.add_argument("--num-future-tokens", type=int, default=4)
    parser.add_argument("--num-layers", type=int, default=8)
    parser.add_argument("--use-mtp", action="store_true", default=True)
    parser.add_argument("--use-bidirectional", action="store_true", default=True)
    parser.add_argument("--use-lookahead", action="store_true", default=True)
    parser.add_argument("--use-dynamic-spec", action="store_true", default=True)
    return parser.parse_args()

def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    
    config = {
        'hidden_size': 5120,
        'num_hidden_layers': args.num_layers,
        'num_attention_heads': 24,
        'num_key_value_heads': 4,
        'head_dim': 213,
        'intermediate_size': 13824,
        'rms_norm_eps': 1e-6,
        'max_position_embeddings': 262144,
        'block_size': args.block_size,
        'target_layer_ids': [1, 16, 31, 46, 61],
        'vocab_size': 152064,
        'num_future_tokens': args.num_future_tokens,
    }
    
    print("=" * 70)
    print("ULTIMATE FRANKEN DRAFT MODEL v3 — EVERYTHING GRAFTED")
    print("=" * 70)
    print(f"Layers: {config['num_hidden_layers']}")
    print(f"MTP future tokens: {config['num_future_tokens']}")
    print(f"Optimizer: {args.optimizer}")
    print(f"Bidirectional: {args.use_bidirectional}")
    print(f"Lookahead: {args.use_lookahead}")
    print(f"Dynamic Speculation: {args.use_dynamic_spec}")
    print("=" * 70)
    
    print("Loading tokenizer and shared weights...")
    tokenizer = AutoTokenizer.from_pretrained(args.target_model_path, trust_remote_code=args.trust_remote_code)
    
    from transformers import AutoModelForCausalLM
    target_model = AutoModelForCausalLM.from_pretrained(
        args.target_model_path,
        torch_dtype=torch.bfloat16,
        device_map='cpu',
        trust_remote_code=args.trust_remote_code,
    )
    
    embed_tokens = target_model.model.embed_tokens.to('cuda')
    lm_head = target_model.lm_head.to('cuda')
    
    del target_model
    torch.cuda.empty_cache()
    
    print("Creating Franken draft model v3...")
    draft_model = UltimateFrankenDraftModelV3(config).cuda().bfloat16()
    draft_model.set_shared_weights(embed_tokens, lm_head)
    
    total_params = sum(p.numel() for p in draft_model.parameters())
    print(f"Draft model parameters: {total_params / 1e9:.2f}B")
    
    if args.optimizer == "muon":
        optimizer = Muon(
            draft_model.parameters(),
            lr=args.learning_rate,
            weight_decay=0.1,
            momentum=0.95,
            nesterov=True,
            ns_steps=args.muon_ns_steps,
        )
        print("[FRANKEN] Muon optimizer")
    else:
        optimizer = torch.optim.AdamW(
            [p for p in draft_model.parameters() if p.requires_grad],
            lr=args.learning_rate,
            betas=(0.9, 0.95),
            weight_decay=0.1,
        )
        print("[FRANKEN] AdamW optimizer")
    
    dataset = DFlashDataset(args.hidden_states_dir, block_size=args.block_size)
    dataloader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=0,
    )
    
    global_step = 0
    for epoch in range(args.num_epochs):
        draft_model.train()
        epoch_loss = 0
        
        pbar = tqdm(dataloader, desc=f"Epoch {epoch}")
        for batch in pbar:
            input_ids = batch['input_ids'].cuda()
            hidden_states = batch['hidden_states'].cuda().bfloat16()
            seq_lens = batch['seq_lens']
            
            bsz, max_len = input_ids.shape
            attention_mask = torch.ones(bsz, 1, max_len, max_len, device='cuda', dtype=torch.bfloat16)
            for i, seq_len in enumerate(seq_lens):
                attention_mask[i, :, seq_len:, :] = 0
                attention_mask[i, :, :, seq_len:] = 0
            
            # FRANKEN: Forward with everything
            primary_logits, mtp_logits, spec_confidence = draft_model(input_ids, hidden_states, attention_mask)
            
            # Primary loss
            shift_primary = primary_logits[..., :-1, :].contiguous()
            shift_labels = input_ids[..., 1:].contiguous()
            loss_primary = F.cross_entropy(
                shift_primary.reshape(-1, shift_primary.size(-1)),
                shift_labels.reshape(-1),
                ignore_index=0,
            )
            
            # MTP losses
            loss_mtp = 0
            if args.use_mtp and len(mtp_logits) > 1:
                for i, mtp_logit in enumerate(mtp_logits[1:], start=1):
                    shift_mtp = mtp_logit[..., :-1, :].contiguous()
                    shift_mtp_labels = torch.cat([
                        input_ids[..., i+1:].contiguous(),
                        torch.zeros(bsz, i, dtype=torch.long, device='cuda')
                    ], dim=-1)
                    loss_mtp += F.cross_entropy(
                        shift_mtp.reshape(-1, shift_mtp.size(-1)),
                        shift_mtp_labels.reshape(-1),
                        ignore_index=0,
                    )
                loss_mtp = loss_mtp / (len(mtp_logits) - 1)
            
            # Dynamic speculation loss (encourage confident predictions)
            loss_spec = 0
            if args.use_dynamic_spec:
                # Reward high confidence on correct predictions
                pred_tokens = primary_logits.argmax(dim=-1)
                correct_mask = (pred_tokens[..., :-1] == shift_labels).float()
                spec_conf = spec_confidence[..., :-1, 0]
                loss_spec = -torch.mean(correct_mask * torch.log(spec_conf + 1e-6))
            
            # Combined loss
            loss = loss_primary + 0.5 * loss_mtp + 0.1 * loss_spec
            
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(draft_model.parameters(), 1.0)
            optimizer.step()
            
            epoch_loss += loss.item()
            global_step += 1
            
            pbar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'primary': f'{loss_primary.item():.4f}',
                'mtp': f'{loss_mtp.item():.4f}' if isinstance(loss_mtp, torch.Tensor) else '0.0000',
                'spec': f'{loss_spec.item():.4f}' if isinstance(loss_spec, torch.Tensor) else '0.0000',
                'step': global_step
            })
            
            if global_step % args.save_interval == 0:
                checkpoint_path = os.path.join(args.output_dir, f'checkpoint-{global_step}.pt')
                torch.save({
                    'step': global_step,
                    'epoch': epoch,
                    'model_state_dict': draft_model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'loss': loss.item(),
                    'config': config,
                    'optimizer_type': args.optimizer,
                }, checkpoint_path)
                print(f"Saved checkpoint to {checkpoint_path}")
        
        avg_loss = epoch_loss / len(dataloader)
        print(f"Epoch {epoch} complete. Average loss: {avg_loss:.4f}")
    
    final_path = os.path.join(args.output_dir, 'final_model.pt')
    torch.save({
        'model_state_dict': draft_model.state_dict(),
        'config': config,
        'optimizer_type': args.optimizer,
    }, final_path)
    print(f"Training complete! Final model saved to {final_path}")

if __name__ == "__main__":
    main()
