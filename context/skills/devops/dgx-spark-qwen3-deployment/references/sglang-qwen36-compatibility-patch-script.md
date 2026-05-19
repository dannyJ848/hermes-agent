# SGLang Qwen3.6 Compatibility Patch Script

**Date:** May 15, 2026
**Purpose:** Reproduction script for the SGLang+Qwen3.6 compatibility investigation. Demonstrates config patching, parallel state init, and weight format mismatch detection.
**Status:** Model instantiates but weights cannot load — weight format mismatch is the blocker.

## Patch Script

Save as `/tmp/sglang_qwen36_patch.py` on the DGX host:

```python
# Patch for SGLang Qwen3.6-27B compatibility
# The issue: SGLang expects config.layers_block_type but Qwen3.6 uses config.layer_types
# Also: SGLang uses 'attention' for full attention, but Qwen3.6 uses 'full_attention'

import json
import os
import sys

# Monkey-patch transformers config loading
_original_from_pretrained = None

def patched_from_pretrained(cls, pretrained_model_name_or_path, **kwargs):
    config = _original_from_pretrained(pretrained_model_name_or_path, **kwargs)
    
    # Handle both Qwen3_5Config and Qwen3_5TextConfig
    if hasattr(config, 'text_config'):
        text_config = config.text_config
    else:
        text_config = config
    
    # Patch layers_block_type -> layer_types
    if hasattr(text_config, 'layer_types') and not hasattr(text_config, 'layers_block_type'):
        print(f"[PATCH] Adding layers_block_type from layer_types", file=sys.stderr)
        text_config.layers_block_type = text_config.layer_types
    
    # Map 'full_attention' to 'attention' for SGLang compatibility
    if hasattr(text_config, 'layers_block_type'):
        mapped = []
        for lt in text_config.layers_block_type:
            if lt == 'full_attention':
                mapped.append('attention')
            else:
                mapped.append(lt)
        text_config.layers_block_type = mapped
        print(f"[PATCH] Mapped full_attention -> attention", file=sys.stderr)
    
    # Ensure rope_theta exists
    if not hasattr(text_config, 'rope_theta'):
        text_config.rope_theta = 10000.0
        print(f"[PATCH] Adding rope_theta = 10000.0", file=sys.stderr)
    
    return config

# Apply patch
from transformers import AutoConfig
_original_from_pretrained = AutoConfig.from_pretrained
AutoConfig.from_pretrained = classmethod(patched_from_pretrained)

# Also patch ALL_DECODER_LAYER_TYPES to accept 'full_attention'
import sglang.srt.models.qwen3_5 as qwen_module
if 'full_attention' not in qwen_module.ALL_DECODER_LAYER_TYPES:
    qwen_module.ALL_DECODER_LAYER_TYPES['full_attention'] = qwen_module.ALL_DECODER_LAYER_TYPES['attention']
    print("[PATCH] Added full_attention to ALL_DECODER_LAYER_TYPES", file=sys.stderr)

print("[PATCH] SGLang Qwen3.6 compatibility patch loaded", file=sys.stderr)
```

## Full Test Script

Save as `/tmp/test_sglang_load.py` on the DGX host:

```python
import sys
sys.path.insert(0, '/tmp')
import sglang_qwen36_patch

import os
os.environ['MASTER_ADDR'] = 'localhost'
os.environ['MASTER_PORT'] = '29500'

import torch
import json
from transformers import AutoConfig

# Initialize torch distributed
if not torch.distributed.is_initialized():
    torch.distributed.init_process_group(backend='gloo', rank=0, world_size=1)

# Initialize parallel state properly
from sglang.srt.distributed.parallel_state import (
    init_distributed_environment,
    initialize_model_parallel
)
init_distributed_environment(
    backend='gloo',
    world_size=1,
    rank=0,
    local_rank=0,
    distributed_init_method='env://'
)
initialize_model_parallel(tensor_model_parallel_size=1, pipeline_model_parallel_size=1)

# Set global server args using the internal function
from sglang.srt.server_args import ServerArgs, _global_server_args
import sglang.srt.server_args as sargs
args = ServerArgs(model_path='/data/models/Qwen3.6-27B-Uncensored')
sargs._global_server_args = args

# Initialize DP attention
from sglang.srt.layers.dp_attention import initialize_dp_attention
from sglang.srt.model_executor.model_runner import ModelConfig
config = AutoConfig.from_pretrained('/data/models/Qwen3.6-27B-Uncensored', trust_remote_code=True)
model_config = ModelConfig(
    model_path='/data/models/Qwen3.6-27B-Uncensored',
    trust_remote_code=True,
)
initialize_dp_attention(args, model_config)

from sglang.srt.models.qwen3_5 import Qwen3_5ForCausalLM

print('Loading config...')
text_config = config.text_config

print(f'Config: {text_config.num_hidden_layers} layers, hidden={text_config.hidden_size}')
print(f'Layer types: {text_config.layers_block_type[:8]}...')

print('Creating model...')
model = Qwen3_5ForCausalLM(text_config)
print(f'Model created! Parameters: {sum(p.numel() for p in model.parameters()) / 1e9:.1f}B')

print('Loading weights...')
from safetensors.torch import load_file

model_path = '/data/models/Qwen3.6-27B-Uncensored'
index_file = os.path.join(model_path, 'model.safetensors.index.json')

with open(index_file) as f:
    index = json.load(f)

weight_map = index['weight_map']
files = set(weight_map.values())
print(f'Found {len(weight_map)} weights in {len(files)} files')

# Load all weights with key mapping
all_weights = {}
for i, file in enumerate(sorted(files)):
    print(f'Loading shard {i+1}/{len(files)}: {file}')
    weights = load_file(os.path.join(model_path, file))
    for key, value in weights.items():
        # Map keys: model.language_model.X -> model.X
        if key.startswith('model.language_model.'):
            new_key = key.replace('model.language_model.', 'model.')
        else:
            new_key = key
        # Strip 'model.' prefix since SGLang model expects 'layers.X' not 'model.layers.X'
        if new_key.startswith('model.layers.'):
            new_key = new_key.replace('model.layers.', 'layers.')
        elif new_key.startswith('model.embed_tokens.'):
            new_key = new_key.replace('model.embed_tokens.', 'embed_tokens.')
        elif new_key.startswith('model.norm.'):
            new_key = new_key.replace('model.norm.', 'norm.')
        all_weights[new_key] = value

print(f'Total weights loaded: {len(all_weights)}')

# Check what keys the model expects vs what we have
params_dict = dict(model.named_parameters(remove_duplicate=False))
print(f'\nModel expects {len(params_dict)} parameters')
print(f'Checkpoint has {len(all_weights)} parameters')

# Find mismatches
model_keys = set(params_dict.keys())
checkpoint_keys = set(all_weights.keys())

missing_in_checkpoint = model_keys - checkpoint_keys
extra_in_checkpoint = checkpoint_keys - model_keys

print(f'\nMissing in checkpoint: {len(missing_in_checkpoint)}')
for k in sorted(list(missing_in_checkpoint)[:10]):
    print(f'  {k}')

print(f'\nExtra in checkpoint: {len(extra_in_checkpoint)}')
for k in sorted(list(extra_in_checkpoint)[:10]):
    print(f'  {k}')

# Attempt to load weights
try:
    loaded = model.load_weights(all_weights.items())
    print(f'\nSuccessfully loaded {len(loaded)} parameters!')
except Exception as e:
    print(f'\nError loading weights: {e}')
```

## Run in Docker

```bash
docker run --rm --gpus all --network host --privileged --ipc host \
  -v /data/models:/data/models \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v /tmp:/tmp \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  lmsysorg/sglang:latest \
  python3 /tmp/test_sglang_load.py
```

## Expected Output

```
[PATCH] Added full_attention to ALL_DECODER_LAYER_TYPES
[PATCH] SGLang Qwen3.6 compatibility patch loaded
[PATCH] Adding layers_block_type from layer_types
[PATCH] Mapped full_attention -> attention
[PATCH] Adding rope_theta = 10000.0
Loading config...
Config: 64 layers, hidden=5120
Layer types: ['linear_attention', 'linear_attention', 'linear_attention', 'attention', ...]
Creating model...
Model created! Parameters: 25.6B
Loading weights...
Found 1199 weights in 15 files
Total weights loaded: 1199

Model expects 754 parameters
Checkpoint has 1199 parameters

Missing in checkpoint: 754
  layers.1.linear_attn.in_proj_qkvz.weight
  layers.11.input_layernorm.weight
  ...

Extra in checkpoint: 1199
  model.layers.1.mlp.up_proj.weight
  model.layers.12.linear_attn.in_proj_b.weight
  ...

Error loading weights: ...
```

## Key Finding

The model **creates successfully** (25.6B params, 754 parameter objects) but **0 parameters load** from checkpoint because:
- Checkpoint uses split weight format (`in_proj_qkv` + `in_proj_z`)
- SGLang expects merged weight format (`in_proj_qkvz`)
- Same pattern for attention QKV (`q_proj`+`k_proj`+`v_proj` vs `qkv_proj`) and MLP (`gate_proj`+`up_proj` vs `gate_up_proj`)

This is a **fundamental weight format incompatibility**, not a config or initialization issue.
