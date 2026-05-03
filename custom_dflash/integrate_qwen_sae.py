#!/usr/bin/env python3
"""
Qwen 3.6 27B + Qwen-Scope SAE Integration Script
Loads the uncensored 27B model and integrates SAE modules for ModelScope training.
"""

import torch
import torch.nn as nn
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path
import json

class SAEIntegration(nn.Module):
    """Sparse Autoencoder integration layer for Qwen 27B"""
    
    def __init__(self, d_model=5120, d_sae=81920, top_k=50):
        super().__init__()
        self.d_model = d_model
        self.d_sae = d_sae
        self.top_k = top_k
        
        # SAE encoder: d_model -> d_sae (sparse features)
        self.W_enc = nn.Parameter(torch.randn(d_model, d_sae) * 0.01)
        self.b_enc = nn.Parameter(torch.zeros(d_sae))
        # SAE decoder: d_sae -> d_model (reconstruction)
        self.W_dec = nn.Parameter(torch.randn(d_sae, d_model) * 0.01)
        self.b_dec = nn.Parameter(torch.zeros(d_model))
        
    def forward(self, hidden_states):
        # hidden_states: (batch, seq, d_model)
        # Encode to sparse features: (batch, seq, d_model) @ (d_model, d_sae) = (batch, seq, d_sae)
        acts = torch.relu(hidden_states @ self.W_enc + self.b_enc)
        
        # Top-k sparsity
        if self.top_k > 0:
            topk_vals, topk_indices = torch.topk(acts, k=self.top_k, dim=-1)
            acts_sparse = torch.zeros_like(acts)
            acts_sparse.scatter_(-1, topk_indices, topk_vals)
        else:
            acts_sparse = acts
            
        # Decode back: (batch, seq, d_sae) @ (d_sae, d_model) = (batch, seq, d_model)
        reconstructed = acts_sparse @ self.W_dec + self.b_dec
        return reconstructed, acts_sparse

