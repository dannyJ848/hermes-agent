#!/usr/bin/env python3
"""
Franken V8 Unified Modular Training — All partitions in one process
=====================================================================

Trains core first, then each graft module sequentially.
Core stays in GPU memory throughout. Only one partition active at a time.

Usage:
  python3 train_franken_v8_unified.py --batch-id 2 --hidden-states-dir ... --output-dir ...
"""

import os
import sys
import time
import argparse
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# =============================================================================
# CONSTANTS
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

# =============================================================================
# MODULES (same as modular script)
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
        q = self.q_norm(q)
        k = self.k_norm(k)
        if self.num_heads != self.num_kv_heads:
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
        self.highway_alpha = nn.Parameter(torch.tensor(0.5))
        self.highway_beta = nn.Parameter(torch.tensor(0.5))
    def forward(self, hidden_states, attention_mask=None):
        normed = self.input_layernorm(hidden_states)
        attn_out = self.self_attn(normed, attention_mask)
        hidden_states = self.highway_alpha * hidden_states + self.highway_beta * attn_out
        normed2 = self.post_attention_layernorm(hidden_states)
        mlp_out = self.mlp(normed2)
        hidden_states = self.highway_alpha * hidden_states + self.highway_beta * mlp_out
        return hidden_states

class FrankenV8Core(nn.Module):
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
            bsz, num_aux, seq_len, hid = aux_hidden_states.shape
            aux_flat = aux_hidden_states.permute(0, 2, 1, 3).contiguous().view(bsz, seq_len, -1)
            aux_flat = aux_flat.to(hidden_states.dtype)
            combined = self.fc(aux_flat)
            combined = self.hidden_norm(combined)
            hidden_states = hidden_states + combined
        logits = self.lm_head(hidden_states)
        if return_hidden:
            return {'logits': logits, 'hidden_states': hidden_states}
        return {'logits': logits}

# =============================================================================
# GRAFT MODULES
# =============================================================================

class MTP4Module(nn.Module):
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

