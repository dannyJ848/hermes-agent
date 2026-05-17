#!/usr/bin/env python3
"""
Extract logits from hidden states for Franken V8 training.
Run on DGX Spark to generate batch logits from hidden_states_full/.

The hidden state files have:
  - input_ids: [seq_len]
  - hidden_states: [num_layers, seq_len, hidden_size] (5 layers for aux training)
  - seq_len: int

We extract target_logits by taking the LAST layer's hidden states and passing through
Qwen3.6-27B's LM head. Output format matches batch_2_logits/:
  - input_ids, hidden_states (all layers), target_logits, seq_len

Usage:
    python3 extract_logits.py \
        --hidden-states-dir /data/SpecForge/custom_dflash/hidden_states_full \
        --output-dir /data/SpecForge/custom_dflash/batch_1_logits \
        --model-path /data/models/Qwen3.6-27B-Uncensored \
        --num-samples 3333
"""

import argparse
import os
import sys
import torch
from pathlib import Path
from tqdm import tqdm


def extract_logits(
    hidden_states_dir: str,
    output_dir: str,
    model_path: str,
    num_samples: int = None,
):
    """Extract logits from hidden states using the base model's LM head."""
    
    hidden_states_dir = Path(hidden_states_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load model for LM head
    print(f"Loading model from {model_path}...")
    from transformers import AutoModelForCausalLM
    
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    
    # Get all hidden state files
    hidden_state_files = sorted(hidden_states_dir.glob("sample_*.pt"))
    if num_samples:
        hidden_state_files = hidden_state_files[:num_samples]
    
    print(f"Found {len(hidden_state_files)} hidden state files")
    print(f"Output dir: {output_dir}")
    
    # Process each file
    for hs_file in tqdm(hidden_state_files, desc="Extracting logits"):
        try:
            # Load hidden state data
            hs_data = torch.load(str(hs_file), map_location="cpu", weights_only=True)
            hidden_states = hs_data["hidden_states"]  # [num_layers, seq_len, hidden_size]
            input_ids = hs_data["input_ids"]
            seq_len = hs_data.get("seq_len", input_ids.shape[0])
            
            # Take last layer's hidden states for logits
            final_hidden = hidden_states[-1]  # [seq_len, hidden_size]
            
            # Move to GPU and get logits via LM head
            final_hidden = final_hidden.to(model.device).to(torch.bfloat16)
            with torch.no_grad():
                logits = model.lm_head(final_hidden)  # [seq_len, vocab_size]
            
            # Save in same format as batch_2_logits/
            output_file = output_dir / hs_file.name
            torch.save({
                "input_ids": input_ids,
                "hidden_states": hidden_states,  # All layers for aux training
                "target_logits": logits.cpu(),
                "seq_len": seq_len,
            }, str(output_file))
            
        except Exception as e:
            print(f"Error processing {hs_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"Done! Extracted logits to {output_dir}")
    print(f"Total files: {len(list(output_dir.glob('sample_*.pt')))}")


def main():
    parser = argparse.ArgumentParser(description="Extract logits from hidden states")
    parser.add_argument("--hidden-states-dir", required=True, help="Dir with hidden state .pt files")
    parser.add_argument("--output-dir", required=True, help="Output dir for logits")
    parser.add_argument("--model-path", default="/data/models/Qwen3.6-27B-Uncensored", help="Base model path")
    parser.add_argument("--num-samples", type=int, default=None, help="Limit number of samples (e.g., 3333 for Batch 1)")
    
    args = parser.parse_args()
    
    extract_logits(
        hidden_states_dir=args.hidden_states_dir,
        output_dir=args.output_dir,
        model_path=args.model_path,
        num_samples=args.num_samples,
    )


if __name__ == "__main__":
    main()
