#!/usr/bin/env python3
"""
Franken V8 + ModelScope Training Script (Optimized)
Pre-extracts SAE features, then trains with lightweight cross-attention.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
import json
import argparse
from tqdm import tqdm

class ModelScopeCrossAttention(nn.Module):
    """Lightweight cross-attention for SAE features"""
    
    def __init__(self, d_model=5120, d_sae=81920, num_heads=8):
        super().__init__()
        self.d_model = d_model
        self.d_sae = d_sae
        self.num_heads = num_heads
        
        # Project SAE features to model dimension
        self.sae_proj = nn.Linear(d_sae, d_model)
        
        # Cross-attention
        self.cross_attn = nn.MultiheadAttention(d_model, num_heads, batch_first=True)
        
        # Layer norm and feedforward
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)
        self.ff = nn.Sequential(
            nn.Linear(d_model, d_model * 2),
            nn.GELU(),
            nn.Linear(d_model * 2, d_model)
        )
        
    def forward(self, hidden_states, sae_features):
        # hidden_states: (batch, seq, d_model)
        # sae_features: (batch, seq, d_sae)
        sae_proj = self.sae_proj(sae_features)
        attn_out, _ = self.cross_attn(hidden_states, sae_proj, sae_proj)
        hidden_states = self.ln1(hidden_states + attn_out)
        ff_out = self.ff(hidden_states)
        hidden_states = self.ln2(hidden_states + ff_out)
        return hidden_states

class FrankenV8ModelScope(nn.Module):
    """Franken V8 with ModelScope SAE cross-attention"""
    
    def __init__(self, base_model_path, num_layers=6, d_model=5120, d_sae=81920, vocab_size=248320):
        super().__init__()
        
        self.d_model = d_model
        self.d_sae = d_sae
        self.vocab_size = vocab_size
        self.num_layers = num_layers
        
        # Embedding
        self.embedding = nn.Embedding(vocab_size, d_model)
        
        # Transformer layers
        self.layers = nn.ModuleList([
            nn.TransformerEncoderLayer(
                d_model=d_model,
                nhead=16,
                dim_feedforward=d_model * 2,
                batch_first=True,
                dtype=torch.bfloat16
            )
            for _ in range(num_layers)
        ])
        
        # ModelScope cross-attention (every 2 layers)
        self.modelscope_layers = nn.ModuleList([
            ModelScopeCrossAttention(d_model, d_sae)
            for _ in range(num_layers // 2)
        ])
        
        # Output head
        self.ln = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
        
        # SAE aggregator (combines 2 key layers)
        self.sae_aggregator = nn.Sequential(
            nn.Linear(d_sae * 2, d_sae),
            nn.ReLU(),
            nn.Linear(d_sae, d_sae)
        )
        
    def forward(self, input_ids, sae_features=None, labels=None):
        # input_ids: (batch, seq)
        # sae_features: dict of layer_idx -> (batch, seq, d_sae)
        
        hidden = self.embedding(input_ids)
        
        # Process through transformer layers with ModelScope injection
        for i, layer in enumerate(self.layers):
            hidden = layer(hidden)
            
            # Inject ModelScope every 2 layers
            if i % 2 == 0 and sae_features is not None:
                ms_idx = i // 2
                if ms_idx < len(self.modelscope_layers):
                    # Aggregate SAE features from key layers
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
                        sae_context = torch.zeros_like(hidden)
                        
                    hidden = self.modelscope_layers[ms_idx](hidden, sae_context)
        
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

class SAELogitDataset(Dataset):
    """Dataset with pre-extracted SAE features and logits"""
    
    def __init__(self, logits_dir, sae_features_dir=None):
        self.logits_dir = Path(logits_dir)
        self.sae_features_dir = Path(sae_features_dir) if sae_features_dir else None
        
        self.samples = sorted(self.logits_dir.glob("sample_*.pt"))
        print(f"Found {len(self.samples)} samples")
        
    def __len__(self):
        return len(self.samples)
        
    def __getitem__(self, idx):
        data = torch.load(self.samples[idx], map_location="cpu")
        
        if isinstance(data, dict):
            input_ids = data.get('input_ids')
            logits = data.get('logits')
            sae_features = data.get('sae_features')
        else:
            logits = data
            input_ids = None
            sae_features = None
            
        if input_ids is None:
            input_ids = torch.argmax(logits, dim=-1)
            
        result = {
            'input_ids': input_ids,
            'labels': input_ids.clone(),
            'target_logits': logits
        }
        
        if sae_features is not None:
            result['sae_features'] = sae_features
            
        return result

def train():
    parser = argparse.ArgumentParser()
    parser.add_argument("--logits-dir", required=True)
    parser.add_argument("--sae-features-dir", help="Pre-extracted SAE features")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--num-steps", type=int, default=3334)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--save-every", type=int, default=500)
    parser.add_argument("--resume-from")
    args = parser.parse_args()
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Model
    print("Building Franken V8 + ModelScope model...")
    model = FrankenV8ModelScope(
        base_model_path=None,
        num_layers=6,
        d_model=5120,
        d_sae=81920,
        vocab_size=248320
    ).to(device).to(torch.bfloat16)
    
    # Load pretrained Franken V8 weights if available
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
    dataset = SAELogitDataset(args.logits_dir, args.sae_features_dir)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)
    
    # Training
    model.train()
    step = 0
    pbar = tqdm(total=args.num_steps, desc="Training")
    
    while step < args.num_steps:
        for batch in dataloader:
            if step >= args.num_steps:
                break
                
            input_ids = batch['input_ids'].to(device)
            labels = batch['labels'].to(device)
            sae_features = batch.get('sae_features')
            
            if sae_features is not None:
                sae_features = {
                    k: v.to(device).to(torch.bfloat16) 
                    for k, v in sae_features.items()
                }
            
            outputs = model(input_ids, sae_features, labels)
            loss = outputs['loss']
            
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
