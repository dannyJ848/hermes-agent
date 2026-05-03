#!/usr/bin/env python3
"""
ULTIMATE FRANKEN DRAFT MODEL v8 — DART + SSD + LK + LTD
DART: Diffusion-Inspired Speculative Decoding (Jan 2026)
SSD: Speculative Speculative Decoding (Tri Dao, ICLR 2026)
LK Losses: Direct Acceptance Rate Optimization (Feb 2026)
LTD: Learning to Draft with RL (Mar 2026)
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
# FRANKEN GRAFT #25: LTD — Learning to Draft with RL
# Mar 2026 paper: "Learning to Draft: Adaptive Speculative Decoding with RL"
# ============================================================
class AdaptiveDraftPolicy(nn.Module):
    """
    LTD: Reinforcement learning policy for adaptive speculative decoding.
    
    Key insight: Train a policy that dynamically decides:
    - How many tokens to draft (speculation depth)
    - When to stop drafting (early exit)
    - How to allocate time between draft and verify
    
    Results: 2.24x-4.32x speedup, 36.4% better than EAGLE3.
    """
    def __init__(self, hidden_size: int, max_depth: int = 16):
        super().__init__()
        self.hidden_size = hidden_size
        self.max_depth = max_depth
        
        # State encoder
        self.state_encoder = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.SiLU(),
            nn.LayerNorm(hidden_size // 2)
        )
        
        # Action heads
        self.depth_policy = nn.Sequential(
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.SiLU(),
            nn.Linear(hidden_size // 4, max_depth),
            nn.Softmax(dim=-1)
        )
        
        self.exit_policy = nn.Sequential(
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.SiLU(),
            nn.Linear(hidden_size // 4, 1),
            nn.Sigmoid()
        )
        
        self.confidence_policy = nn.Sequential(
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.SiLU(),
            nn.Linear(hidden_size // 4, 1),
            nn.Sigmoid()
        )
    
    def forward(self, hidden_states):
        """
        Returns:
          - depth_probs: [bsz, seq_len, max_depth] — how many tokens to draft
          - exit_prob: [bsz, seq_len, 1] — probability of early exit
          - confidence: [bsz, seq_len, 1] — confidence in current state
        """
        state = self.state_encoder(hidden_states)
        depth_probs = self.depth_policy(state)
        exit_prob = self.exit_policy(state)
        confidence = self.confidence_policy(state)
        return depth_probs, exit_prob, confidence
    
    def select_action(self, hidden_states, temperature=1.0):
        """Sample actions from policies."""
        depth_probs, exit_prob, confidence = self.forward(hidden_states)
        
        # Sample speculation depth
        depth_dist = torch.distributions.Categorical(depth_probs / temperature)
        depth = depth_dist.sample()
        
        # Sample exit decision
        exit_dist = torch.distributions.Bernoulli(exit_prob.squeeze(-1))
        should_exit = exit_dist.sample()
        
        return depth, should_exit, confidence


# ============================================================
# FRANKEN GRAFT #24: DART
# ============================================================
class DARTParallelDraft(nn.Module):
    def __init__(self, hidden_size: int, vocab_size: int, num_positions: int = 8):
        super().__init__()
        self.num_positions = num_positions
        self.position_embeddings = nn.Embedding(num_positions, hidden_size)
        self.parallel_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size),
                nn.SiLU(),
                nn.LayerNorm(hidden_size),
                nn.Linear(hidden_size, vocab_size)
            )
            for _ in range(num_positions)
        ])
        self.feature_extractor = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.SiLU(),
            nn.LayerNorm(hidden_size)
        )
    
    def forward(self, hidden_states):
        bsz, seq_len, hidden = hidden_states.shape
        features = self.feature_extractor(hidden_states)
        logits = []
        for i, head in enumerate(self.parallel_heads):
            pos_emb = self.position_embeddings(torch.tensor(i, device=hidden_states.device))
            pos_emb = pos_emb.view(1, 1, -1).expand(bsz, seq_len, -1)
            combined = features + pos_emb
            logits.append(head(combined))
        return logits


# ============================================================
# FRANKEN GRAFT #23: SSD
# ============================================================
class SSDSpeculator(nn.Module):
    def __init__(self, hidden_size: int, vocab_size: int, num_outcomes: int = 4):
        super().__init__()
        self.num_outcomes = num_outcomes
        self.outcome_predictor = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.SiLU(),
            nn.Linear(hidden_size // 2, num_outcomes)
        )
        self.preemptive_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2),
                nn.SiLU(),
                nn.Linear(hidden_size // 2, vocab_size)
            )
            for _ in range(num_outcomes)
        ])
        self.confidence_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 4),
            nn.SiLU(),
            nn.Linear(hidden_size // 4, 1),
            nn.Sigmoid()
        )
    
    def forward(self, hidden_states):
        outcome_logits = self.outcome_predictor(hidden_states)
        preemptive_logits = [head(hidden_states) for head in self.preemptive_heads]
        confidence = self.confidence_head(hidden_states)
        return outcome_logits, preemptive_logits, confidence


# ============================================================
# FRANKEN GRAFT #22: LK Losses
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


# ============================================================
# Previous grafts abbreviated
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
# ULTIMATE FRANKEN DRAFT MODEL v8 — DART + SSD + LK + LTD
# ============================================================
class UltimateFrankenDraftModelV8(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.hidden_size = config['hidden_size']
        self.num_layers = config['num_hidden_layers']
        self.target_layers = config['target_layer_ids']
        self.block_size = config['block_size']
        
        self.fc = nn.Linear(len(self.target_layers) * self.hidden_size, self.hidden_size, bias=False)
        self.hidden_norm = AdaptiveRMSNorm(self.hidden_size, eps=config['rms_norm_eps'])
        
        # Transformer layers
        self.layers = nn.ModuleList([
            nn.TransformerEncoderLayer(
                d_model=config['hidden_size'],
                nhead=config['num_attention_heads'],
                dim_feedforward=config['intermediate_size'],
                batch_first=True
            )
            for _ in range(self.num_layers)
        ])
        
        # FRANKEN GRAFT #24: DART
        self.dart = DARTParallelDraft(self.hidden_size, config['vocab_size'], num_positions=8)
        
        # FRANKEN GRAFT #23: SSD
        self.ssd = SSDSpeculator(self.hidden_size, config['vocab_size'], num_outcomes=4)
        
        # FRANKEN GRAFT #25: LTD
        self.ltd = AdaptiveDraftPolicy(self.hidden_size, max_depth=16)
        
        self.norm = AdaptiveRMSNorm(self.hidden_size, eps=config['rms_norm_eps'])
        
        self.embed_tokens = None
        self.lm_head = None
    
    def set_shared_weights(self, embed_tokens, lm_head):
        self.embed_tokens = embed_tokens
        self.lm_head = lm_head
    
    def forward(self, input_ids, target_hidden_states, attention_mask=None):
        hidden_states = self.embed_tokens(input_ids)
        
        bsz, seq_len, _ = hidden_states.size()
        
        target_combined = target_hidden_states.permute(1, 2, 0, 3).reshape(bsz, seq_len, -1)
        target_combined = self.fc(target_combined)
        target_combined = self.hidden_norm(target_combined)
        
        for layer in self.layers:
            hidden_states = layer(hidden_states)
        
        hidden_states = self.norm(hidden_states)
        
        # FRANKEN GRAFT #24: DART
        dart_logits = self.dart(hidden_states)
        
        # FRANKEN GRAFT #23: SSD
        ssd_outcome, ssd_preemptive, ssd_conf = self.ssd(hidden_states)
        
        # FRANKEN GRAFT #25: LTD
        depth_probs, exit_prob, confidence = self.ltd(hidden_states)
        
        # Primary logits
        primary_logits = self.lm_head(hidden_states)
        
        return primary_logits, dart_logits, ssd_outcome, ssd_preemptive, ssd_conf, depth_probs, exit_prob, confidence


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
    parser.add_argument("--num-layers", type=int, default=8)
    parser.add_argument("--use-dart", action="store_true", default=True)
    parser.add_argument("--use-ssd", action="store_true", default=True)
    parser.add_argument("--use-ltd", action="store_true", default=True, help="Enable LTD RL policy")
    parser.add_argument("--use-lk-loss", action="store_true", default=True)
    parser.add_argument("--lk-loss-weight", type=float, default=1.0)
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
    }
    
    print("=" * 70)
    print("ULTIMATE FRANKEN DRAFT MODEL v8 — DART + SSD + LK + LTD")
    print("DART: Jan 2026 | SSD: Tri Dao ICLR 2026 | LK: Feb 2026 | LTD: Mar 2026")
    print("=" * 70)
    print(f"Layers: {config['num_hidden_layers']}")
    print(f"DART positions: 8")
    print(f"SSD outcomes: 4")
    print(f"LTD depth: 16")
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
    
    print("Creating Franken draft model v8...")
    draft_model = UltimateFrankenDraftModelV8(config).cuda().bfloat16()
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
            
            # Forward
            primary_logits, dart_logits, ssd_outcome, ssd_preemptive, ssd_conf, depth_probs, exit_prob, confidence = draft_model(
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
            
            # DART losses
            loss_dart = 0
            if args.use_dart and len(dart_logits) > 0:
                for i, dart_logit in enumerate(dart_logits):
                    shift_dart = dart_logit[..., :-1, :].contiguous()
                    shift_dart_labels = torch.cat([
                        input_ids[..., i+1:].contiguous(),
                        torch.zeros(bsz, i, dtype=torch.long, device='cuda')
                    ], dim=-1)
                    loss_dart += F.cross_entropy(
                        shift_dart.reshape(-1, shift_dart.size(-1)),
                        shift_dart_labels.reshape(-1),
                        ignore_index=0,
                    )
                loss_dart = loss_dart / len(dart_logits)
            
            # SSD losses
            loss_ssd = 0
            if args.use_ssd:
                ssd_outcome_shift = ssd_outcome[:, :-1, :]
                outcome_target = torch.zeros(bsz, max_len-1, dtype=torch.long, device='cuda')
                loss_ssd += F.cross_entropy(
                    ssd_outcome_shift.reshape(-1, ssd_outcome_shift.size(-1)),
                    outcome_target.reshape(-1),
                    ignore_index=0,
                )
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
            
            # LTD losses (RL-style)
            loss_ltd = 0
            if args.use_ltd:
                # Reward: higher confidence when prediction is correct
                pred_tokens = primary_logits.argmax(dim=-1)
                correct_mask = (pred_tokens[..., :-1] == shift_labels).float()
                
                # Depth policy loss: prefer deeper speculation when confident
                depth_reward = correct_mask.mean(dim=-1, keepdim=True).unsqueeze(-1)
                loss_ltd += -torch.mean(depth_reward * torch.log(depth_probs[:, :-1, :].mean(dim=-1, keepdim=True) + 1e-6))
                
                # Exit policy loss: exit early when low confidence
                exit_reward = 1.0 - correct_mask.mean(dim=-1, keepdim=True)
                loss_ltd += -torch.mean(exit_reward * torch.log(exit_prob[:, :-1, 0] + 1e-6))
                
                # Confidence calibration
                loss_ltd += F.binary_cross_entropy(
                    confidence[:, :-1, 0],
                    correct_mask.mean(dim=-1)
                )
            
            # Combined loss
            loss = (
                loss_primary + 
                args.lk_loss_weight * loss_lk +
                0.5 * loss_dart +
                0.3 * loss_ssd +
                0.2 * loss_ltd
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
                'dart': f'{loss_dart.item():.4f}' if isinstance(loss_dart, torch.Tensor) else '0.0000',
                'ssd': f'{loss_ssd.item():.4f}' if isinstance(loss_ssd, torch.Tensor) else '0.0000',
                'ltd': f'{loss_ltd.item():.4f}' if isinstance(loss_ltd, torch.Tensor) else '0.0000',
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
