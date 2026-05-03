#!/usr/bin/env python3
"""
Franken V8 + ModelScope Training Script
Trains Franken V8 draft model using Qwen 27B + SAE features as context.
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
import sys

# Add integration module path
sys.path.insert(0, '/data/SpecForge/custom_dflash')
from integrate_qwen_sae import QwenWithSAE, SAEIntegration

class ModelScopeCrossAttention(nn.Module):
    """Cross-attention module that uses SAE features to guide draft generation"""
    
    def __init__(self, d_model, d_sae, num_heads=8):
        super().__init__()
        self.d_model = d_model
        self.d_sae = d_sae
        self.num_heads = num_heads
        
        # Project SAE features to model dimension
        self.sae_proj = nn.Linear(d_sae, d_model)
        
        # Cross-attention: draft hidden states attend to SAE features
        self.cross_attn = nn.MultiheadAttention(d_model, num_heads, batch_first=True)
        
        # Layer norm and feedforward
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)
        self.ff = nn.Sequential(
            nn.Linear(d_model, d_model * 4),
            nn.GELU(),
            nn.Linear(d_model * 4, d_model)
        )
        
    def forward(self, hidden_states, sae_features):
        # hidden_states: (batch, seq, d_model)
        # sae_features: (batch, seq, d_sae)
        
        # Project SAE features
        sae_proj = self.sae_proj(sae_features)  # (batch, seq, d_model)
        
        # Cross-attention
        attn_out, _ = self.cross_attn(hidden_states, sae_proj, sae_proj)
        hidden_states = self.ln1(hidden_states + attn_out)
        
        # Feedforward
        ff_out = self.ff(hidden_states)
        hidden_states = self.ln2(hidden_states + ff_out)
        
        return hidden_states

class FrankenV8WithModelScope(nn.Module):
    """Franken V8 draft model enhanced with ModelScope SAE features"""
    
    def __init__(self, franken_model_path, qwen_sae_model, num_grafts=25):
        super().__init__()
        
        # Load Franken V8 model
        print(f"Loading Franken V8 from {franken_model_path}...")
        self.franken_model = torch.load(franken_model_path, map_location="cpu")
        if isinstance(self.franken_model, dict):
            # Handle checkpoint dict
            if 'model_state_dict' in self.franken_model:
                # Need to reconstruct model architecture
                self.franken_base = self._build_franken_base(num_grafts)
                self.franken_base.load_state_dict(self.franken_model['model_state_dict'])
            else:
                self.franken_base = self.franken_model
        else:
            self.franken_base = self.franken_model
            
        # Store Qwen+SAE model (frozen, used for feature extraction)
        self.qwen_sae = qwen_sae_model
        self.qwen_sae.eval()
        for param in self.qwen_sae.parameters():
            param.requires_grad = False
            
        # Get dimensions
        self.d_model = self.qwen_sae.hidden_size  # 5120
        self.d_sae = 81920
        self.vocab_size = self.qwen_sae.base_model.config.vocab_size  # 248320
        
        # ModelScope cross-attention layers (one per draft layer)
        self.num_draft_layers = 6  # Franken V8 has 6 layers
        self.modelscope_layers = nn.ModuleList([
            ModelScopeCrossAttention(self.d_model, self.d_sae)
            for _ in range(self.num_draft_layers)
        ])
        
        # SAE feature aggregator (combines features from multiple layers)
        self.sae_aggregator = nn.Sequential(
            nn.Linear(self.d_sae * 2, self.d_sae),  # Combine 2 key layers
            nn.ReLU(),
            nn.Linear(self.d_sae, self.d_sae)
        )
        
        print(f"ModelScope integration ready:")
        print(f"  Draft layers: {self.num_draft_layers}")
        print(f"  Cross-attention heads: 8")
        print(f"  SAE features per layer: {self.d_sae}")
        
    def _build_franken_base(self, num_grafts):
        """Build Franken V8 base architecture"""
        # This is a placeholder - actual architecture depends on Franken V8
        # For now, use a simple transformer
        from transformers import Qwen3ForCausalLM, Qwen3Config
        config = Qwen3Config(
            vocab_size=248320,
            hidden_size=5120,
            num_hidden_layers=6,
            num_attention_heads=40,
            intermediate_size=27648,
            max_position_embeddings=131072
        )
        return Qwen3ForCausalLM(config)
        
    def forward(self, input_ids, attention_mask=None, labels=None):
        # Get SAE features from Qwen 27B (frozen)
        with torch.no_grad():
            qwen_outputs = self.qwen_sae(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
            sae_features = qwen_outputs['sae_features']
            
        # Aggregate SAE features from key layers (e.g., middle layers)
        # Use layers 32 and 48 (roughly 1/2 and 3/4 through 64 layers)
        key_layers = ['32', '48']
        aggregated_sae = []
        for key in key_layers:
            if key in sae_features:
                aggregated_sae.append(sae_features[key])
                
        if len(aggregated_sae) >= 2:
            # Concatenate and aggregate
            combined = torch.cat(aggregated_sae[:2], dim=-1)  # (batch, seq, d_sae*2)
            sae_context = self.sae_aggregator(combined)  # (batch, seq, d_sae)
        elif len(aggregated_sae) == 1:
            sae_context = aggregated_sae[0]
        else:
            # Fallback: create dummy features
            batch, seq = input_ids.shape
            sae_context = torch.zeros(batch, seq, self.d_sae, device=input_ids.device, dtype=torch.bfloat16)
            
        # Run Franken V8 forward pass
        # Note: This is simplified - actual Franken V8 forward may differ
        hidden_states = self.franken_base.transformer.wte(input_ids)
        
        # Apply ModelScope cross-attention at each layer
        for i, layer in enumerate(self.franken_base.transformer.h):
            hidden_states = layer(hidden_states, attention_mask=attention_mask)[0]
            
            # Inject ModelScope guidance every 2 layers
            if i % 2 == 0 and i // 2 < len(self.modelscope_layers):
                hidden_states = self.modelscope_layers[i // 2](hidden_states, sae_context)
                
        # Final output
        logits = self.franken_base.lm_head(hidden_states)
        
        loss = None
        if labels is not None:
            # Shift for next-token prediction
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            loss = F.cross_entropy(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1),
                ignore_index=-100
            )
            
        return {'logits': logits, 'loss': loss}
        
    def save(self, output_dir, step=None):
        """Save checkpoint"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        checkpoint = {
            'model_state_dict': self.state_dict(),
            'num_grafts': 25,
            'has_modelscope': True,
        }
        
        if step is not None:
            path = Path(output_dir) / f"checkpoint_step{step}.pt"
        else:
            path = Path(output_dir) / "final_model.pt"
            
        torch.save(checkpoint, path)
        print(f"Saved checkpoint to {path}")
        return path

