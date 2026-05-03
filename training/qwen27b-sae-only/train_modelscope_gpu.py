import os
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
from pathlib import Path
import argparse
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
from tqdm import tqdm
import json

# Force CUDA if available
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

class SimpleSAE(nn.Module):
    """Simple SAE with encoder/decoder weights"""
    def __init__(self, d_model=5120, n_features=81920):
        super().__init__()
        self.d_model = d_model
        self.n_features = n_features
        self.W_enc = nn.Parameter(torch.empty(n_features, d_model))
        self.b_enc = nn.Parameter(torch.empty(n_features))
        self.W_dec = nn.Parameter(torch.empty(d_model, n_features))
        self.b_dec = nn.Parameter(torch.empty(d_model))
        
    def encode(self, x):
        """Encode hidden states to SAE features"""
        # x: [..., d_model]
        # W_enc: [n_features, d_model]
        # b_enc: [n_features]
        acts = F.relu(F.linear(x, self.W_enc, self.b_enc))
        return acts
    
    def decode(self, acts):
        """Decode SAE features back to hidden states"""
        # acts: [..., n_features]
        # W_dec: [d_model, n_features]
        # b_dec: [d_model]
        x = F.linear(acts, self.W_dec, self.b_dec)
        return x
    
    def forward(self, x):
        acts = self.encode(x)
        x_recon = self.decode(acts)
        return x_recon, acts

def load_sae(sae_path, device='cuda', dtype=torch.bfloat16):
    """Load SAE weights from checkpoint, cast to bfloat16"""
    checkpoint = torch.load(sae_path, map_location=device)
    sae = SimpleSAE(d_model=5120, n_features=81920)
    sae.W_enc.data = checkpoint['W_enc'].to(device).to(dtype)
    sae.b_enc.data = checkpoint['b_enc'].to(device).to(dtype)
    sae.W_dec.data = checkpoint['W_dec'].to(device).to(dtype)
    sae.b_dec.data = checkpoint['b_dec'].to(device).to(dtype)
    sae.to(device).to(dtype).eval()
    for p in sae.parameters():
        p.requires_grad = False
    return sae

class FrankenV8ModelScope(nn.Module):
    """Franken V8 draft with ModelScope cross-attention on SAE features"""
    def __init__(self, vocab_size=151936, d_model=5120, num_layers=6, num_heads=16, 
                 d_ff=13824, max_seq_len=8192, sae_dims=[81920, 81920], dropout=0.1):
        super().__init__()
        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads
        
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.pos_embedding = nn.Embedding(max_seq_len, d_model)
        
        # ModelScope cross-attention layers
        self.cross_attn = nn.ModuleList([
            nn.MultiheadAttention(d_model, num_heads, dropout=dropout, batch_first=True)
            for _ in range(num_layers)
        ])
        self.cross_attn_norm = nn.ModuleList([nn.LayerNorm(d_model) for _ in range(num_layers)])
        
        # SAE feature projection layers
        self.sae_proj = nn.ModuleList([
            nn.Linear(sae_dims[i], d_model) for i in range(len(sae_dims))
        ])
        
        # Standard transformer layers
        self.layers = nn.ModuleList([
            FrankenLayer(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])
        
        self.norm = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
        
        # Tie weights
        self.lm_head.weight = self.token_embedding.weight
        
    def forward(self, input_ids, sae_features=None, hidden_states=None):
        B, T = input_ids.shape
        positions = torch.arange(T, device=input_ids.device).unsqueeze(0).expand(B, -1)
        
        x = self.token_embedding(input_ids) + self.pos_embedding(positions)
        
        # Cross-attention with SAE features
        if sae_features is not None and len(sae_features) > 0:
            for i, (cross_attn, cross_norm, sae_proj) in enumerate(
                zip(self.cross_attn, self.cross_attn_norm, self.sae_proj)
            ):
                if i < len(sae_features) and sae_features[i] is not None:
                    sae_feat = sae_features[i].to(x.device)
                    if sae_feat.dtype != x.dtype:
                        sae_feat = sae_feat.to(x.dtype)
                    
                    # Project SAE features to model dimension
                    sae_proj_feat = sae_proj(sae_feat)
                    
                    # Cross-attention: query from x, key/value from SAE features
                    residual = x
                    x = cross_norm(x)
                    attn_out, _ = cross_attn(x, sae_proj_feat, sae_proj_feat)
                    x = residual + attn_out
        
        # Standard transformer layers
        for layer in self.layers:
            x = layer(x)
        
        x = self.norm(x)
        logits = self.lm_head(x)
        return logits

class FrankenLayer(nn.Module):
    def __init__(self, d_model, num_heads, d_ff, dropout=0.1):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(d_model, num_heads, dropout=dropout, batch_first=True)
        self.attn_norm = nn.LayerNorm(d_model)
        self.ff = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout)
        )
        self.ff_norm = nn.LayerNorm(d_model)
    
    def forward(self, x):
        # Self-attention
        residual = x
        x = self.attn_norm(x)
        attn_out, _ = self.self_attn(x, x, x)
        x = residual + attn_out
        
        # Feed-forward
        residual = x
        x = self.ff_norm(x)
        x = residual + self.ff(x)
        return x