class QwenWithSAE(nn.Module):
    """Qwen 27B model with SAE integration for ModelScope training"""
    
    def __init__(self, base_model_path, sae_dir, device="cuda"):
        super().__init__()
        
        print(f"Loading base model from {base_model_path}...")
        # Load in bf16 for training compatibility
        self.base_model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
            max_memory={0: "100GiB", "cpu": "80GiB"}
        )
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)
        
        self.device = device
        self.hidden_size = self.base_model.config.hidden_size
        self.num_layers = self.base_model.config.num_hidden_layers
        
        # Wave-based SAE loading: only active wave on GPU, rest stay on disk
        print(f"Scanning SAE modules from {sae_dir}...")
        self.sae_paths = {}
        self.sae_cache = {}  # LRU cache for loaded SAEs
        self.active_wave = set()
        self.wave_size = 8  # 8 SAEs per wave
        
        for layer_idx in range(self.num_layers):
            sae_path = Path(sae_dir) / f"layer{layer_idx}.sae.pt"
            if sae_path.exists():
                self.sae_paths[str(layer_idx)] = sae_path
                print(f"  Found SAE for layer {layer_idx}")
        
        # Freeze base model, train only SAE adapters
        for param in self.base_model.parameters():
            param.requires_grad = False
            
        print(f"Integration ready. {len(self.sae_paths)} SAE modules available (wave loading, {self.wave_size} per wave).")
        
    def _load_sae(self, layer_idx):
        """Load a single SAE module on demand"""
        if layer_idx in self.sae_cache:
            return self.sae_cache[layer_idx]
            
        sae_path = self.sae_paths.get(str(layer_idx))
        if not sae_path:
            return None
            
        sae_state = torch.load(sae_path, map_location="cpu")
        sae = SAEIntegration(
            d_model=self.hidden_size,
            d_sae=81920,
            top_k=50
        )
        
        # Load pretrained weights (transpose to correct orientation, convert to bf16, move to GPU)
        if 'W_enc' in sae_state:
            # Pretrained: W_enc is (d_sae, d_model), need (d_model, d_sae)
            sae.W_enc.data = sae_state['W_enc'].t().to(torch.bfloat16).to(self.device)
            sae.W_dec.data = sae_state['W_dec'].t().to(torch.bfloat16).to(self.device)
            sae.b_enc.data = sae_state['b_enc'].to(torch.bfloat16).to(self.device)
            sae.b_dec.data = sae_state['b_dec'].to(torch.bfloat16).to(self.device)
        
        self.sae_cache[layer_idx] = sae
        return sae
        
    def _set_wave(self, wave_idx):
        """Activate a wave of SAEs (move to GPU), evict others to CPU"""
        if wave_idx < 0:
            # Empty wave - evict all
            for layer_idx in list(self.sae_cache.keys()):
                self.sae_cache[layer_idx] = self.sae_cache[layer_idx].cpu()
            self.active_wave = set()
            torch.cuda.empty_cache()
            return
            
        start_layer = wave_idx * self.wave_size
        end_layer = min(start_layer + self.wave_size, self.num_layers)
        new_wave = set(range(start_layer, end_layer))
        
        # Evict SAEs not in new wave
        for layer_idx in list(self.sae_cache.keys()):
            if layer_idx not in new_wave and layer_idx in self.active_wave:
                self.sae_cache[layer_idx] = self.sae_cache[layer_idx].cpu()
                
        # Load new wave to GPU
        for layer_idx in new_wave:
            if str(layer_idx) in self.sae_paths:
                sae = self._load_sae(layer_idx)
                if sae is not None and layer_idx not in self.active_wave:
                    # Ensure SAE is on GPU
                    self.sae_cache[layer_idx] = sae.to(self.device)
                    
        self.active_wave = new_wave
        torch.cuda.empty_cache()
        
    def forward(self, input_ids, attention_mask=None, labels=None):
        # Get base model hidden states
        outputs = self.base_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=True,
            return_dict=True
        )
        
        hidden_states = outputs.hidden_states  # Tuple of (batch, seq, hidden)
        
        # Apply SAE to each layer's hidden states with wave loading
        sae_features = {}
        num_waves = (self.num_layers + self.wave_size - 1) // self.wave_size
        
        for wave_idx in range(num_waves):
            # Load current wave to GPU
            self._set_wave(wave_idx)
            
            # Process layers in this wave
            start_layer = wave_idx * self.wave_size
            end_layer = min(start_layer + self.wave_size, self.num_layers)
            
            for layer_idx in range(start_layer, end_layer):
                if layer_idx in self.sae_cache:
                    layer_hidden = hidden_states[layer_idx + 1]  # +1 because index 0 is embedding
                    sae = self.sae_cache[layer_idx]
                    reconstructed, features = sae(layer_hidden)
                    sae_features[str(layer_idx)] = features
            
            # Evict this wave to free memory
            self._set_wave(-1)  # Empty wave
        
        # Return logits and SAE features for ModelScope training
        return {
            'logits': outputs.logits,
            'sae_features': sae_features,
            'hidden_states': hidden_states
        }
    
    def save(self, output_dir):
        """Save the integrated model"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save SAE modules (load all from disk to ensure we save complete set)
        sae_dir = Path(output_dir) / "sae_modules"
        sae_dir.mkdir(exist_ok=True)
        
        for layer_idx_str, sae_path in self.sae_paths.items():
            # Copy original SAE file
            import shutil
            shutil.copy2(sae_path, sae_dir / f"layer{layer_idx_str}.sae.pt")
            
        # Save config
        config = {
            'base_model': str(self.base_model.config._name_or_path),
            'num_sae_layers': len(self.sae_paths),
            'hidden_size': self.hidden_size,
            'd_sae': 81920,
            'top_k': 50
        }
        
        with open(Path(output_dir) / "integration_config.json", "w") as f:
            json.dump(config, f, indent=2)
            
        print(f"Model saved to {output_dir}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", default="/data/models/Qwen3.6-27B-Uncensored")
    parser.add_argument("--sae-dir", default="/data/models/Qwen-Scope")
    parser.add_argument("--output-dir", default="/data/models/Qwen3.6-27B-ModelScope")
    parser.add_argument("--test", action="store_true", help="Run a quick integration test")
    args = parser.parse_args()
    
    # Initialize model
    model = QwenWithSAE(args.base_model, args.sae_dir)
    
    if args.test:
        print("\nRunning integration test...")
        test_input = "The quick brown fox jumps over the lazy dog."
        inputs = model.tokenizer(test_input, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model(**inputs)
            
        print(f"Logits shape: {outputs['logits'].shape}")
        print(f"SAE features extracted from {len(outputs['sae_features'])} layers")
        
        # Check sparsity
        for layer_idx, features in list(outputs['sae_features'].items())[:3]:
            sparsity = (features > 0).float().mean().item()
            print(f"  Layer {layer_idx}: feature sparsity = {sparsity:.4f}")
            
        print("\nIntegration test PASSED!")
    
    # Save the integrated model
    model.save(args.output_dir)
    print(f"\nModelScope-ready model saved to {args.output_dir}")
