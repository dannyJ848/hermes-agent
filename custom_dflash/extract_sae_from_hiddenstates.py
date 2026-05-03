#!/usr/bin/env python3
"""
Extract SAE features from input_ids using Qwen 27B + SAE integration.
Processes hidden_states_full samples to create SAE feature cache.
"""

import torch
import sys
from pathlib import Path
from tqdm import tqdm
import argparse

sys.path.insert(0, '/data/SpecForge/custom_dflash')
from integrate_qwen_sae import QwenWithSAE

def extract_sae_features_from_hiddenstates(
    hidden_states_dir,
    output_dir,
    qwen_base_path="/data/models/Qwen3.6-27B-Uncensored",
    sae_dir="/data/models/Qwen-Scope",
    max_samples=None,
    batch_size=1
):
    """Extract SAE features from input_ids in hidden_states_full"""
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load Qwen+SAE model
    print("Loading Qwen 27B + SAE integration...")
    print("  (This will take ~4-5 minutes for model loading)")
    model = QwenWithSAE(qwen_base_path, sae_dir, device=device)
    model.eval()
    
    # Find all samples
    hs_path = Path(hidden_states_dir)
    samples = sorted(hs_path.glob("sample_*.pt"))
    
    if max_samples:
        samples = samples[:max_samples]
        
    print(f"Processing {len(samples)} samples...")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Process each sample
    processed = 0
    for sample_path in tqdm(samples, desc="Extracting SAE features"):
        # Load hidden states data
        data = torch.load(sample_path, map_location="cpu")
        
        input_ids = data['input_ids']
        hidden_states = data['hidden_states']  # (5, 684, 5120) - draft model hidden states
        seq_len = data['seq_len']
        
        # Move to device
        input_ids = input_ids.to(device)
        if input_ids.dim() == 1:
            input_ids = input_ids.unsqueeze(0)
            
        # Extract SAE features from Qwen 27B
        with torch.no_grad():
            outputs = model(input_ids=input_ids)
            sae_features = outputs['sae_features']
            
        # Save combined data
        output_file = output_path / sample_path.name
        torch.save({
            'input_ids': input_ids.cpu(),
            'hidden_states': hidden_states,  # Keep draft hidden states
            'sae_features': {k: v.cpu() for k, v in sae_features.items()},  # Qwen SAE features
            'seq_len': seq_len,
        }, output_file)
        
        processed += 1
        
        # Clear cache periodically
        if processed % 100 == 0:
            torch.cuda.empty_cache()
            
    print(f"\nExtracted SAE features for {processed} samples")
    print(f"Saved to {output_dir}")
    
    # Calculate total size
    total_size = sum(f.stat().st_size for f in output_path.glob('*.pt'))
    print(f"Total size: {total_size / 1e9:.1f}GB")
    
    # Estimate per-sample SAE feature size
    if processed > 0:
        sample_size = total_size / processed
        print(f"Per sample: {sample_size / 1e6:.1f}MB")
        print(f"SAE features per sample: ~{64 * 81920 * 4 / 1e6:.1f}MB (64 layers × 81920 features × 4 bytes)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hidden-states-dir", default="/data/SpecForge/custom_dflash/hidden_states_full",
                        help="Directory with sample_*.pt files containing input_ids")
    parser.add_argument("--output-dir", default="/data/SpecForge/custom_dflash/sae_features_full",
                        help="Output directory for SAE features")
    parser.add_argument("--qwen-base", default="/data/models/Qwen3.6-27B-Uncensored")
    parser.add_argument("--sae-dir", default="/data/models/Qwen-Scope")
    parser.add_argument("--max-samples", type=int, help="Limit number of samples")
    parser.add_argument("--batch-size", type=int, default=1)
    
    args = parser.parse_args()
    
    extract_sae_features_from_hiddenstates(
        hidden_states_dir=args.hidden_states_dir,
        output_dir=args.output_dir,
        qwen_base_path=args.qwen_base,
        sae_dir=args.sae_dir,
        max_samples=args.max_samples,
        batch_size=args.batch_size
    )