class HiddenStateDataset(Dataset):
    def __init__(self, hidden_states_dir, max_seq_len=2048):
        self.hidden_states_dir = Path(hidden_states_dir)
        self.files = sorted(self.hidden_states_dir.glob('sample_*.pt'))
        self.max_seq_len = max_seq_len
        print(f"Found {len(self.files)} hidden state files")
    
    def __len__(self):
        return len(self.files)
    
    def __getitem__(self, idx):
        data = torch.load(self.files[idx], map_location='cpu')
        input_ids = data['input_ids'].long()
        hidden_states = data['hidden_states']
        
        # Truncate/pad to max_seq_len
        seq_len = input_ids.shape[-1]
        if seq_len > self.max_seq_len:
            input_ids = input_ids[:self.max_seq_len]
            if hidden_states.dim() == 3:
                hidden_states = hidden_states[:, :self.max_seq_len, :]
            else:
                hidden_states = hidden_states[:self.max_seq_len, :]
        
        result = {
            'input_ids': input_ids,
            'hidden_states': hidden_states,
            'file_idx': idx
        }
        
        # Only include target_logits if it exists
        if 'target_logits' in data:
            target_logits = data['target_logits']
            if seq_len > self.max_seq_len and target_logits is not None:
                target_logits = target_logits[:self.max_seq_len, :]
            result['target_logits'] = target_logits
        
        return result

def extract_sae_features_batch(qwen_model, saes, input_ids, hidden_states, device='cuda', batch_size=1):
    """Extract SAE features on GPU with memory-efficient batching"""
    B = input_ids.shape[0]
    sae_features = []
    
    # Get Qwen hidden states for SAE layers
    with torch.no_grad():
        # Forward through Qwen to get layer outputs
        outputs = qwen_model(input_ids.to(device), output_hidden_states=True)
        qwen_hidden = outputs.hidden_states  # tuple of (num_layers+1) tensors
        
        # Extract SAE features for specified layers
        for i, (layer_idx, sae) in enumerate(saes):
            # Get hidden state at target layer
            h = qwen_hidden[layer_idx]  # [B, T, d_model]
            
            # Reshape for SAE: [B*T, d_model]
            B_t, T_t, D = h.shape
            h_flat = h.reshape(-1, D)
            
            # Process in chunks if needed
            chunk_size = 4096  # tokens per chunk
            all_acts = []
            for start in range(0, h_flat.shape[0], chunk_size):
                end = min(start + chunk_size, h_flat.shape[0])
                chunk = h_flat[start:end]
                acts = sae.encode(chunk)
                all_acts.append(acts)
            
            acts = torch.cat(all_acts, dim=0)
            acts = acts.reshape(B_t, T_t, -1)
            sae_features.append(acts)
    
    return sae_features

