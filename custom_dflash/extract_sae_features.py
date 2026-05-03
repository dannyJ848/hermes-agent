#!/usr/bin/env python3
"""
Pre-extract SAE features from training data using Qwen 27B + SAE integration.
This creates cached SAE features that can be loaded quickly during training.
"""

import torch
import sys
from pathlib import Path
from tqdm import tqdm
import argparse

sys.path.insert(0, '/data/SpecForge/custom_dflash')
from integrate_qwen_sae import QwenWithSAE

def extract_sae_features(
    logits_dir,
    output_dir,
    qwen_base_path="/data/models/Qwen3.6-27B-Uncensored",
    sae_dir="/data/models/Qwen-Scope",
    batch_size=1,
    max_samples=None
):
    """Extract SAE features from pre-extracted logits"""
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load Qwen+SAE model
    print("Loading Qwen 27B + SAE integration...")
    model = QwenWithSAE(qwen_base_path, sae_dir, device=device)
    model.eval()
    
    # Find all samples
    logits_path = Path(logits_dir)
    samples = sorted(logits_path.glob("sample_*.pt"))
    
    if max_samples:
        samples = samples[:max_samples]
        
    print(f"Processing {len(samples)} samples...")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Process each sample
    for i, sample_path in enumerate(tqdm(samples, desc="Extracting SAE features")):
        # Load logits data
        data = torch.load(sample_path, map_location="cpu")
        
        if isinstance(data, dict):
            input_ids = data.get('input_ids')
            logits = data.get('logits')
        else:
            logits = data
            input_ids = None
            
        if input_ids is None:
            # Use argmax from logits as input
            input_ids = torch.argmax(logits, dim=-1)
            
        # Move to device
        input_ids = input_ids.to(device)
        if input_ids.dim() == 1:
            input_ids = input_ids.unsqueeze(0)
            
        # Extract SAE features
        with torch.no_grad():
            outputs = model(input_ids=input_ids)
            sae_features = outputs['sae_features']
            
        # Save SAE features
        output_file = output_path / f"sample_{i:06d}.pt"
        torch.save({
            'input_ids': input_ids.cpu(),
            'sae_features': {k: v.cpu() for k, v in sae_features.items()},
            'logits': logits.cpu() if isinstance(logits, torch.Tensor) else logits,
        }, output_file)
        
    print(f"\nExtracted SAE features for {len(samples)} samples")
    print(f"Saved to {output_dir}")
    print(f"Total size: {sum(f.stat().st_size for f in output_path.glob('*.pt')) / 1e9:.1f}GB")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--logits-dir", required=True, help="Directory with sample_*.pt files")
    parser.add_argument("--output-dir", required=True, help="Output directory for SAE features")
    parser.add_argument("--qwen-base", default="/data/models/Qwen3.6-27B-Uncensored")
    parser.add_argument("--sae-dir", default="/data/models/Qwen-Scope")
    parser.add_argument("--max-samples", type=int, help="Limit number of samples")
    
    args = parser.parse_args()
    
    extract_sae_features(
        logits_dir=args.logits_dir,
        output_dir=args.output_dir,
        qwen_base_path=args.qwen_base,
        sae_dir=args.sae_dir,
        max_samples=args.max_samples
    )
