#!/usr/bin/env python3
"""
Convert custom DFlash checkpoint to vLLM-compatible DFlash format.
Matches the structure of Qwen3.6-35B-A3B-DFlash.
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
    
    # Build proper DFlash config matching Qwen3.6-35B-A3B-DFlash format
    dflash_config = {
        "architectures": ["DFlashDraftModel"],
        "attention_bias": False,
        "attention_dropout": 0.0,
        "auto_map": {
            "AutoModel": "dflash.DFlashDraftModel"
        },
        "block_size": config.get("block_size", 16),
        "dflash_config": {
            "mask_token_id": 248077,  # Qwen3.6-27B mask token
            "target_layer_ids": config.get("target_layer_ids", [1, 16, 31, 46, 61])
        },
        "dtype": "bfloat16",
        "head_dim": config.get("head_dim", 213),
        "hidden_act": "silu",
        "hidden_size": config.get("hidden_size", 5120),
        "initializer_range": 0.02,
        "intermediate_size": config.get("intermediate_size", 13824),
        "max_position_embeddings": 262144,
        "model_type": "qwen3",
        "num_attention_heads": config.get("num_attention_heads", 24),
        "num_hidden_layers": config.get("num_hidden_layers", 5),
        "num_key_value_heads": config.get("num_key_value_heads", 4),
        "num_target_layers": 64,  # Qwen3.6-27B has 64 layers
        "rms_norm_eps": 1e-06,
        "rope_theta": 10000000,
        "tie_word_embeddings": False,
        "transformers_version": "4.57.1",
        "use_cache": False,
        "vocab_size": 152064,
    }
    
    # Save config
    with open(os.path.join(args.output_dir, "config.json"), "w") as f:
        json.dump(dflash_config, f, indent=2)
    
    # Save model weights
    try:
        from safetensors.torch import save_file
        save_file(state_dict, os.path.join(args.output_dir, "model.safetensors"))
        print("Saved as Safetensors")
    except ImportError:
        torch.save(state_dict, os.path.join(args.output_dir, "pytorch_model.bin"))
        print("Saved as PyTorch checkpoint")
    
    # Copy tokenizer from target model
    import shutil
    tokenizer_files = ["tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"]
    for fname in tokenizer_files:
        src = os.path.join(args.target_model_path, fname)
        if os.path.exists(src):
            shutil.copy2(src, args.output_dir)
            print(f"Copied {fname}")
    
    # Create dflash.py module (copy from existing or create minimal)
    dflash_py = """from typing import Optional
import torch
from torch import nn
from transformers.models.qwen3.modeling_qwen3 import Qwen3RMSNorm, Qwen3Config, Qwen3PreTrainedModel
from transformers.modeling_outputs import CausalLMOutputWithPast

class DFlashDraftModel(Qwen3PreTrainedModel):
    def __init__(self, config):
        super().__init__(config)
        self.config = config
        # Minimal implementation - vLLM loads weights directly
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
    
    def forward(self, input_ids, **kwargs):
        # Placeholder - actual forward is handled by vLLM's DFlash integration
        hidden = self.embed_tokens(input_ids)
        logits = self.lm_head(hidden)
        return CausalLMOutputWithPast(logits=logits)
"""
    with open(os.path.join(args.output_dir, "dflash.py"), "w") as f:
        f.write(dflash_py)
    
    print(f"\nConversion complete! Output: {args.output_dir}")
    print(f"To use with vLLM:")
    print(f'  --speculative-config \'{{"method":"dflash","model":"{args.output_dir}","num_speculative_tokens":15}}\'')

if __name__ == "__main__":
    main()