def train(args):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    if device.type == 'cuda':
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    
    # Load tokenizer first (needed for vocab_size)
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.qwen_model, trust_remote_code=True)
    
    # Load Qwen 27B on GPU
    print("Loading Qwen 27B base model...")
    qwen_model = AutoModelForCausalLM.from_pretrained(
        args.qwen_model,
        torch_dtype=torch.bfloat16,
        device_map='auto',
        trust_remote_code=True
    )
    qwen_model.eval()
    for p in qwen_model.parameters():
        p.requires_grad = False
    
    # Load SAEs on GPU
    print("Loading SAE modules...")
    sae_layers = [32, 48]
    saes = []
    for layer_idx in sae_layers:
        sae_path = f"{args.sae_dir}/layer{layer_idx}.sae.pt"
        print(f"  Loading SAE layer {layer_idx} from {sae_path}")
        sae = load_sae(sae_path, device='cuda')
        saes.append((layer_idx, sae))
    
    # Get config from Qwen
    config = AutoConfig.from_pretrained(args.qwen_model, trust_remote_code=True)
    
    # Safe attribute extraction (Qwen3_5Config compatibility)
    hidden_size = getattr(config, 'hidden_size', getattr(config, 'd_model', 4096))
    num_heads = getattr(config, 'num_attention_heads', getattr(config, 'num_heads', 64))
    intermediate_size = getattr(config, 'intermediate_size', getattr(config, 'ffn_dim', 4 * hidden_size))
    
    # Create Franken model
    print("Creating Franken V8 + ModelScope model...")
    franken = FrankenV8ModelScope(
        vocab_size=len(tokenizer),
        d_model=hidden_size,
        num_layers=6,
        num_heads=num_heads,
        d_ff=intermediate_size,
        max_seq_len=8192,
        sae_dims=[81920, 81920]
    ).to(device).to(torch.bfloat16)
    
    # Load pretrained Franken V8 weights if available
    if args.pretrained:
        print(f"Loading pretrained weights from {args.pretrained}")
        checkpoint = torch.load(args.pretrained, map_location=device)
        franken.load_state_dict(checkpoint, strict=False)
    
    # Count parameters
    total_params = sum(p.numel() for p in franken.parameters())
    trainable_params = sum(p.numel() for p in franken.parameters() if p.requires_grad)
    print(f"Total params: {total_params/1e6:.1f}M, Trainable: {trainable_params/1e6:.1f}M")
    # Create dataset and dataloader
    print("Creating dataset...")
    dataset = HiddenStateDataset(args.hidden_states_dir, max_seq_len=2048)
    
    def collate_fn(batch):
        # Find max length in this batch
        max_len = max(item['input_ids'].shape[-1] for item in batch)
        
        padded_batch = {}
        # Only process keys that exist in the data
        keys_to_process = []
        if 'input_ids' in batch[0]:
            keys_to_process.append('input_ids')
        if 'hidden_states' in batch[0]:
            keys_to_process.append('hidden_states')
        if 'target_logits' in batch[0] and batch[0]['target_logits'] is not None:
            keys_to_process.append('target_logits')
        
        for key in keys_to_process:
            tensors = [item[key] for item in batch]
            # Pad each tensor to max_len
            padded = []
            for t in tensors:
                if t.dim() == 1:  # input_ids [seq_len]
                    pad_size = max_len - t.shape[0]
                    if pad_size > 0:
                        t = torch.cat([t, torch.zeros(pad_size, dtype=t.dtype)], dim=0)
                elif t.dim() == 2:  # hidden_states [seq_len, dim] or target_logits [seq_len, vocab]
                    pad_size = max_len - t.shape[0]
                    if pad_size > 0:
                        t = torch.cat([t, torch.zeros(pad_size, t.shape[1], dtype=t.dtype)], dim=0)
                elif t.dim() == 3:  # hidden_states [B, seq_len, dim]
                    pad_size = max_len - t.shape[1]
                    if pad_size > 0:
                        pad = torch.zeros(t.shape[0], pad_size, t.shape[2], dtype=t.dtype)
                        t = torch.cat([t, pad], dim=1)
                padded.append(t)
            
            padded_batch[key] = torch.stack(padded, dim=0)
        
        padded_batch['file_idx'] = torch.tensor([item['file_idx'] for item in batch])
        return padded_batch
    
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=0, collate_fn=collate_fn)
    
    # Optimizer
    optimizer = torch.optim.AdamW(franken.parameters(), lr=args.lr, weight_decay=0.01)
    
    # Training loop
    franken.train()
    global_step = 0
    
    print(f"\nStarting training for {args.num_steps} steps...")
    pbar = tqdm(total=args.num_steps, desc="Training")
    
    while global_step < args.num_steps:
        for batch in dataloader:
            if global_step >= args.num_steps:
                break
            
            input_ids = batch['input_ids'].to(device)
            
            # Extract SAE features on-the-fly with Qwen on GPU
            with torch.no_grad():
                sae_features = extract_sae_features_batch(
                    qwen_model, saes, input_ids, batch['hidden_states'], 
                    device=device, batch_size=args.batch_size
                )
            
            # Forward through Franken
            logits = franken(input_ids, sae_features=sae_features)
            
            # Compute loss (next-token prediction)
            targets = input_ids[:, 1:].contiguous()
            logits_shifted = logits[:, :-1, :].contiguous()
            
            loss = F.cross_entropy(
                logits_shifted.view(-1, logits_shifted.size(-1)),
                targets.view(-1),
                ignore_index=0
            )
            
            # Backward
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(franken.parameters(), 1.0)
            optimizer.step()
            
            global_step += 1
            pbar.update(1)
            pbar.set_postfix({'loss': f'{loss.item():.4f}'})
            
            # Save checkpoint
            if global_step % args.save_every == 0:
                save_path = f"{args.output_dir}/checkpoint_step_{global_step}.pt"
                torch.save(franken.state_dict(), save_path)
                print(f"\nSaved checkpoint: {save_path}")
            
            # Clear GPU cache periodically
            if global_step % 10 == 0:
                torch.cuda.empty_cache()
    
    pbar.close()
    
    # Save final model
    final_path = f"{args.output_dir}/final_model.pt"
    torch.save(franken.state_dict(), final_path)
    print(f"\nTraining complete! Final model saved to {final_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--qwen-model', default='/data/models/Qwen3.6-27B-Uncensored')
    parser.add_argument('--sae-dir', default='/data/models/Qwen-Scope')
    parser.add_argument('--hidden-states-dir', default='/data/SpecForge/custom_dflash/hidden_states_full')
    parser.add_argument('--pretrained', default='/data/models/FrankenV8-Final/final_model.pt')
    parser.add_argument('--output-dir', default='/data/models/FrankenV8-ModelScope')
    parser.add_argument('--num-steps', type=int, default=3334)
    parser.add_argument('--save-every', type=int, default=500)
    parser.add_argument('--batch-size', type=int, default=1)
    parser.add_argument('--lr', type=float, default=1e-4)
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    train(args)
