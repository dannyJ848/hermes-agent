#!/usr/bin/env python3
"""
Convert trained DFlash checkpoint to vLLM-compatible format.

DFlash (our custom training) -> vLLM speculative decoding format

Key steps:
1. Load DFlash checkpoint (PyTorch state_dict)
2. Extract draft model weights
3. Create HuggingFace-compatible model directory
4. Generate config.json with correct architecture
5. Save safetensors format
6. Verify with vLLM
"""

import argparse
import json
import os
import sys
import torch
import torch.nn as nn
from pathlib import Path

try:
    from safetensors.torch import save_file
    HAS_SAFETENSORS = True
except ImportError:
    HAS_SAFETENSORS = False
    print("Warning: safetensors not available, using torch.save")

def load_dflash_checkpoint(checkpoint_path):
    """Load DFlash checkpoint and extract model weights."""
    print(f"Loading checkpoint: {checkpoint_path}")
    
    # Try loading to CPU first to avoid OOM
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    
    if 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
    elif 'state_dict' in checkpoint:
        state_dict = checkpoint['state_dict']
    else:
        state_dict = checkpoint
    
    print(f"Checkpoint keys: {list(checkpoint.keys())}")
    print(f"State dict keys (first 10): {list(state_dict.keys())[:10]}")
    
    return state_dict, checkpoint

def analyze_architecture(state_dict):
    """Analyze the architecture from state dict keys."""
    keys = list(state_dict.keys())
    
    # Count layers
    layer_keys = [k for k in keys if 'layers.' in k]
    num_layers = len(set(k.split('.')[1] for k in layer_keys if k.split('.')[1].isdigit()))
    
    # Get hidden size
    hidden_size = None
    for k in keys:
        if 'embed_tokens' in k or 'lm_head' in k:
            tensor = state_dict[k]
            if len(tensor.shape) >= 2:
                hidden_size = tensor.shape[-1]
                break
    
    # Get vocab size
    vocab_size = None
    for k in keys:
        if 'lm_head' in k or 'embed_tokens' in k:
            tensor = state_dict[k]
            if len(tensor.shape) >= 2:
                vocab_size = tensor.shape[0] if tensor.shape[0] > tensor.shape[1] else tensor.shape[1]
                break
    
    print(f"Architecture analysis:")
    print(f"  Num layers: {num_layers}")
    print(f"  Hidden size: {hidden_size}")
    print(f"  Vocab size: {vocab_size}")
    
    return {
        'num_layers': num_layers,
        'hidden_size': hidden_size,
        'vocab_size': vocab_size,
    }

def create_vllm_compatible_model(state_dict, output_dir, target_model_path, config_overrides=None):
    """Create vLLM-compatible model directory."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Analyze architecture
    arch_info = analyze_architecture(state_dict)
    
    # Load target model config for reference
    target_config_path = os.path.join(target_model_path, 'config.json')
    if os.path.exists(target_config_path):
        with open(target_config_path, 'r') as f:
            target_config = json.load(f)
    else:
        target_config = {}
    
    # Build draft config
    draft_config = {
        'model_type': 'dflash_draft',
        'architectures': ['DFlashDraftModel'],
        'hidden_size': arch_info['hidden_size'] or target_config.get('hidden_size', 5120),
        'num_hidden_layers': arch_info['num_layers'] or 8,
        'num_attention_heads': target_config.get('num_attention_heads', 32),
        'num_key_value_heads': target_config.get('num_key_value_heads', 4),
        'intermediate_size': target_config.get('intermediate_size', 13824),
        'rms_norm_eps': target_config.get('rms_norm_eps', 1e-6),
        'vocab_size': arch_info['vocab_size'] or target_config.get('vocab_size', 152064),
        'max_position_embeddings': target_config.get('max_position_embeddings', 262144),
        'block_size': 16,
        'target_layer_ids': [1, 16, 31, 46, 61],
        'torch_dtype': 'bfloat16',
        'transformers_version': '4.40.0',
    }
    
    if config_overrides:
        draft_config.update(config_overrides)
    
    # Save config
    config_path = os.path.join(output_dir, 'config.json')
    with open(config_path, 'w') as f:
        json.dump(draft_config, f, indent=2)
    print(f"Config saved: {config_path}")
    
    # Save tokenizer files (copy from target)
    import shutil
    for fname in ['tokenizer.json', 'tokenizer_config.json', 'vocab.json', 'merges.txt']:
        src = os.path.join(target_model_path, fname)
        if os.path.exists(src):
            dst = os.path.join(output_dir, fname)
            shutil.copy2(src, dst)
            print(f"Copied: {fname}")
    
    # Save weights
    if HAS_SAFETENSORS:
        weights_path = os.path.join(output_dir, 'model.safetensors')
        save_file(state_dict, weights_path)
        print(f"Weights saved (safetensors): {weights_path}")
    else:
        weights_path = os.path.join(output_dir, 'pytorch_model.bin')
        torch.save(state_dict, weights_path)
        print(f"Weights saved (pytorch): {weights_path}")
    
    # Create modeling file for vLLM
    modeling_code = generate_modeling_code(draft_config)
    modeling_path = os.path.join(output_dir, 'modeling_dflash.py')
    with open(modeling_path, 'w') as f:
        f.write(modeling_code)
    print(f"Modeling code saved: {modeling_path}")
    
    return draft_config

def generate_modeling_code(config):
    """Generate Python modeling code for vLLM integration."""
    
    code = f"""# Auto-generated DFlash modeling code for vLLM integration
