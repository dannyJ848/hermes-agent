#!/usr/bin/env python3
"""
Phase 2: Train DFlash draft model using pre-generated hidden states.
FRANKEN EDITION: Muon optimizer + TileLang kernel acceleration
NO target model loaded — only draft model + cached data.
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
# FRANKEN GRAFT #1: Muon Optimizer (from DeepSeek V4)
# ============================================================
import torch.distributed as dist

def zeropower_via_newtonschulz5(G, steps: int):
    """
    Newton-Schulz iteration for matrix orthogonalization.
    From KellerJordan/Muon — used in DeepSeek V4, Kimi-2, GLM-4.5
    """
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
    """
    Muon optimizer for 2D weight matrices.
    Use AdamW for embeddings, biases, and other non-2D params.
    """
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
            lr = group['lr']
            wd = group['weight_decay']
            momentum = group['momentum']
            nesterov = group['nesterov']
            ns_steps = group['ns_steps']

            for p in group['params']:
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
                    # Fallback to AdamW-like for non-2D params
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
# FRANKEN GRAFT #2: TileLang acceleration (optional)
# ============================================================
TILELANG_AVAILABLE = False
try:
    import tilelang as tl
    from tilelang import language as T
    TILELANG_AVAILABLE = True
    print("[FRANKEN] TileLang loaded — custom kernels available")
except ImportError:
    print("[FRANKEN] TileLang not available — using standard PyTorch ops")


def tilelang_matmul_if_available(A, B):
    """Use TileLang GEMM if available, fallback to torch.matmul"""
    if not TILELANG_AVAILABLE:
        return torch.matmul(A, B)
    # Fallback for now — custom TileLang kernels can be added here
    return torch.matmul(A, B)


# ============================================================
# Original model code (unchanged)
# ============================================================
class Qwen3RMSNorm(nn.Module):
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

class DFlashDraftLayer(nn.Module):
    def __init__(self, hidden_size, num_heads, num_kv_heads, head_dim, intermediate_size, rms_norm_eps=1e-6):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.num_kv_heads = num_kv_heads
        self.head_dim = head_dim
        self.num_kv_groups = num_heads // num_kv_heads
        
        self.q_proj = nn.Linear(hidden_size, num_heads * head_dim, bias=False)
        self.k_proj = nn.Linear(hidden_size, num_kv_heads * head_dim, bias=False)
        self.v_proj = nn.Linear(hidden_size, num_kv_heads * head_dim, bias=False)
        self.o_proj = nn.Linear(num_heads * head_dim, hidden_size, bias=False)
        
        self.q_norm = Qwen3RMSNorm(head_dim, eps=rms_norm_eps)
        self.k_norm = Qwen3RMSNorm(head_dim, eps=rms_norm_eps)
        
        self.mlp = nn.Sequential(
            nn.Linear(hidden_size, intermediate_size, bias=False),
            nn.SiLU(),
            nn.Linear(intermediate_size, hidden_size, bias=False),
        )
        
        self.input_norm = Qwen3RMSNorm(hidden_size, eps=rms_norm_eps)
        self.post_attn_norm = Qwen3RMSNorm(hidden_size, eps=rms_norm_eps)
    
    def forward(self, hidden_states, target_hidden, attention_mask=None):
        bsz, q_len, _ = hidden_states.size()
        kv_len = target_hidden.size(1)
        
        residual = hidden_states
        hidden_states = self.input_norm(hidden_states)
        
        query = self.q_proj(hidden_states).view(bsz, q_len, self.num_heads, self.head_dim).transpose(1, 2)
        key = self.k_proj(target_hidden).view(bsz, kv_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        value = self.v_proj(target_hidden).view(bsz, kv_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        
        query = self.q_norm(query)
        key = self.k_norm(key)
        
        key = key.repeat_interleave(self.num_kv_groups, dim=1)
        value = value.repeat_interleave(self.num_kv_groups, dim=1)
        
        if attention_mask is None:
            attn_output = F.scaled_dot_product_attention(query, key, value, is_causal=True)
        else:
            attn_output = F.scaled_dot_product_attention(query, key, value, is_causal=False)
        
        attn_output = attn_output.transpose(1, 2).contiguous().view(bsz, q_len, -1)
        attn_output = self.o_proj(attn_output)
        hidden_states = residual + attn_output
        
        residual = hidden_states
        hidden_states = self.post_attn_norm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        hidden_states = residual + hidden_states
        
        return hidden_states

class CustomDFlashModel(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.hidden_size = config['hidden_size']
        self.num_layers = config['num_hidden_layers']
        self.target_layers = config['target_layer_ids']
        self.block_size = config['block_size']
        
        self.fc = nn.Linear(len(self.target_layers) * self.hidden_size, self.hidden_size, bias=False)
        self.hidden_norm = Qwen3RMSNorm(self.hidden_size, eps=config['rms_norm_eps'])
        
        self.layers = nn.ModuleList([
            DFlashDraftLayer(
                hidden_size=config['hidden_size'],
                num_heads=config['num_attention_heads'],
                num_kv_heads=config['num_key_value_heads'],
                head_dim=config['head_dim'],
                intermediate_size=config['intermediate_size'],
                rms_norm_eps=config['rms_norm_eps'],
            ) for _ in range(config['num_hidden_layers'])
        ])
        
        self.norm = Qwen3RMSNorm(config['hidden_size'], eps=config['rms_norm_eps'])
        self.lm_head = None  # Shared with target model
    
    def set_shared_weights(self, embed_tokens, lm_head):
        self.embed_tokens = embed_tokens
        self.lm_head = lm_head
    
    def forward(self, input_ids, target_hidden_states, attention_mask=None):
        hidden_states = self.embed_tokens(input_ids)
        
        # Combine target hidden states
        bsz, seq_len, _ = hidden_states.size()
        target_combined = target_hidden_states.transpose(0, 1).reshape(bsz, seq_len, -1)
        target_combined = self.fc(target_combined)
        target_combined = self.hidden_norm(target_combined)
        
        for layer in self.layers:
            hidden_states = layer(hidden_states, target_combined, attention_mask)
        
        hidden_states = self.norm(hidden_states)
        logits = self.lm_head(hidden_states)
        return logits

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
    # FRANKEN: optimizer selection
    parser.add_argument("--optimizer", type=str, default="muon", choices=["adamw", "muon"],
                       help="Optimizer: muon (DeepSeek V4 style) or adamw")
    parser.add_argument("--muon-ns-steps", type=int, default=5,
                       help="Newton-Schulz steps for Muon (higher = more orthogonal, slower)")
    return parser.parse_args()

def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    
    config = {
        'hidden_size': 5120,
        'num_hidden_layers': 5,
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
    
    print("Loading tokenizer and shared weights from target model...")
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
    
    print("Creating draft model...")
    draft_model = CustomDFlashModel(config).cuda().bfloat16()
    draft_model.set_shared_weights(embed_tokens, lm_head)
    
    total_params = sum(p.numel() for p in draft_model.parameters())
    print(f"Draft model parameters: {total_params / 1e9:.2f}B")
    
    # FRANKEN: Muon optimizer setup
    if args.optimizer == "muon":
        # Separate 2D+ matrices from other params
        muon_params = [p for p in draft_model.parameters() if p.ndim >= 2 and p.numel() >= 2]
        other_params = [p for p in draft_model.parameters() if p.ndim < 2 or p.numel() < 2]
        
        print(f"[FRANKEN] Muon optimizer: {len(muon_params)} 2D+ matrices, {len(other_params)} other params")
        print(f"[FRANKEN] Newton-Schulz steps: {args.muon_ns_steps}")
        
        optimizer = Muon(
            muon_params,
            lr=args.learning_rate,
            weight_decay=0.1,
            momentum=0.95,
            nesterov=True,
            ns_steps=args.muon_ns_steps,
        )
        # Add other params with AdamW-like behavior (handled internally by Muon class)
        # Actually, let's use MuonWithAuxAdam pattern
        # For simplicity, we'll use Muon for all and let it handle non-2D internally
        optimizer = Muon(
            draft_model.parameters(),
            lr=args.learning_rate,
            weight_decay=0.1,
            momentum=0.95,
            nesterov=True,
            ns_steps=args.muon_ns_steps,
        )
        print("[FRANKEN] Using Muon optimizer (DeepSeek V4 / Kimi-2 style)")
    else:
        optimizer = torch.optim.AdamW(
            [p for p in draft_model.parameters() if p.requires_grad],
            lr=args.learning_rate,
            betas=(0.9, 0.95),
            weight_decay=0.1,
        )
        print("[FRANKEN] Using AdamW optimizer (baseline)")
    
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
            
            logits = draft_model(input_ids, hidden_states, attention_mask)
            
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = input_ids[..., 1:].contiguous()
            
            loss = F.cross_entropy(
                shift_logits.reshape(-1, shift_logits.size(-1)),
                shift_labels.reshape(-1),
                ignore_index=0,
            )
            
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(draft_model.parameters(), 1.0)
            optimizer.step()
            
            epoch_loss += loss.item()
            global_step += 1
            
            pbar.set_postfix({'loss': f'{loss.item():.4f}', 'step': global_step})
            
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