class SSDModule(nn.Module):
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
    def __init__(self, hidden_size):
        super().__init__()
        self.policy = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2, bias=True),
            nn.SiLU(),
            nn.Linear(hidden_size // 2, 3, bias=True)
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
    max_len = max(b['input_ids'].shape[0] for b in batch)
    vocab_size = batch[0]['target_logits'].shape[-1]
    input_ids = torch.full((len(batch), max_len), 0, dtype=torch.long)
    target_logits = torch.full((len(batch), max_len, vocab_size), 0.0, dtype=torch.float32)
    aux = None
    if batch[0]['aux_hidden_states'] is not None:
        aux_shape = batch[0]['aux_hidden_states'].shape
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
# TRAINING
# =============================================================================

def train_partition(core, graft_module, dataloader, partition_name, args, device):
    logger = lambda msg: print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    
    # Set train/eval mode
    core.train()
    if graft_module:
        graft_module.train()
    
    # Optimizer — only train graft parameters, core is frozen
    params_to_train = list(graft_module.parameters()) if graft_module else list(core.parameters())
    optimizer = torch.optim.AdamW(params_to_train, lr=args.lr, weight_decay=args.weight_decay)
    
    global_step = 0
    for epoch in range(1000):
        for batch in dataloader:
            if global_step >= args.max_steps:
                break
            
            input_ids = batch['input_ids'].to(device)
            target_logits = batch['target_logits'].to(device)
            aux_hidden = batch['aux_hidden_states'].to(device) if batch['aux_hidden_states'] is not None else None
            
            # Forward through core (get both logits and hidden_states)
            outputs = core(input_ids, aux_hidden, return_hidden=True)
            logits = outputs['logits']
            hidden_states = outputs['hidden_states']
            
            # Primary loss
            loss = nn.functional.kl_div(
                nn.functional.log_softmax(logits, dim=-1),
                nn.functional.softmax(target_logits, dim=-1),
                reduction='batchmean'
            )
            
            # Graft-specific losses
            if partition_name == 'graft_mtp4' and graft_module:
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
            
            elif partition_name == 'graft_pard' and graft_module:
                pard_outputs = graft_module(hidden_states)
                for pard_logit in pard_outputs:
                    loss += 0.05 * nn.functional.kl_div(
                        nn.functional.log_softmax(pard_logit, dim=-1),
                        nn.functional.softmax(target_logits, dim=-1),
                        reduction='batchmean'
                    )
            
            elif partition_name == 'graft_spec' and graft_module:
                ssd_logits = graft_module['ssd'](hidden_states)
                dart_logits = graft_module['dart'](hidden_states, ssd_logits)
                ltd_policy, ltd_value = graft_module['ltd'](hidden_states)
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
                logger(f"  Step {global_step}/{args.max_steps} | Loss: {loss.item():.4f}")
        
        if global_step >= args.max_steps:
            break
    
    return global_step

def save_checkpoint(core, graft_module, step, partition_dir):
    ckpt = {'step': step}
    if partition_dir.name == 'core':
        ckpt['model_state_dict'] = core.state_dict()
    else:
        ckpt['model_state_dict'] = core.state_dict()
        if graft_module:
            ckpt['graft_state_dict'] = graft_module.state_dict()
    
    latest_path = partition_dir / "latest.pt"
    torch.save(ckpt, latest_path, pickle_protocol=4)
    print(f"[{time.strftime('%H:%M:%S')}] Saved: {latest_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-id', type=int, required=True)
    parser.add_argument('--hidden-states-dir', type=str, required=True)
    parser.add_argument('--output-dir', type=str, default='/data/models/FrankenV8-Modular')
    parser.add_argument('--partitions', type=str, default='core,graft_mtp4,graft_pard,graft_spec',
                        help='Comma-separated list of partitions to train')
    parser.add_argument('--core-steps', type=int, default=3000)
    parser.add_argument('--graft-steps', type=int, default=1000)
    parser.add_argument('--lr', type=float, default=0.0001)
    parser.add_argument('--batch-size', type=int, default=1)
    parser.add_argument('--weight-decay', type=float, default=0.01)
    parser.add_argument('--max-grad-norm', type=float, default=1.0)
    parser.add_argument('--bf16', action='store_true', default=True)
    parser.add_argument('--log-interval', type=int, default=10)
    
    args = parser.parse_args()
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger = lambda msg: print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    
    # Create output dir
    batch_dir = Path(args.output_dir) / f"batch_{args.batch_id}"
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    # Dataset
    logger(f"Loading dataset from {args.hidden_states_dir}")
    total_steps_needed = args.core_steps + len(args.partitions.split(',')) * args.graft_steps
    dataset = HiddenStatesDataset(args.hidden_states_dir, max_samples=total_steps_needed * args.batch_size)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=0, pin_memory=True, collate_fn=collate_fn)
    
    # Create core
    logger("Creating FrankenV8 core")
    core = FrankenV8Core().to(device)
    if args.bf16:
        core = core.to(torch.bfloat16)
    
    # Train each partition (fresh start, no checkpoint loading to avoid 28GB load hang)
    
    # Train each partition
    partitions = args.partitions.split(',')
    for partition_name in partitions:
        partition_dir = batch_dir / partition_name
        partition_dir.mkdir(parents=True, exist_ok=True)
        
        logger("="*60)
        logger(f"Training partition: {partition_name}")
        logger(f"{'='*60}")
        
        if partition_name == 'core':
            # Train core (not frozen)
            for p in core.parameters():
                p.requires_grad = True
            graft_module = None
            steps = args.core_steps
        elif partition_name == 'graft_mtp4':
            # Freeze core, train graft
            for p in core.parameters():
                p.requires_grad = False
            graft_module = MTP4Module(HIDDEN_SIZE, VOCAB_SIZE).to(device)
            if args.bf16:
                graft_module = graft_module.to(torch.bfloat16)
            steps = args.graft_steps
        elif partition_name == 'graft_pard':
            for p in core.parameters():
                p.requires_grad = False
            graft_module = PARDModule(HIDDEN_SIZE, VOCAB_SIZE).to(device)
            if args.bf16:
                graft_module = graft_module.to(torch.bfloat16)
            steps = args.graft_steps
        elif partition_name == 'graft_spec':
            for p in core.parameters():
                p.requires_grad = False
            graft_module = nn.ModuleDict({
                'ssd': SSDModule(HIDDEN_SIZE, VOCAB_SIZE).to(device),
                'dart': DARTModule(HIDDEN_SIZE, VOCAB_SIZE).to(device),
                'ltd': LTDModule(HIDDEN_SIZE).to(device),
            }).to(device)
            if args.bf16:
                graft_module = graft_module.to(torch.bfloat16)
            steps = args.graft_steps
        else:
            logger(f"Unknown partition: {partition_name}, skipping")
            continue
        
        # Update args for this partition
        args.max_steps = steps
        
        # Train
        final_step = train_partition(core, graft_module, dataloader, partition_name, args, device)
        
        # Save
        save_checkpoint(core, graft_module, final_step, partition_dir)
        
        # Report size
        if graft_module:
            graft_size = sum(p.numel() * p.element_size() for p in graft_module.parameters()) / (1024**3)
            logger(f"Graft size: {graft_size:.2f} GB")
    
    logger("All partitions complete!")

if __name__ == '__main__':
    main()