import torch
import torch.nn as nn
from transformers import PreTrainedModel, PretrainedConfig

class DFlashConfig(PretrainedConfig):
    model_type = "dflash_draft"
    
    def __init__(self, **kwargs):
        self.hidden_size = {config['hidden_size']}
        self.num_hidden_layers = {config['num_hidden_layers']}
        self.num_attention_heads = {config['num_attention_heads']}
        self.num_key_value_heads = {config['num_key_value_heads']}
        self.intermediate_size = {config['intermediate_size']}
        self.rms_norm_eps = {config['rms_norm_eps']}
        self.vocab_size = {config['vocab_size']}
        self.max_position_embeddings = {config['max_position_embeddings']}
        self.block_size = {config['block_size']}
        self.target_layer_ids = {config['target_layer_ids']}
        super().__init__(**kwargs)

class DFlashDraftModel(PreTrainedModel):
    config_class = DFlashConfig
    
    def __init__(self, config):
        super().__init__(config)
        self.hidden_size = config.hidden_size
        self.num_layers = config.num_hidden_layers
        
        # Shared embeddings (loaded from target model)
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
        
        # Draft layers
        self.layers = nn.ModuleList([
            nn.TransformerEncoderLayer(
                d_model=config.hidden_size,
                nhead=config.num_attention_heads,
                dim_feedforward=config.intermediate_size,
                batch_first=True,
                dropout=0.1
            )
            for _ in range(config.num_hidden_layers)
        ])
        
        self.norm = nn.LayerNorm(config.hidden_size, eps=config.rms_norm_eps)
    
    def forward(self, input_ids, hidden_states=None, attention_mask=None):
        # input_ids: [batch, seq_len]
        # hidden_states: [batch, seq_len, num_layers, hidden] (from target)
        
        x = self.embed_tokens(input_ids)
        
        if hidden_states is not None:
            # Flatten target hidden states
            bsz, seq_len, num_layers, hidden = hidden_states.shape
            target_combined = hidden_states.reshape(bsz, seq_len, -1)
            # Project to hidden_size
            if target_combined.size(-1) != self.hidden_size:
                if not hasattr(self, 'fc'):
                    self.fc = nn.Linear(target_combined.size(-1), self.hidden_size, bias=False).to(x.device)
                target_combined = self.fc(target_combined)
            x = x + target_combined
        
        for layer in self.layers:
            x = layer(x)
        
        x = self.norm(x)
        logits = self.lm_head(x)
        
        return logits
    
    def generate_draft(self, input_ids, target_hidden_states=None, max_new_tokens=16):
        '''Generate draft tokens autoregressively.'''
        generated = []
        
        for _ in range(max_new_tokens):
            logits = self.forward(input_ids, target_hidden_states)
            next_token = logits[:, -1, :].argmax(dim=-1)
            generated.append(next_token.item())
            input_ids = torch.cat([input_ids, next_token.unsqueeze(1)], dim=1)
        
        return generated
"""
    return code

def verify_vllm_compatibility(model_dir):
    """Verify the converted model can be loaded."""
    print("\nVerifying vLLM compatibility...")
    
    try:
        from transformers import AutoModelForCausalLM, AutoConfig
        
        config = AutoConfig.from_pretrained(model_dir, trust_remote_code=True)
        print(f"  Config loaded: {config.model_type}")
        
        # Try loading model
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            torch_dtype=torch.bfloat16,
            device_map='cpu',
            trust_remote_code=True,
        )
        print(f"  Model loaded: {type(model).__name__}")
        
        # Test forward pass
        dummy_input = torch.randint(0, config.vocab_size, (1, 10))
        with torch.no_grad():
            output = model(dummy_input)
        print(f"  Forward pass OK: {output.shape}")
        
        return True
        
    except Exception as e:
        print(f"  Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', type=str, required=True,
                        help='Path to DFlash checkpoint .pt file')
    parser.add_argument('--target-model', type=str, required=True,
                        help='Path to target model directory (for config/tokenizer)')
    parser.add_argument('--output-dir', type=str, required=True,
                        help='Output directory for vLLM-compatible model')
    parser.add_argument('--verify', action='store_true',
                        help='Verify vLLM compatibility after conversion')
    
    args = parser.parse_args()
    
    # Load checkpoint
    state_dict, checkpoint = load_dflash_checkpoint(args.checkpoint)
    
    # Create vLLM-compatible model
    config = create_vllm_compatible_model(
        state_dict,
        args.output_dir,
        args.target_model,
    )
    
    # Verify
    if args.verify:
        success = verify_vllm_compatibility(args.output_dir)
        if not success:
            print("\nVerification failed! Check the model files.")
            sys.exit(1)
    
    print(f"\nConversion complete: {args.output_dir}")
    print(f"\nTo use with vLLM:")
    print(f"  --speculative-config '{spec_config}'")

if __name__ == '__main__':
    main()
