#!/usr/bin/env python3
"""
Fast SAE Feature Extractor
Loads all SAEs to CPU, processes samples in batches with minimal GPU transfers.
"""

import torch
import torch.nn as nn
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path
from tqdm import tqdm
import argparse

class SimpleSAE(nn.Module):
    """Lightweight SAE for feature extraction"""
    def __init__(self, d_model=5120, d_sae=81920):
        super().__init__()
        self.W_enc = nn.Parameter(torch.zeros(d_model, d_sae))
        self.b_enc = nn.Parameter(torch.zeros(d_sae))
        self.W_dec = nn.Parameter(torch.zeros(d_sae, d_model))
        self.b_dec = nn.Parameter(torch.zeros(d_model))
    
    def forward(self, x):
        acts = torch.relu(x @ self.W_enc + self.b_enc)
        return acts  # Return sparse activations only

def extract_sae_features_fast(
    hidden_states_dir,
    output_dir,
    qwen_base_path="/data/models/Qwen3.6-27B-Uncensored",
    sae_dir="/data/models/Qwen-Scope",
    max_samples=None,
    batch_size=4
):
    """Fast SAE feature extraction with CPU-based SAEs"""
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load Qwen base model (for hidden state extraction)
    print("Loading Qwen 27B base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        qwen_base_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        max_memory={0: "100GiB", "cpu": "80GiB"}
    )
    base_model.eval()
    
    # Load all SAEs to CPU memory
    print("Loading SAE modules to CPU...")
    sae_modules = {}
    sae_paths = sorted(Path(sae_dir).glob("layer*.sae.pt"))
    
    for sae_path in tqdm(sae_paths, desc="Loading SAEs"):
        layer_idx = int(sae_path.stem.replace("layer", "").replace(".sae", ""))
        sae_state = torch.load(sae_path, map_location="cpu")
        
        sae = SimpleSAE(d_model=5120, d_sae=81920)
        # Transpose and convert to bf16
        sae.W_enc.data = sae_state['W_enc'].t().to(torch.bfloat16)
        sae.W_dec.data = sae_state['W_dec'].t().to(torch.bfloat16)
        sae.b_enc.data = sae_state['b_enc'].to(torch.bfloat16)
        sae.b_dec.data = sae_state['b_dec'].to(torch.bfloat16)
        
        sae_modules[layer_idx] = sae
        
    print(f"Loaded {len(sae_modules)} SAE modules to CPU")
    
    # Find samples
    hs_path = Path(hidden_states_dir)
    samples = sorted(hs_path.glob("sample_*.pt"))
    if max_samples:
        samples = samples[:max_samples]
    print(f"Processing {len(samples)} samples...")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Process samples
    for i, sample_path in enumerate(tqdm(samples, desc="Extracting")):
        data = torch.load(sample_path, map_location="cpu")
        input_ids = data['input_ids'].to(device)
        if input_ids.dim() == 1:
            input_ids = input_ids.unsqueeze(0)
            
        # Get hidden states from Qwen
        with torch.no_grad():
            outputs = base_model(input_ids, output_hidden_states=True)
            hidden_states = outputs.hidden_states  # Tuple of 65 tensors
            
        # Extract SAE features (process on CPU to save GPU memory)
        sae_features = {}
        for layer_idx, sae in sae_modules.items():
            if layer_idx + 1 < len(hidden_states):
                # Get hidden state for this layer, move to CPU
                layer_hidden = hidden_states[layer_idx + 1].cpu().to(torch.bfloat16)
                # Process on CPU
                with torch.no_grad():
                    acts = sae(layer_hidden)
                sae_features[str(layer_idx)] = acts.cpu()
                
        # Save
        torch.save({
            'input_ids': data['input_ids'],
            'sae_features': sae_features,
            'seq_len': data.get('seq_len', len(data['input_ids']))
        }, output_path / f"sample_{i:06d}.pt")
        
        # Clear GPU cache periodically
        if i % 50 == 0:
            torch.cuda.empty_cache()
            
    print(f"\nDone! Extracted {len(samples)} samples to {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hidden-states-dir", default="/data/SpecForge/custom_dflash/hidden_states_full")
    parser.add_argument("--output-dir", default="/data/SpecForge/custom_dflash/sae_features_full")
    parser.add_argument("--qwen-base", default="/data/models/Qwen3.6-27B-Uncensored")
    parser.add_argument("--sae-dir", default="/data/models/Qwen-Scope")
    parser.add_argument("--max-samples", type=int)
    parser.add_argument("--batch-size", type=int, default=4)
    
    args = parser.parse_args()
    
    extract_sae_features_fast(
        hidden_states_dir=args.hidden_states_dir,
        output_dir=args.output_dir,
        qwen_base_path=args.qwen_base,
        sae_dir=args.sae_dir,
        max_samples=args.max_samples,
        batch_size=args.batch_size
    )
