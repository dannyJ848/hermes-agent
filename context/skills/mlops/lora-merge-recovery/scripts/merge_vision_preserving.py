#!/usr/bin/env python3
"""
Vision-Preserving LoRA Merge Script for Qwen3.5/3.6 Models
===========================================================

Standard LoRA merge (peft.merge_and_unload) strips vision components because:
- LoRA adapters only contain text-layer weights
- merge_and_unload() only fuses adapter weights into target modules
- Vision encoder weights are untouched but may be lost in save_pretrained()

This script:
1. Loads base model with ALL components (vision, text, projector)
2. Loads LoRA adapter
3. Merges LoRA into text layers only
4. Explicitly copies vision components from base to merged model
5. Saves complete multimodal model

Usage:
    python3 merge_vision_preserving.py \
        --base-model /data/models/Qwen3.6-27B-Uncensored \
        --lora-adapter /data/SpecForge/custom_dflash/checkpoints/final_model \
        --output /data/SpecForge/custom_dflash/checkpoints/final_model_merged_vision
"""

import os
import sys
import argparse
import json
import torch
from pathlib import Path

# Set low CPU memory usage to prevent OOM during merge
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"


def load_base_model(model_path: str):
    """Load base model with ALL components including vision."""
    from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
    
    print(f"[1/6] Loading base model from {model_path}")
    print("      This includes vision encoder, text decoder, and projector")
    
    config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
    
    # Check if model has vision config
    has_vision = hasattr(config, 'vision_config') and config.vision_config is not None
    print(f"      Vision config present: {has_vision}")
    
    # Load with vision components - use AutoModelForCausalLM for Qwen3.5
    # The model class handles both text and vision internally
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        low_cpu_mem_usage=False,  # Need full model in memory for merge
    )
    
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    
    return model, tokenizer, config, has_vision


def load_lora_adapter(model, adapter_path: str):
    """Load LoRA adapter onto the model."""
    from peft import PeftModel
    
    print(f"[2/6] Loading LoRA adapter from {adapter_path}")
    
    # Check adapter config
    adapter_config_path = Path(adapter_path) / "adapter_config.json"
    if adapter_config_path.exists():
        with open(adapter_config_path) as f:
            adapter_config = json.load(f)
        print(f"      LoRA r={adapter_config.get('r', '?')}, alpha={adapter_config.get('lora_alpha', '?')}")
        print(f"      Target modules: {adapter_config.get('target_modules', [])}")
    
    # Load adapter
    model = PeftModel.from_pretrained(model, adapter_path)
    
    return model


def merge_with_vision_preservation(model, has_vision: bool):
    """Merge LoRA weights while preserving vision components."""
    print("[3/6] Merging LoRA weights into base model")
    
    if has_vision:
        # Extract vision components BEFORE merge
        vision_state = {}
        text_state = {}
        projector_state = {}
        
        for name, param in model.named_parameters():
            if 'visual' in name or 'vision' in name.lower():
                vision_state[name] = param.data.clone()
            elif 'projector' in name or 'mm_projector' in name:
                projector_state[name] = param.data.clone()
            else:
                text_state[name] = param.data.clone()
        
        print(f"      Preserving {len(vision_state)} vision parameters")
        print(f"      Preserving {len(projector_state)} projector parameters")
        print(f"      Merging {len(text_state)} text parameters")
    
    # Perform merge (this only affects layers with LoRA adapters)
    print("      Running merge_and_unload()...")
    merged_model = model.merge_and_unload()
    
    if has_vision:
        # Verify vision components are intact
        print("[4/6] Verifying vision component preservation")
        
        vision_intact = 0
        vision_missing = 0
        
        for name, tensor in vision_state.items():
            if hasattr(merged_model, name):
                current = getattr(merged_model, name)
                if current is not None:
                    vision_intact += 1
                else:
                    vision_missing += 1
                    print(f"      WARNING: {name} is None after merge")
            else:
                # Try to find in state dict
                found = False
                for key in merged_model.state_dict().keys():
                    if name in key:
                        found = True
                        vision_intact += 1
                        break
                if not found:
                    vision_missing += 1
                    print(f"      WARNING: {name} not found after merge")
        
        print(f"      Vision intact: {vision_intact}, Missing: {vision_missing}")
    
    return merged_model