class LogitDataset(Dataset):
    """Dataset for training on pre-extracted logits"""
    
    def __init__(self, logits_dir, hidden_states_dir=None, max_seq_length=2048):
        self.logits_dir = Path(logits_dir)
        self.hidden_states_dir = Path(hidden_states_dir) if hidden_states_dir else None
        self.max_seq_length = max_seq_length
        
        # Find all sample files
        self.samples = sorted(self.logits_dir.glob("sample_*.pt"))
        print(f"Found {len(self.samples)} training samples")
        
    def __len__(self):
        return len(self.samples)
        
    def __getitem__(self, idx):
        # Load logits
        logits_data = torch.load(self.samples[idx], map_location="cpu")
        
        # Extract input_ids and target logits
        if isinstance(logits_data, dict):
            input_ids = logits_data.get('input_ids')
            logits = logits_data.get('logits')
        else:
            # Assume it's just logits tensor
            logits = logits_data
            input_ids = None
            
        # Create labels from logits (argmax for hard targets, or use soft)
        if input_ids is not None:
            labels = input_ids.clone()
        else:
            labels = torch.argmax(logits, dim=-1)
            
        return {
            'input_ids': input_ids if input_ids is not None else labels,
            'labels': labels,
            'target_logits': logits
        }

def train_modelscope_franken(
    franken_model_path,
    qwen_base_path,
    sae_dir,
    logits_dir,
    output_dir,
    batch_size=1,
    num_steps=3334,
    learning_rate=1e-5,
    save_every=500,
    resume_from=None
):
    """Train Franken V8 with ModelScope integration"""
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Initialize Qwen+SAE model (frozen feature extractor)
    print("\n=== Loading Qwen 27B + SAE Integration ===")
    qwen_sae = QwenWithSAE(qwen_base_path, sae_dir, device=device)
    
    # Initialize Franken V8 + ModelScope
    print("\n=== Loading Franken V8 + ModelScope ===")
    model = FrankenV8WithModelScope(franken_model_path, qwen_sae)
    model = model.to(device).to(torch.bfloat16)
    
    # Only train ModelScope layers, freeze draft model
    for param in model.franken_base.parameters():
        param.requires_grad = False
    for param in model.modelscope_layers.parameters():
        param.requires_grad = True
    for param in model.sae_aggregator.parameters():
        param.requires_grad = True
        
    print(f"\nTrainable parameters:")
    total_trainable = 0
    for name, param in model.named_parameters():
        if param.requires_grad:
            total_trainable += param.numel()
            print(f"  {name}: {param.numel():,}")
    print(f"Total trainable: {total_trainable:,}")
    
    # Optimizer
    optimizer = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=learning_rate,
        betas=(0.9, 0.999),
        weight_decay=0.01
    )
    
    # Resume if checkpoint provided
    start_step = 0
    if resume_from and Path(resume_from).exists():
        print(f"\nResuming from {resume_from}")
        checkpoint = torch.load(resume_from, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        start_step = checkpoint.get('step', 0)
        
    # Dataset
    print(f"\n=== Loading Dataset ===")
    dataset = LogitDataset(logits_dir)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # Training loop
    print(f"\n=== Training ===")
    model.train()
    global_step = start_step
    
    pbar = tqdm(total=num_steps, initial=start_step, desc="Training")
    
    while global_step < num_steps:
        for batch in dataloader:
            if global_step >= num_steps:
                break
                
            # Move to device
            input_ids = batch['input_ids'].to(device)
            labels = batch['labels'].to(device)
            
            # Forward pass
            outputs = model(input_ids=input_ids, labels=labels)
            loss = outputs['loss']
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            
            # Logging
            pbar.update(1)
            pbar.set_postfix({'loss': f'{loss.item():.4f}'})
            
            # Save checkpoint
            if (global_step + 1) % save_every == 0:
                model.save(output_dir, step=global_step + 1)
                
            global_step += 1
            
    pbar.close()
    
    # Save final model
    final_path = model.save(output_dir)
    print(f"\nTraining complete! Final model: {final_path}")
    
    return final_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Franken V8 with ModelScope")
    parser.add_argument("--franken-model", required=True, help="Path to Franken V8 model")
    parser.add_argument("--qwen-base", default="/data/models/Qwen3.6-27B-Uncensored", help="Qwen 27B base")
    parser.add_argument("--sae-dir", default="/data/models/Qwen-Scope", help="SAE modules directory")
    parser.add_argument("--logits-dir", required=True, help="Directory with extracted logits")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size")
    parser.add_argument("--num-steps", type=int, default=3334, help="Training steps")
    parser.add_argument("--lr", type=float, default=1e-5, help="Learning rate")
    parser.add_argument("--save-every", type=int, default=500, help="Save checkpoint every N steps")
    parser.add_argument("--resume-from", help="Resume from checkpoint")
    
    args = parser.parse_args()
    
    train_modelscope_franken(
        franken_model_path=args.franken_model,
        qwen_base_path=args.qwen_base,
        sae_dir=args.sae_dir,
        logits_dir=args.logits_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        num_steps=args.num_steps,
        learning_rate=args.lr,
        save_every=args.save_every,
        resume_from=args.resume_from
    )
