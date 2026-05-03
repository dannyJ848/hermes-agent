"""
Qwen 27B + Qwen-Scope SAE Enhanced Trainer for Franken V9

Architecture:
1. Franken V9 generates tokens/hidden states
2. Franken V9's hidden states are fed into Qwen-Scope SAEs (via Qwen 27B's SAE hooks)
3. Qwen 27B analyzes SAE features + Franken outputs to generate enhanced targets
4. Franken V9 trains on enhanced targets (not just next-token prediction)

This gives Qwen 27B "X-ray vision" into Franken V9's internals via SAE interpretability.
"""

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
from typing import List, Dict, Tuple, Optional
import gc

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
        acts = F.relu(F.linear(x, self.W_enc, self.b_enc))
        return acts
    
    def decode(self, acts):
        """Decode SAE features back to hidden states"""
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


class SAEHookSystem:
    """
    SAE Hook System that attaches to Qwen 27B's forward pass.
    
    Instead of analyzing Qwen 27B's own activations, this system:
    1. Takes Franken V9's hidden states as input
    2. Routes them through Qwen-Scope SAEs
    3. Returns SAE feature activations for Qwen 27B to analyze
    
    This is the key innovation: Qwen 27B gets SAE-interpretable views of Franken V9's internals.
    """
    
    def __init__(self, saes: List[Tuple[int, SimpleSAE]], device='cuda'):
        self.saes = saes  # List of (layer_idx, sae) tuples
        self.device = device
        self.feature_history = []  # Track feature activations over training
        
    def analyze_franken_states(self, franken_hidden_states: torch.Tensor, 
                               layer_idx: int) -> Dict[str, torch.Tensor]:
        """
        Analyze Franken V9's hidden states using Qwen-Scope SAEs.
        
        Args:
            franken_hidden_states: [B, T, d_model] from Franken V9
            layer_idx: Which layer of Franken V9 these states came from
            
        Returns:
            Dictionary with SAE features, reconstructions, and analysis metrics
        """
        B, T, D = franken_hidden_states.shape
        
        # Flatten for SAE processing
        h_flat = franken_hidden_states.reshape(-1, D)
        
        results = {}
        
        # Process through each SAE (typically layers 32 and 48 of Qwen)
        for sae_layer_idx, sae in self.saes:
            # Encode Franken states through SAE
            acts = sae.encode(h_flat)  # [B*T, n_features]
            
            # Decode back to check reconstruction quality
            h_recon = sae.decode(acts)  # [B*T, d_model]
            
            # Reshape back
            acts = acts.reshape(B, T, -1)  # [B, T, n_features]
            h_recon = h_recon.reshape(B, T, -1)  # [B, T, d_model]
            
            # Compute analysis metrics
            recon_error = F.mse_loss(h_recon, franken_hidden_states)
            feature_sparsity = (acts > 0).float().mean()  # % of active features
            top_features = acts.max(dim=-1).values.mean()  # Average peak activation
            
            results[f'sae_{sae_layer_idx}'] = {
                'features': acts,  # [B, T, n_features]
                'reconstruction': h_recon,  # [B, T, d_model]
                'recon_error': recon_error,
                'sparsity': feature_sparsity,
                'top_feature_activation': top_features,
                'feature_entropy': self._compute_feature_entropy(acts)
            }
        
        return results
    
    def _compute_feature_entropy(self, acts: torch.Tensor) -> torch.Tensor:
        """Compute entropy of feature activations (measure of diversity)"""
        # acts: [B, T, n_features]
        probs = F.softmax(acts, dim=-1)
        entropy = -(probs * torch.log(probs + 1e-10)).sum(dim=-1).mean()
        return entropy
    
    def get_feature_importance(self, sae_idx: int = 0, top_k: int = 100) -> torch.Tensor:
        """Get top-k most important features based on historical activation patterns"""
        if len(self.feature_history) == 0:
            return torch.zeros(top_k)
        
        # Aggregate feature activations over history
        all_acts = torch.stack([h[sae_idx] for h in self.feature_history])
        importance = all_acts.mean(dim=0).mean(dim=0)  # [n_features]
        
        top_k_values, top_k_indices = torch.topk(importance, top_k)
        return top_k_indices