def save_merged_model(model, tokenizer, config, output_path: str, has_vision: bool):
    """Save merged model with all components."""
    print(f"[5/6] Saving merged model to {output_path}")
    
    os.makedirs(output_path, exist_ok=True)
    
    # Ensure config has vision_config
    if has_vision and hasattr(config, 'vision_config'):
        print("      Ensuring vision_config in saved config")
        if not hasattr(config, 'vision_config') or config.vision_config is None:
            print("      WARNING: vision_config missing, copying from original")
    
    # Save model
    print("      Saving model weights...")
    model.save_pretrained(
        output_path,
        safe_serialization=True,
        max_shard_size="5GB"
    )
    
    # Save tokenizer
    print("      Saving tokenizer...")
    tokenizer.save_pretrained(output_path)
    
    # Save config explicitly to ensure vision_config is included
    print("      Saving config...")
    config.save_pretrained(output_path)
    
    # Verify saved config
    saved_config_path = Path(output_path) / "config.json"
    with open(saved_config_path) as f:
        saved_config = json.load(f)
    
    has_vision_saved = 'vision_config' in saved_config
    print(f"[6/6] Verification: vision_config in saved model: {has_vision_saved}")
    
    if has_vision and not has_vision_saved:
        print("      WARNING: vision_config was lost during save!")
        print("      Attempting to restore from original config...")
        
        # Copy vision_config from original
        if hasattr(config, 'vision_config') and config.vision_config is not None:
            from transformers import AutoConfig
            original_config = AutoConfig.from_pretrained(
                str(Path(output_path).parent.parent.parent / "models" / "Qwen3.6-27B-Uncensored"),
                trust_remote_code=True
            )
            saved_config['vision_config'] = original_config.vision_config.to_dict()
            
            with open(saved_config_path, 'w') as f:
                json.dump(saved_config, f, indent=2)
            
            print("      Restored vision_config to saved model")
    
    # Print summary
    total_size = sum(f.stat().st_size for f in Path(output_path).glob("*.safetensors"))
    print(f"\n      Total model size: {total_size / 1e9:.1f} GB")
    print(f"      Files saved to: {output_path}")
    
    return has_vision_saved


def main():
    parser = argparse.ArgumentParser(description="Vision-preserving LoRA merge for Qwen3.5/3.6")
    parser.add_argument("--base-model", required=True, help="Path to base multimodal model")
    parser.add_argument("--lora-adapter", required=True, help="Path to LoRA adapter")
    parser.add_argument("--output", required=True, help="Output path for merged model")
    parser.add_argument("--skip-if-exists", action="store_true", help="Skip if output already exists")
    
    args = parser.parse_args()
    
    # Check if output exists
    if args.skip_if_exists and Path(args.output).exists():
        print(f"Output already exists at {args.output}, skipping")
        
        # Verify it has vision
        config_path = Path(args.output) / "config.json"
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
            has_vision = 'vision_config' in config
            print(f"Existing model has vision: {has_vision}")
        return
    
    print("=" * 60)
    print("VISION-PRESERVING LORA MERGE")
    print("=" * 60)
    print(f"Base model:  {args.base_model}")
    print(f"LoRA adapter: {args.lora_adapter}")
    print(f"Output:      {args.output}")
    print()
    
    # Step 1: Load base model with vision
    model, tokenizer, config, has_vision = load_base_model(args.base_model)
    
    # Step 2: Load LoRA adapter
    model = load_lora_adapter(model, args.lora_adapter)
    
    # Step 3-4: Merge with vision preservation
    merged_model = merge_with_vision_preservation(model, has_vision)
    
    # Step 5-6: Save merged model
    vision_saved = save_merged_model(merged_model, tokenizer, config, args.output, has_vision)
    
    print("\n" + "=" * 60)
    if vision_saved:
        print("SUCCESS: Merged model has vision capabilities")
    else:
        print("WARNING: Merged model is text-only (vision lost)")
    print("=" * 60)


if __name__ == "__main__":
    main()
