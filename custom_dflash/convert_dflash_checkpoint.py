#!/usr/bin/env python3
"""
Convert custom DFlash checkpoint to vLLM-compatible format.
"""

import argparse
import json
import os
import torch

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--target-model-path", type=str, required=True)
    return parser.parse_args()

def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Loading checkpoint from {args.checkpoint}...")
    checkpoint = torch.load(args.checkpoint, map_location='cpu')
    
    config = checkpoint['config']
    state_dict = checkpoint['model_state_dict']
    
    print(f"Config: {json.dumps(config, indent=2)}")
    
    # Save as Safetensors format for vLLM compatibility
    try:
        from safetensors.torch import save_file
        save_file(state_dict, os.path.join(args.output_dir, "model.safetensors"))
        print("Saved as Safetensors")
    except ImportError:
        torch.save(state_dict, os.path.join(args.output_dir, "pytorch_model.bin"))
        print("Saved as PyTorch checkpoint (safetensors not available)")
    
    # Save config
    with open(os.path.join(args.output_dir, "config.json"), "w") as f:
        json.dump(config, f, indent=2)
    
    # Copy tokenizer from target model
    import shutil
    tokenizer_files = ["tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"]
    for fname in tokenizer_files:
        src = os.path.join(args.target_model_path, fname)
        if os.path.exists(src):
            shutil.copy2(src, args.output_dir)
            print(f"Copied {fname}")
    
    print(f"\nConversion complete! Output: {args.output_dir}")
    print(f"To use with vLLM, add to your speculative config:")
    print(f'  --speculative-config \'{{"method":"dflash","model":"{args.output_dir}","num_speculative_tokens":15}}\'')

if __name__ == "__main__":
    main()
