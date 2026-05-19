# Axolotl on DGX Spark GB10 — Session Notes (May 2026)

## Summary

Successfully ran Axolotl 0.16.1 LoRA training on DGX Spark GB10 after multiple dependency and config fixes. The key insight is that axolotl requires a **completely isolated virtual environment** — it cannot coexist with Hermes' torch 2.11.0+cu130.

## Working Setup

### 1. Create Isolated Training Venv

```bash
python3 -m venv ~/train-venv
source ~/train-venv/bin/activate

# Install axolotl (pulls torch 2.8.0 CPU-only as dependency)
pip install axolotl

# OVERWRITE with CUDA torch for GB10
pip uninstall -y torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
```

### 2. Fix Axolotl Bugs

```bash
# Bug 1: Missing whitelist.yaml → FileNotFoundError
touch ~/train-venv/lib/python3.12/site-packages/axolotl/telemetry/whitelist.yaml
echo 'organizations: []' > ~/train-venv/lib/python3.12/site-packages/axolotl/telemetry/whitelist.yaml

# Bug 2: torch.cuda.get_device_capability() called during config validation
# → Requires CUDA torch (fixed by step 1)
```

### 3. Dataset Format Conversion

Axolotl 0.16.1 `chat_template` type requires `{"messages": [...]}` format, NOT `{"input": "...", "output": "..."}`.

**Conversion script:**
```python
import json
from pathlib import Path

def convert_to_messages(input_file, output_file):
    with open(input_file) as f:
        lines = f.readlines()
    with open(output_file, 'w') as f:
        for line in lines:
            data = json.loads(line)
            messages = [
                {'role': 'user', 'content': data['input']},
                {'role': 'assistant', 'content': data['output']}
            ]
            f.write(json.dumps({'messages': messages}) + '\n')
    print(f'Converted {len(lines)} examples to {output_file}')

# Usage
convert_to_messages('tier1-reasoning.jsonl', 'tier1-reasoning-chat.jsonl')
```

### 4. Working Config (axolotl_config.yaml)

```yaml
base_model: /data/SpecForge/custom_dflash/checkpoints/final_model_merged
model_type: AutoModelForCausalLM
load_in_8bit: false
load_in_4bit: false
strict: false

adapter: lora
lora_model_dir:
lora_r: 256
lora_alpha: 512
lora_dropout: 0.05
lora_target_linear: true
lora_fan_in_fan_out: false
lora_target_modules:
  - q_proj
  - k_proj
  - v_proj
  - o_proj
  - gate_proj
  - up_proj
  - down_proj

num_epochs: 2
micro_batch_size: 1
gradient_accumulation_steps: 4
learning_rate: 2.0e-4
lr_scheduler: cosine
warmup_steps: 100
optimizer: adamw_bnb_8bit
weight_decay: 0.0
max_grad_norm: 1.0

sequence_len: 4096
pad_to_sequence_len: true
sample_packing: true

datasets:
  - path: /data/SpecForge/custom_dflash/datasets/tier1-reasoning-chat.jsonl
    type: chat_template
  - path: /data/SpecForge/custom_dflash/datasets/tier2-reasoning-chat.jsonl
    type: chat_template
  - path: /data/SpecForge/custom_dflash/datasets/tier3-health-chat.jsonl
    type: chat_template

val_set_size: 0.02
eval_steps: 200
save_steps: 1000
logging_steps: 10

output_dir: /data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256

bf16: true
fp16: false
tf32: true

gpu_memory_limit: 110Gi

seed: 42
dataloader_num_workers: 2
dataloader_pin_memory: true
```

**Key changes from older configs:**
- REMOVED: `max_packed_sequence_len: 4096` (deprecated in 0.16.1)
- CHANGED: `type: input_output` → `type: chat_template`
- CHANGED: Dataset format `{"input": ..., "output": ...}` → `{"messages": [{"role": "user", ...}, {"role": "assistant", ...}]}`

### 5. Preprocessing

```bash
source ~/train-venv/bin/activate
axolotl preprocess /data/SpecForge/custom_dflash/axolotl_config.yaml
```

- Takes 10-20 minutes for 2.15M examples
- Uses 20 workers by default
- Progress shown in debug.log
- Some warnings about "empty turns" are normal and safe

### 6. Training Launch

```bash
source ~/train-venv/bin/activate
axolotl train /data/SpecForge/custom_dflash/axolotl_config.yaml
```

## Error Signatures and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `FileNotFoundError: whitelist.yaml` | Axolotl bug | `touch .../whitelist.yaml; echo 'organizations: []' > ...` |
| `AssertionError: Torch not compiled with CUDA` | CPU-only torch installed | `pip install torch --index-url https://download.pytorch.org/whl/cu128` |
| `DeprecationWarning: max_packed_sequence_len is no longer supported` | Deprecated config key | Remove `max_packed_sequence_len` from config |
| `KeyError: 'segments'` | Wrong dataset format | Use `messages` not `segments` |
| `ValueError: Messages is null` | Wrong dataset format | Use `messages` array, not `input`/`output` |
| `torchvision::nms does not exist` | torch/torchvision version mismatch | Ensure torch and torchvision versions match |

## Dependencies

| Package | Version | Source |
|---------|---------|--------|
| torch | 2.11.0+cu128 | PyTorch CUDA 12.8 wheel |
| torchvision | 0.26.0+cu128 | PyTorch CUDA 12.8 wheel |
| transformers | 5.5.0 | Axolotl dependency |
| axolotl | 0.16.1 | PyPI |
| bitsandbytes | 0.49.1 | PyPI |
| peft | 0.19.1 | PyPI |

## User Preference

When user must choose between model training and Hermes skill accumulation, prioritize Hermes tinkering. Train only when:
- Datasets are ready and verified
- Training config is validated
- Hermes has a working inference endpoint
- User explicitly requests training first
