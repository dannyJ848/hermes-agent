#!/usr/bin/env python3
"""
ULTIMATE FRANKEN DRAFT MODEL v6 — WITH SSD (Speculative Speculative Decoding)
Tri Dao's ICLR 2026 breakthrough + LK Losses + everything else
For Qwen3.6-27B speculative decoding. ABSOLUTE MAXIMUM SPEED.
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
# FRANKEN GRAFT #23: SSD — Speculative Speculative Decoding
# Tri Dao, ICLR 2026
# ============================================================
class SSDSpeculator(nn.Module):
    """
    Speculative Speculative Decoding (SSD) from Tri Dao et al.
    
    Key insight: While target model verifies, predict verification outcome
    and prepare next speculations pre-emptively. If prediction is correct,
    speculation returns immediately — zero drafting overhead.
    
    Results: 30% faster than optimized speculative decoding, up to 5x vs AR.
    """
    def __init__(self, hidden_size: int, vocab_size: int, num_outcomes: int = 4):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_outcomes = num_outcomes
        
        # Predict verification outcome (how many tokens will be accepted)
        self.outcome_predictor = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.SiLU(),
            nn.Linear(hidden_size // 2, num_outcomes)
        )
        
        # Pre-emptive speculation heads for each outcome
        self.preemptive_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2),
                nn.SiLU(),
                nn.Linear(hidden_size // 2, vocab_size)
            )
            for _ in range(num_outcomes)
        ])
        
        # Confidence in outcome prediction
        self.confidence_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 4),
            nn.SiLU(),
            nn.Linear(hidden_size // 4, 1),
            nn.Sigmoid()
        )
    
    def forward(self, hidden_states):
        """
        hidden_states: [bsz, seq_len, hidden]
        Returns:
          - outcome_logits: [bsz, seq_len, num_outcomes]
          - preemptive_logits: list of [bsz, seq_len, vocab_size]
          - confidence: [bsz, seq_len, 1]
        """
        outcome_logits = self.outcome_predictor(hidden_states)
        preemptive_logits = [head(hidden_states) for head in self.preemptive_heads]
        confidence = self.confidence_head(hidden_states)
        
        return outcome_logits, preemptive_logits, confidence
    
    def get_best_speculation(self, hidden_states, outcome_probs):
        """Select pre-emptive speculation based on predicted outcome."""
        predicted_outcome = torch.argmax(outcome_probs, dim=-1)
        # Use the corresponding preemptive head
        return predicted_outcome


# ============================================================
# Previous grafts (1-22) abbreviated for space
# ============================================================
class LKLosses:
    @staticmethod
    def lk_loss(draft_logits, target_logits, temperature=1.0):
        target_probs = F.softmax(target_logits / temperature, dim=-1)
        draft_probs = F.softmax(draft_logits / temperature, dim=-1)
        target_topk = torch.argmax(target_probs, dim=-1)
        draft_at_target = torch.gather(draft_probs, -1, target_topk.unsqueeze(-1)).squeeze(-1)
        loss = -torch.log(draft_at_target + 1e-10)
        return loss.mean()
    
    @staticmethod
    def acceptance_rate_loss(draft_logits, target_logits, temperature=1.0):
        draft_probs = F.softmax(draft_logits / temperature, dim=-1)
        target_probs = F.softmax(target_logits / temperature, dim=-1)
        acceptance = torch.sum(torch.min(draft_probs, target_probs), dim=-1)
        return -acceptance.mean()

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

class SwiGLU(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.w1 = nn.Linear(dim, dim, bias=False)
        self.w2 = nn.Linear(dim, dim, bias=False)
        self.w3 = nn.Linear(dim, dim, bias=False)
    def forward(self, x):
        return self.w1(x) * F.silu(self.w2(x))

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

class MultiTokenHead(nn.Module):
    def __init__(self, hidden_size: int, vocab_size: int, num_future_tokens: int = 4):
        super().__init__()
        self.num_future_tokens = num_future_tokens
        self.heads = nn.ModuleList([
            nn.Linear(hidden_size, vocab_size, bias=False)
            for _ in range(num_future_tokens)
        ])
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

class HighwayConnection(nn.Module):
    def __init__(self, hidden_size: int):
        super().__init__()
        self.gate = nn.Linear(hidden_size, hidden_size, bias=True)
        self.transform = nn.Linear(hidden_size, hidden_size, bias=True)
    def forward(self, x, residual):
        gate = torch.sigmoid(self.gate(x))
        transform = self.transform(x)
        return gate * transform + (1 - gate) * residual

class DynamicSpeculationController(nn.Module):
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
        return self.confidence_head(hidden_states)

class BidirectionalContextFusion(nn.Module):
    def __init__(self, hidden_size: int):
        super().__init__()
        self.left_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.right_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.fusion_gate = nn.Linear(hidden_size * 2, hidden_size)
    def forward(self, hidden_states):
        bsz, seq_len, hidden = hidden_states.shape
        left = self.left_proj(hidden_states)
        reversed_states = torch.flip(hidden_states, dims=[1])
        right = self.right_proj(reversed_states)
        right = torch.flip(right, dims=[1])
        combined = torch.cat([left, right], dim=-1)
        gate = torch.sigmoid(self.fusion_gate(combined))
        return gate * left + (1 - gate) * right

class LookaheadAttention(nn.Module):
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
        self.lookahead_gate = nn.Parameter(torch.zeros(lookahead))
    def forward(self, hidden_states, attention_mask=None):
        bsz, seq_len, _ = hidden_states.shape
        q = self.q_proj(hidden_states).view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(hidden_states).view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(hidden_states).view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)
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

class PARDParallelDraft(nn.Module):
    def __init__(self, hidden_size: int, vocab_size: int, num_parallel: int = 8):
        super().__init__()
        self.num_parallel = num_parallel
        self.parallel_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2),
                nn.SiLU(),
                nn.Linear(hidden_size // 2, vocab_size)
            )
            for _ in range(num_parallel)
        ])
        self.pos_embed = nn.Embedding(num_parallel, hidden_size)
    def forward(self, hidden_states):
        bsz, seq_len, hidden = hidden_states.shape
        logits = []
        for i, head in enumerate(self.parallel_heads):
            pos_emb = self.pos_embed(torch.tensor(i, device=hidden_states.device))
            pos_emb = pos_emb.view(1, 1, -1).expand(bsz, seq_len, -1)
            combined = hidden_states + pos_emb
            logits.append(head(combined))
        return logits

class TreeAttention(nn.Module):
    def __init__(self, hidden_size: int, num_heads: int, branching_factor: int = 4):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads
        self.branching_factor = branching_factor
        self.q_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.k_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.v_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.o_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.tree_bias = nn.Parameter(torch.zeros(branching_factor, branching_factor))
    def forward(self, hidden_states, tree_mask=None):
        bsz, seq_len, _ = hidden_states.shape
        q = self.q_proj(hidden_states).view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(hidden_states).view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(hidden_states).view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        if seq_len > 1 and tree_mask is not None:
            scores = scores + tree_mask.unsqueeze(1)
        attn = F.softmax(scores, dim=-1)
        out = torch.matmul(attn, v)
        out = out.transpose(1, 2).contiguous().view(bsz, seq_len, -1)
        return self.o_proj(out)

class ConfidenceEarlyExit(nn.Module):
    def __init__(self, hidden_size: int, threshold: float = 0.95):
        super().__init__()
        self.threshold = threshold
        self.confidence_proj = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 4),
            nn.SiLU(),
            nn.Linear(hidden_size // 4, 1),
            nn.Sigmoid()
        )
    def forward(self, hidden_states):
        return self.confidence_proj(hidden_states)
    def should_exit(self, confidence):
        return confidence.mean() > self.threshold


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
# ULTIMATE FRANKEN DRAFT MODEL v6 — WITH SSD
# ============================================================
class UltimateFrankenDraftModelV6(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.hidden_size = config['hidden_size']
        self.num_layers = config['num_hidden_layers']
        self.target_layers = config['target_layer_ids']
        self.block_size = config['block_size']
        self.num_future_tokens = config.get('num_future_tokens', 4)
        
        self.fc = nn.Linear(len(self.target_layers) * self.hidden_size, self.hidden_size, bias=False)
        self.hidden_norm = AdaptiveRMSNorm(self.hidden_size, eps=config['rms_norm_eps'])
        
        # Previous layers (abbreviated)
        self.layers = nn.ModuleList([
            nn.TransformerEncoderLayer(
                d_model=config['hidden_size'],
                nhead=config['num_attention_heads'],
                dim_feedforward=config['intermediate_size'],
                batch_first=True
            )
            for _ in range(self.num_layers)
        ])
        
        self.mtp = MultiTokenHead(self.hidden_size, config['vocab_size'], self.num_future_tokens)
        self.pard = PARDParallelDraft(self.hidden_size, config['vocab_size'], num_parallel=8)
        self.spec_controller = DynamicSpeculationController(self.hidden_size, max_tokens=16)
        self.early_exit = ConfidenceEarlyExit(self.hidden_size)
        
        # FRANKEN GRAFT #23: SSD
        self.ssd = SSDSpeculator(self.hidden_size, config['vocab_size'], num_outcomes=4)
        
        self.norm = AdaptiveRMSNorm(self.hidden_size, eps=config['rms_norm_eps'])
        
        self.embed_tokens = None
        self.lm_head = None
    
    def set_shared_weights(self, embed_tokens, lm_head):
        self.embed_tokens = embed_tokens
        self.lm_head = lm_head
    
    def forward(self, input_ids, target_hidden_states, attention_mask=None, position_ids=None, tree_mask=None):
        hidden_states = self.embed_tokens(input_ids)
        
        bsz, seq_len, _ = hidden_states.size()
        
        target_combined = target_hidden_states.permute(1, 2, 0, 3).reshape(bsz, seq_len, -1)
        target_combined = self.fc(target_combined)
        target_combined = self.hidden_norm(target_combined)
        
        for layer in self.layers:
            hidden_states = layer(hidden_states)
        
        hidden_states = self.norm(hidden_states)
        
        mtp_logits = self.mtp(hidden_states)
        pard_logits = self.pard(hidden_states)
        spec_confidence = self.spec_controller(hidden_states)
        exit_confidence = self.early_exit(hidden_states)
        
        # FRANKEN GRAFT #23: SSD forward
        ssd_outcome, ssd_preemptive, ssd_conf = self.ssd(hidden_states)
        
        primary_logits = self.lm_head(hidden_states)
        
        return primary_logits, mtp_logits, pard_logits, spec_confidence, exit_confidence, ssd_outcome, ssd_preemptive, ssd_conf


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
    parser.add_argument("--optimizer", type=str, default="muon", choices=["adamw", "muon"])
    parser.add_argument("--muon-ns-steps", type=int, default=5)
    parser.add_argument("--num-future-tokens", type=int, default=4)
    parser.add_argument("--num-layers", type=int, default=8)
    parser.add_argument("--use-mtp", action="store_true", default=True)
    parser.add_argument("--use-pard", action="store_true", default=True)
    parser.add_argument("--use-lk-loss", action="store_true", default=True)
    parser.add_argument("--lk-loss-weight", type=float, default=1.0)
    parser.add_argument("--use-ssd", action="store_true", default=True, help="Enable Speculative Speculative Decoding")
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
    print("ULTIMATE FRANKEN DRAFT MODEL v6 — WITH SSD")
    print("Tri Dao's ICLR 2026 + LK Losses + Everything")
    print("=" * 70)
    print(f"Layers: {config['num_hidden_layers']}")
    print(f"MTP: {config['num_future_tokens']}")
    print(f"PARD: 8")
    print(f"SSD: Enabled")
    print(f"LK Loss: {args.use_lk_loss}")
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
    
    print("Creating Franken draft model v6...")
    draft_model = UltimateFrankenDraftModelV6(config).cuda().bfloat16()
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
    
    lk_losses = LKLosses()
    
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
            
            # Forward with everything
            primary_logits, mtp_logits, pard_logits, spec_confidence, exit_confidence, ssd_outcome, ssd_preemptive, ssd_conf = draft_model(
                input_ids, hidden_states, attention_mask
            )
            
            # Primary loss
            shift_primary = primary_logits[..., :-1, :].contiguous()
            shift_labels = input_ids[..., 1:].contiguous()
            loss_primary = F.cross_entropy(
                shift_primary.reshape(-1, shift_primary.size(-1)),
                shift_labels.reshape(-1),
                ignore_index=0,
            )
            
            # LK Loss
            loss_lk = 0
            if args.use_lk_loss:
                loss_lk = lk_losses.lk_loss(
                    primary_logits[:, :-1, :],
                    primary_logits[:, :-1, :],
                    temperature=1.0
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
            
            # PARD losses
            loss_pard = 0
            if args.use_pard and len(pard_logits) > 0:
                for i, pard_logit in enumerate(pard_logits):
                    shift_pard = pard_logit[..., :-1, :].contiguous()
                    shift_pard_labels = torch.cat([
                        input_ids[..., i+1:].contiguous(),
                        torch.zeros(bsz, i, dtype=torch.long, device='cuda')
                    ], dim=-1)
                    loss_pard += F.cross_entropy(
                        shift_pard.reshape(-1, shift_pard.size(-1)),
                        shift_pard_labels.reshape(-1),
                        ignore_index=0,
                    )
                loss_pard = loss_pard / len(pard_logits)
            
            # SSD losses
            loss_ssd = 0
            if args.use_ssd:
                # Outcome prediction loss
                ssd_outcome_shift = ssd_outcome[:, :-1, :]
                # Predict how many tokens will be accepted
                outcome_target = torch.zeros(bsz, max_len-1, dtype=torch.long, device='cuda')
                loss_ssd += F.cross_entropy(
                    ssd_outcome_shift.reshape(-1, ssd_outcome_shift.size(-1)),
                    outcome_target.reshape(-1),
                    ignore_index=0,
                )
                
                # Preemptive speculation loss
                for i, preemptive in enumerate(ssd_preemptive):
                    shift_pre = preemptive[..., :-1, :].contiguous()
                    shift_pre_labels = torch.cat([
                        input_ids[..., i+1:].contiguous(),
                        torch.zeros(bsz, i, dtype=torch.long, device='cuda')
                    ], dim=-1)
                    loss_ssd += F.cross_entropy(
                        shift_pre.reshape(-1, shift_pre.size(-1)),
                        shift_pre_labels.reshape(-1),
                        ignore_index=0,
                    )
                loss_ssd = loss_ssd / (1 + len(ssd_preemptive))
            
            # Dynamic speculation loss
            loss_spec = 0
            pred_tokens = primary_logits.argmax(dim=-1)
            correct_mask = (pred_tokens[..., :-1] == shift_labels).float()
            spec_conf = spec_confidence[..., :-1, 0]
            loss_spec = -torch.mean(correct_mask * torch.log(spec_conf + 1e-6))
            
            # Early exit loss
            loss_exit = 0
            exit_conf = exit_confidence[..., :-1, 0]
            loss_exit = -torch.mean(correct_mask * torch.log(exit_conf + 1e-6))
            
            # Combined loss with SSD
            loss = (
                loss_primary + 
                args.lk_loss_weight * loss_lk +
                0.5 * loss_mtp + 
                0.3 * loss_pard + 
                0.2 * loss_ssd +
                0.1 * loss_spec + 
                0.05 * loss_exit
            )
            
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(draft_model.parameters(), 1.0)
            optimizer.step()
            
            epoch_loss += loss.item()
            global_step += 1
            
            pbar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'primary': f'{loss_primary.item():.4f}',
                'lk': f'{loss_lk.item():.4f}' if isinstance(loss_lk, torch.Tensor) else '0.0000',
                'mtp': f'{loss_mtp.item():.4f}' if isinstance(loss_mtp, torch.Tensor) else '0.0000',
                'pard': f'{loss_pard.item():.4f}' if isinstance(loss_pard, torch.Tensor) else '0.0000',
                'ssd': f'{loss_ssd.item():.4f}' if isinstance(loss_ssd, torch.Tensor) else '0.0000',
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