class QwenSAETrainer(nn.Module):
    """
    Qwen 27B enhanced with SAE hooks for training Franken V9.
    
    This model:
    1. Takes Franken V9's outputs as input
    2. Uses SAE hooks to analyze Franken's hidden states
    3. Generates enhanced training targets (not just next-token, but SAE-guided targets)
    """
    
    def __init__(self, qwen_model, sae_hooks: SAEHookSystem, device='cuda'):
        super().__init__()
        self.qwen = qwen_model
        self.sae_hooks = sae_hooks
        self.device = device
        
        # Freeze Qwen weights - we only use it for evaluation
        for p in self.qwen.parameters():
            p.requires_grad = False
        self.qwen.eval()
        
        # Enhanced target generation network
        # This takes SAE features + Qwen's own analysis and produces better targets for Franken
        d_model = 5120
        self.enhancement_proj = nn.Sequential(
            nn.Linear(d_model * 2 + 81920 * 2, d_model),  # Qwen hidden + Franken hidden + 2 SAE feature sets
            nn.GELU(),
            nn.LayerNorm(d_model),
            nn.Linear(d_model, d_model)
        ).to(device).to(torch.bfloat16)
        
    def generate_enhanced_targets(self, input_ids: torch.Tensor, 
                                   franken_hidden: torch.Tensor,
                                   franken_logits: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Generate enhanced training targets for Franken V9.
        
        Args:
            input_ids: [B, T] input tokens
            franken_hidden: [B, T, d_model] Franken V9's hidden states
            franken_logits: [B, T, vocab_size] Franken V9's logits
            
        Returns:
            Dictionary with enhanced targets:
            - 'logits_target': Improved logits target
            - 'hidden_target': Target hidden states
            - 'sae_guidance': SAE feature guidance signal
            - 'quality_score': How good Franken's current output is (0-1)
        """
        B, T = input_ids.shape
        
        # 1. Get Qwen 27B's own analysis of the input
        with torch.no_grad():
            qwen_outputs = self.qwen(input_ids, output_hidden_states=True)
            qwen_hidden = qwen_outputs.hidden_states[-1]  # [B, T, d_model]
            qwen_logits = qwen_outputs.logits  # [B, T, vocab_size]
        
        # 2. Analyze Franken's hidden states through SAE hooks
        sae_analysis = self.sae_hooks.analyze_franken_states(franken_hidden, layer_idx=0)
        
        # 3. Combine Qwen's understanding + SAE analysis of Franken
        # Extract SAE features
        sae_32_features = sae_analysis['sae_32']['features']  # [B, T, n_features]
        sae_48_features = sae_analysis['sae_48']['features']  # [B, T, n_features]
        
        # Compute quality metrics
        recon_error_32 = sae_analysis['sae_32']['recon_error']
        recon_error_48 = sae_analysis['sae_48']['recon_error']
        sparsity_32 = sae_analysis['sae_32']['sparsity']
        sparsity_48 = sae_analysis['sae_48']['sparsity']
        
        # Quality score: how well does Franken align with Qwen's SAE structure?
        # Lower recon error + moderate sparsity = better alignment
        quality_score = torch.exp(-(recon_error_32 + recon_error_48)) * \
                        torch.sigmoid((sparsity_32 + sparsity_48) / 0.1 - 5)
        
        # 4. Generate enhanced targets
        # Combine Qwen's logits with SAE-guided corrections
        combined_input = torch.cat([
            qwen_hidden,  # Qwen's understanding
            franken_hidden,  # Franken's current state
            sae_32_features.mean(dim=1, keepdim=True).expand(-1, T, -1),  # SAE 32 features (broadcasted)
            sae_48_features.mean(dim=1, keepdim=True).expand(-1, T, -1),  # SAE 48 features (broadcasted)
        ], dim=-1)
        
        # Project to get enhancement signal
        enhancement = self.enhancement_proj(combined_input)  # [B, T, d_model]
        
        # Enhanced hidden target: Qwen's hidden + enhancement
        hidden_target = qwen_hidden + 0.1 * enhancement
        
        # Enhanced logits target: blend Qwen's logits with enhancement
        # The enhancement should correct Franken's mistakes
        enhanced_logits = qwen_logits + 0.05 * torch.matmul(enhancement, self.qwen.lm_head.weight.T)
        
        # SAE guidance: which features should Franken activate more/less
        sae_guidance = {
            'target_features_32': sae_32_features,  # Franken should produce these features
            'target_features_48': sae_48_features,
            'feature_importance': self.sae_hooks.get_feature_importance(),
        }
        
        return {
            'logits_target': enhanced_logits,
            'hidden_target': hidden_target,
            'sae_guidance': sae_guidance,
            'quality_score': quality_score,
            'raw_qwen_logits': qwen_logits,
            'sae_metrics': {
                'recon_error_32': recon_error_32,
                'recon_error_48': recon_error_48,
                'sparsity_32': sparsity_32,
                'sparsity_48': sparsity_48,
            }
        }


class FrankenV9WithSAE(nn.Module):
    """
    Franken V9 with SAE-aware architecture.
    
    Key differences from V8:
    1. Can output hidden states at multiple layers for SAE analysis
    2. Has SAE feature prediction heads (learns to predict which features should be active)
    3. Uses SAE guidance during training
    """
    
    def __init__(self, vocab_size=151936, d_model=5120, num_layers=6, num_heads=16,
                 d_ff=13824, max_seq_len=8192, sae_dims=[81920, 81920], 
                 num_sae_layers=2, dropout=0.1):
        super().__init__()
        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads
        self.num_layers = num_layers
        
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.pos_embedding = nn.Embedding(max_seq_len, d_model)
        
        # Transformer layers
        self.layers = nn.ModuleList([
            FrankenV9Layer(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])
        
        # SAE feature prediction heads (at specific layers)
        self.sae_predictors = nn.ModuleDict({
            f'layer_{i}': nn.Sequential(
                nn.Linear(d_model, d_model // 4),
                nn.GELU(),
                nn.Linear(d_model // 4, sae_dims[0] if j < num_sae_layers else sae_dims[-1])
            )
            for j, i in enumerate([2, 4])  # Predict SAE features at layers 2 and 4
        })
        
        self.norm = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
        
        # Tie weights
        self.lm_head.weight = self.token_embedding.weight
        
        # Track hidden states for SAE analysis
        self.return_hidden_states = True
        
    def forward(self, input_ids, sae_guidance=None, return_all_hidden=False):
        B, T = input_ids.shape
        positions = torch.arange(T, device=input_ids.device).unsqueeze(0).expand(B, -1)
        
        x = self.token_embedding(input_ids) + self.pos_embedding(positions)
        
        # Collect hidden states at specific layers for SAE analysis
        all_hidden = []
        sae_predictions = {}
        
        for i, layer in enumerate(self.layers):
            x = layer(x)
            all_hidden.append(x)
            
            # Predict SAE features at designated layers
            if f'layer_{i}' in self.sae_predictors:
                sae_predictions[f'layer_{i}'] = self.sae_predictors[f'layer_{i}'](x)
        
        x = self.norm(x)
        logits = self.lm_head(x)
        
        outputs = {
            'logits': logits,
            'sae_predictions': sae_predictions,
            'final_hidden': x,
        }
        
        if return_all_hidden:
            outputs['all_hidden'] = torch.stack(all_hidden, dim=0)  # [num_layers, B, T, d_model]
        
        # If SAE guidance provided, compute alignment loss component
        if sae_guidance is not None:
            sae_alignment_loss = self._compute_sae_alignment(sae_predictions, sae_guidance)
            outputs['sae_alignment_loss'] = sae_alignment_loss
        
        return outputs
    
    def _compute_sae_alignment(self, sae_predictions: Dict[str, torch.Tensor],
                                  sae_guidance: Dict[str, torch.Tensor]) -> torch.Tensor:
        """Compute how well Franken's predicted SAE features match Qwen's guidance"""
        total_loss = 0.0
        count = 0
        
        for layer_key, pred_features in sae_predictions.items():
            if layer_key in sae_guidance:
                target_features = sae_guidance[layer_key]
                # MSE between predicted and target SAE features
                loss = F.mse_loss(pred_features, target_features)
                total_loss += loss
                count += 1
        
        return total_loss / max(count, 1)


class FrankenV9Layer(nn.Module):
    """Enhanced Franken layer with residual connections and pre-norm"""
    
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
        
        # Additional norm for stability
        self.pre_norm = nn.LayerNorm(d_model)
    
    def forward(self, x):
        # Pre-norm
        x = self.pre_norm(x)
        
        # Self-attention with residual
        residual = x
        x = self.attn_norm(x)
        attn_out, _ = self.self_attn(x, x, x)
        x = residual + attn_out
        
        # Feed-forward with residual
        residual = x
        x = self.ff_norm(x)
        x = residual + self.ff(x)
        
        return x


class EnhancedTrainingDataset(Dataset):
    """Dataset that provides input_ids and optionally pre-computed targets"""
    
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
        
        # Truncate if needed
        if input_ids.shape[-1] > self.max_seq_len:
            input_ids = input_ids[:self.max_seq_len]
        
        result = {
            'input_ids': input_ids,
            'file_idx': idx,
        }
        
        # Include hidden states if available (for pre-computed targets)
        if 'hidden_states' in data:
            h = data['hidden_states']
            if h.dim() == 3 and h.shape[1] > self.max_seq_len:
                h = h[:, :self.max_seq_len, :]
            elif h.dim() == 2 and h.shape[0] > self.max_seq_len:
                h = h[:self.max_seq_len, :]
            result['hidden_states'] = h
        
        return result


def collate_fn(batch):
    """Collate with padding for variable-length sequences"""
    max_len = max(item['input_ids'].shape[-1] for item in batch)
    
    padded_batch = {}
    
    # Pad input_ids
    input_ids_list = []
    for item in batch:
        ids = item['input_ids']
        if ids.shape[-1] < max_len:
            pad_size = max_len - ids.shape[-1]
            ids = torch.cat([ids, torch.zeros(pad_size, dtype=ids.dtype)], dim=0)
        input_ids_list.append(ids)
    padded_batch['input_ids'] = torch.stack(input_ids_list, dim=0)
    
    # Pad hidden states if present
    if 'hidden_states' in batch[0]:
        hidden_list = []
        for item in batch:
            h = item['hidden_states']
            if h.dim() == 2:  # [seq_len, dim]
                if h.shape[0] < max_len:
                    pad_size = max_len - h.shape[0]
                    h = torch.cat([h, torch.zeros(pad_size, h.shape[1], dtype=h.dtype)], dim=0)
            elif h.dim() == 3:  # [B, seq_len, dim]
                if h.shape[1] < max_len:
                    pad_size = max_len - h.shape[1]
                    pad = torch.zeros(h.shape[0], pad_size, h.shape[2], dtype=h.dtype)
                    h = torch.cat([h, pad], dim=1)
            hidden_list.append(h)
        padded_batch['hidden_states'] = torch.stack(hidden_list, dim=0)
    
    padded_batch['file_idx'] = torch.tensor([item['file_idx'] for item in batch])
    return padded_batch


def train_qwen_sae_enhanced(args):
    """
    Main training loop for Qwen+SAE enhanced Franken V9 training.
    
    Flow:
    1. Franken V9 generates outputs
    2. Qwen 27B + SAE hooks analyze Franken's internals
    3. Qwen generates enhanced targets
    4. Franken trains on enhanced targets (logits + hidden + SAE alignment)
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    if device.type == 'cuda':
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    
    # 1. Load tokenizer
    print("\n[1/6] Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.qwen_model, trust_remote_code=True)
    
    # 2. Load Qwen 27B (frozen, for evaluation only)
    print("\n[2/6] Loading Qwen 27B base model (frozen)...")
    qwen_model = AutoModelForCausalLM.from_pretrained(
        args.qwen_model,
        torch_dtype=torch.bfloat16,
        device_map='auto',
        trust_remote_code=True
    )
    qwen_model.eval()
    for p in qwen_model.parameters():
        p.requires_grad = False
    print(f"Qwen loaded: {sum(p.numel() for p in qwen_model.parameters())/1e9:.1f}B params")
    
    # 3. Load Qwen-Scope SAEs
    print("\n[3/6] Loading Qwen-Scope SAE modules...")
    sae_layers = [32, 48]
    saes = []
    for layer_idx in sae_layers:
        sae_path = f"{args.sae_dir}/layer{layer_idx}.sae.pt"
        if os.path.exists(sae_path):
            print(f"  Loading SAE layer {layer_idx}")
            sae = load_sae(sae_path, device='cuda')
            saes.append((layer_idx, sae))
        else:
            print(f"  WARNING: SAE file not found: {sae_path}")
    
    # 4. Create SAE Hook System
    print("\n[4/6] Creating SAE Hook System...")
    sae_hooks = SAEHookSystem(saes, device=device)
    
    # 5. Create Qwen SAE Trainer (enhanced evaluator)
    print("\n[5/6] Creating Qwen+SAE enhanced trainer...")
    qwen_sae_trainer = QwenSAETrainer(qwen_model, sae_hooks, device=device)
    
    # 6. Create Franken V9 (student)
    print("\n[6/6] Creating Franken V9 student model...")
    config = AutoConfig.from_pretrained(args.qwen_model, trust_remote_code=True)
    hidden_size = getattr(config, 'hidden_size', getattr(config, 'd_model', 4096))
    num_heads = getattr(config, 'num_attention_heads', getattr(config, 'num_heads', 64))
    intermediate_size = getattr(config, 'intermediate_size', getattr(config, 'ffn_dim', 4 * hidden_size))
    
    franken = FrankenV9WithSAE(
        vocab_size=len(tokenizer),
        d_model=hidden_size,
        num_layers=args.num_layers,
        num_heads=num_heads,
        d_ff=intermediate_size,
        max_seq_len=8192,
        sae_dims=[81920, 81920],
        num_sae_layers=len(saes)
    ).to(device).to(torch.bfloat16)
    
    # Load pretrained weights if available
    if args.pretrained and os.path.exists(args.pretrained):
        print(f"Loading pretrained weights from {args.pretrained}")
        checkpoint = torch.load(args.pretrained, map_location=device)
        franken.load_state_dict(checkpoint, strict=False)
    
    total_params = sum(p.numel() for p in franken.parameters())
    trainable_params = sum(p.numel() for p in franken.parameters() if p.requires_grad)
    print(f"Franken V9: {total_params/1e6:.1f}M total, {trainable_params/1e6:.1f}M trainable")
    
    # 7. Create dataset
    print("\nCreating dataset...")
    dataset = EnhancedTrainingDataset(args.data_dir, max_seq_len=args.max_seq_len)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, 
                           num_workers=0, collate_fn=collate_fn)
    
    # 8. Optimizer
    optimizer = torch.optim.AdamW(franken.parameters(), lr=args.lr, weight_decay=0.01)
    
    # 9. Training loop
    franken.train()
    global_step = 0
    
    print(f"\n{'='*60}")
    print(f"Starting Qwen+SAE enhanced training for {args.num_steps} steps")
    print(f"{'='*60}\n")
    
    pbar = tqdm(total=args.num_steps, desc="Training")
    
    # Loss tracking
    loss_history = {
        'total': [],
        'logits': [],
        'hidden': [],
        'sae_alignment': [],
        'quality': [],
    }
    
    while global_step < args.num_steps:
        for batch in dataloader:
            if global_step >= args.num_steps:
                break
            
            input_ids = batch['input_ids'].to(device)
            B, T = input_ids.shape
            
            # Forward through Franken V9
            franken_outputs = franken(input_ids, return_all_hidden=True)
            franken_logits = franken_outputs['logits']  # [B, T, vocab_size]
            franken_hidden = franken_outputs['final_hidden']  # [B, T, d_model]
            
            # Get enhanced targets from Qwen+SAE
            with torch.no_grad():
                enhanced_targets = qwen_sae_trainer.generate_enhanced_targets(
                    input_ids, franken_hidden, franken_logits
                )
            
            # Compute multi-component loss
            
            # A. Next-token prediction loss (standard)
            targets = input_ids[:, 1:].contiguous()
            logits_shifted = franken_logits[:, :-1, :].contiguous()
            logits_loss = F.cross_entropy(
                logits_shifted.reshape(-1, logits_shifted.size(-1)),
                targets.reshape(-1),
                ignore_index=0
            )
            
            # B. Hidden state alignment loss (Franken should match Qwen's hidden targets)
            hidden_target = enhanced_targets['hidden_target'][:, :-1, :].contiguous()
            franken_hidden_shifted = franken_hidden[:, :-1, :].contiguous()
            hidden_loss = F.mse_loss(franken_hidden_shifted, hidden_target)
            
            # C. SAE alignment loss (Franken should produce correct SAE features)
            sae_loss = torch.tensor(0.0, device=device)
            if 'sae_alignment_loss' in franken_outputs:
                sae_loss = franken_outputs['sae_alignment_loss']
            
            # D. Quality-weighted loss (better Franken outputs = less correction needed)
            quality_score = enhanced_targets['quality_score']
            # If quality is high, we trust Franken more; if low, we apply stronger correction
            adaptive_weight = 1.0 + (1.0 - quality_score) * 2.0  # 1.0 to 3.0
            
            # Combined loss
            total_loss = (
                logits_loss + 
                args.hidden_weight * hidden_loss + 
                args.sae_weight * sae_loss
            ) * adaptive_weight
            
            # Backward
            optimizer.zero_grad()
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(franken.parameters(), 1.0)
            optimizer.step()
            
            # Track metrics
            loss_history['total'].append(total_loss.item())
            loss_history['logits'].append(logits_loss.item())
            loss_history['hidden'].append(hidden_loss.item())
            loss_history['sae_alignment'].append(sae_loss.item())
            loss_history['quality'].append(quality_score.item())
            
            global_step += 1
            pbar.update(1)
            
            # Update progress bar with detailed metrics
            if global_step % 10 == 0:
                avg_total = np.mean(loss_history['total'][-10:])
                avg_logits = np.mean(loss_history['logits'][-10:])
                avg_hidden = np.mean(loss_history['hidden'][-10:])
                avg_quality = np.mean(loss_history['quality'][-10:])
                pbar.set_postfix({
                    'loss': f'{avg_total:.3f}',
                    'logits': f'{avg_logits:.3f}',
                    'hidden': f'{avg_hidden:.3f}',
                    'quality': f'{avg_quality:.3f}',
                })
            
            # Save checkpoint
            if global_step % args.save_every == 0:
                save_path = f"{args.output_dir}/checkpoint_step_{global_step}.pt"
                torch.save({
                    'model_state_dict': franken.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'global_step': global_step,
                    'loss_history': loss_history,
                }, save_path)
                print(f"\nSaved checkpoint: {save_path}")
            
            # Clear cache periodically
            if global_step % 20 == 0:
                torch.cuda.empty_cache()
                gc.collect()
    
    pbar.close()
    
    # Save final model
    final_path = f"{args.output_dir}/final_model.pt"
    torch.save({
        'model_state_dict': franken.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'global_step': global_step,
        'loss_history': loss_history,
    }, final_path)
    
    # Save loss history
    history_path = f"{args.output_dir}/loss_history.json"
    with open(history_path, 'w') as f:
        json.dump({k: [float(v) for v in vals] for k, vals in loss_history.items()}, f)
    
    print(f"\n{'='*60}")
    print(f"Training complete!")
    print(f"Final model: {final_path}")
    print(f"Loss history: {history_path}")
    print(f"{'='*60}")
    
    return franken, loss_history


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Qwen+SAE Enhanced Franken V9 Training')
    
    # Model paths
    parser.add_argument('--qwen-model', default='/data/models/Qwen3.6-27B-Uncensored',
                       help='Path to Qwen 27B base model')
    parser.add_argument('--sae-dir', default='/data/models/Qwen-Scope',
                       help='Path to Qwen-Scope SAE files')
    parser.add_argument('--data-dir', default='/data/SpecForge/custom_dflash/hidden_states',
                       help='Path to training data')
    parser.add_argument('--pretrained', default='/data/models/FrankenV8-Final/final_model.pt',
                       help='Pretrained Franken weights to initialize from')
    parser.add_argument('--output-dir', default='/data/models/FrankenV9-SAE-Enhanced',
                       help='Output directory for checkpoints')
    
    # Model architecture
    parser.add_argument('--num-layers', type=int, default=6,
                       help='Number of layers in Franken V9')
    
    # Training params
    parser.add_argument('--num-steps', type=int, default=1000,
                       help='Total training steps')
    parser.add_argument('--save-every', type=int, default=100,
                       help='Save checkpoint every N steps')
    parser.add_argument('--batch-size', type=int, default=1,
                       help='Batch size')
    parser.add_argument('--max-seq-len', type=int, default=2048,
                       help='Maximum sequence length')
    parser.add_argument('--lr', type=float, default=1e-4,
                       help='Learning rate')
    parser.add_argument('--hidden-weight', type=float, default=0.5,
                       help='Weight for hidden state alignment loss')
    parser.add_argument('--sae-weight', type=float, default=0.3,
                       help='Weight for SAE alignment loss')
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Run training
    franken, history = train_qwen_sae_enhanced(args)
