#!/usr/bin/env python3
"""
Franken V8 + ModelScope Training (Simplified)
Uses only 2 key SAE layers (32, 48) for ModelScope guidance.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path
import json
import argparse
from tqdm import tqdm

class ModelScopeCrossAttention(nn.Module):
    """Lightweight cross-attention for SAE features"""
    
    def __init__(self, d_model=5120, d_sae=81920, num_heads=8):
        super().__init__()
        self.sae_proj = nn.Linear(d_sae, d_model)
        self.cross_attn = nn.MultiheadAttention(d_model, num_heads, batch_first=True)
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)
        self.ff = nn.Sequential(
            nn.Linear(d_model, d_model * 2),
            nn.GELU(),
            nn.Linear(d_model * 2, d_model)
        )
        
    def forward(self, hidden_states, sae_features):
        sae_proj = self.sae_proj(sae_features)
        attn_out, _ = self.cross_attn(hidden_states, sae_proj, sae_proj)
        hidden_states = self.ln1(hidden_states + attn_out)
        ff_out = self.ff(hidden_states)
        return self.ln2(hidden_states + ff_out)

class SimpleSAE(nn.Module):
    """SAE for feature extraction"""
    def __init__(self, d_model=5120, d_sae=81920):
        super().__init__()
        self.W_enc = nn.Parameter(torch.zeros(d_model, d_sae))
        self.b_enc = nn.Parameter(torch.zeros(d_sae))
        self.W_dec = nn.Parameter(torch.zeros(d_sae, d_model))
        self.b_dec = nn.Parameter(torch.zeros(d_model))
    
    def forward(self, x):
        acts = torch.relu(x @ self.W_enc + self.b_enc)
        return acts

def load_sae_to_cpu(sae_path):
    """Load a single SAE to CPU"""
    sae_state = torch.load(sae_path, map_location="cpu")
    sae = SimpleSAE(d_model=5120, d_sae=81920)
    sae.W_enc.data = sae_state['W_enc'].t().to(torch.bfloat16)
    sae.W_dec.data = sae_state['W_dec'].t().to(torch.bfloat16)
    sae.b_enc.data = sae_state['b_enc'].to(torch.bfloat16)
    sae.b_dec.data = sae_state['b_dec'].to(torch.bfloat16)
    return sae

class FrankenV8ModelScope(nn.Module):
    """Franken V8 with ModelScope (2 key SAE layers)"""
    
    def __init__(self, num_layers=6, d_model=5120, d_sae=81920, vocab_size=248320):
        super().__init__()
        
        self.d_model = d_model
        self.d_sae = d_sae
        self.vocab_size = vocab_size
        self.num_layers = num_layers
        
        # Embedding
        self.embedding = nn.Embedding(vocab_size, d_model)
        
        # Transformer layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=16,
            dim_feedforward=d_model * 2,
            batch_first=True,
            dtype=torch.bfloat16
        )
        self.layers = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # ModelScope cross-attention (one layer, at middle)
        self.modelscope = ModelScopeCrossAttention(d_model, d_sae)
        
        # SAE aggregator (combines 2 key layers)
        self.sae_aggregator = nn.Sequential(
            nn.Linear(d_sae * 2, d_sae),
            nn.ReLU(),
            nn.Linear(d_sae, d_sae)
        )
        
        # Output
        self.ln = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
        
    def forward(self, input_ids, sae_features=None, labels=None):
        hidden = self.embedding(input_ids)
        
        # Run through transformer
        hidden = self.layers(hidden)
        
        # Apply ModelScope if SAE features available
        if sae_features is not None:
            key_layers = ['32', '48']
            aggregated = []
            for key in key_layers:
                if key in sae_features:
                    aggregated.append(sae_features[key])
            
            if len(aggregated) >= 2:
                combined = torch.cat(aggregated[:2], dim=-1)
                sae_context = self.sae_aggregator(combined)
            elif len(aggregated) == 1:
                sae_context = aggregated[0]
            else:
                sae_context = torch.zeros(hidden.size(0), hidden.size(1), self.d_sae, 
                                        device=hidden.device, dtype=hidden.dtype)
                
            hidden = self.modelscope(hidden, sae_context)
        
        hidden = self.ln(hidden)
        logits = self.lm_head(hidden)
        
        loss = None
        if labels is not None:
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            loss = F.cross_entropy(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1),
                ignore_index=-100
            )
            
        return {'logits': logits, 'loss': loss}

def train():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hidden-states-dir", default="/data/SpecForge/custom_dflash/hidden_states_full")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--num-steps", type=int, default=3334)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--save-every", type=int, default=500)
    parser.add_argument("--resume-from")
    parser.add_argument("--qwen-base", default="/data/models/Qwen3.6-27B-Uncensored")
    parser.add_argument("--sae-dir", default="/data/models/Qwen-Scope")
    args = parser.parse_args()
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load Qwen base model (frozen, for hidden states)
    print("Loading Qwen 27B base model...")
    qwen_model = AutoModelForCausalLM.from_pretrained(
        args.qwen_base,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        max_memory={0: "100GiB", "cpu": "80GiB"}
    )
    qwen_model.eval()
    for param in qwen_model.parameters():
        param.requires_grad = False
    
    # Load 2 key SAEs to CPU (only ones we need)
    print("Loading key SAE modules (layers 32, 48)...")
    sae_32 = load_sae_to_cpu(Path(args.sae_dir) / "layer32.sae.pt")
    sae_48 = load_sae_to_cpu(Path(args.sae_dir) / "layer48.sae.pt")
    
    # Model
    print("Building Franken V8 + ModelScope model...")
    model = FrankenV8ModelScope(
        num_layers=6,
        d_model=5120,
        d_sae=81920,
        vocab_size=248320
    ).to(device).to(torch.bfloat16)
    
    # Load pretrained Franken V8 weights
    franken_path = "/data/models/FrankenV8-Final/final_model.pt"
    if Path(franken_path).exists():
        print(f"Loading pretrained Franken V8 from {franken_path}")
        checkpoint = torch.load(franken_path, map_location=device)
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'], strict=False)
        else:
            model.load_state_dict(checkpoint, strict=False)
    
    print(f"Trainable params: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")
    
    # Optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    
    # Dataset
    print("Loading dataset...")
    hs_path = Path(args.hidden_states_dir)
    samples = sorted(hs_path.glob("sample_*.pt"))
    print(f"Found {len(samples)} samples")
    
    # Training
    model.train()
    step = 0
    pbar = tqdm(total=args.num_steps, desc="Training")
    
    while step < args.num_steps:
        for sample_path in samples:
            if step >= args.num_steps:
                break
            
            # Load data
            data = torch.load(sample_path, map_location="cpu")
            input_ids = data['input_ids'].to(device)
            if input_ids.dim() == 1:
                input_ids = input_ids.unsqueeze(0)
            
            # Get Qwen hidden states and extract SAE features
            with torch.no_grad():
                qwen_outputs = qwen_model(input_ids, output_hidden_states=True)
                hidden_states = qwen_outputs.hidden_states
                
                # Extract SAE features for key layers (on CPU)
                sae_features = {}
                if len(hidden_states) > 33:
                    h32 = hidden_states[33].cpu().to(torch.bfloat16)
                    sae_features['32'] = sae_32(h32).to(device)
                if len(hidden_states) > 49:
                    h48 = hidden_states[49].cpu().to(torch.bfloat16)
                    sae_features['48'] = sae_48(h48).to(device)
            
            # Forward pass
            labels = input_ids.clone()
            outputs = model(input_ids, sae_features, labels)
            loss = outputs['loss']
            
            # Backward
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            
            pbar.update(1)
            pbar.set_postfix({'loss': f'{loss.item():.4f}'})
            
            if (step + 1) % args.save_every == 0:
                Path(args.output_dir).mkdir(parents=True, exist_ok=True)
                torch.save({
                    'step': step + 1,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                }, Path(args.output_dir) / f"checkpoint_step{step + 1}.pt")
                
            step += 1
            
    pbar.close()
    
    # Save final
    torch.save({
        'step': step,
        'model_state_dict': model.state_dict(),
    }, Path(args.output_dir) / "final_model.pt")
    
    print(f"Training complete! Saved to {args.output_dir}")

if __name__ == "__main__":
    train()
