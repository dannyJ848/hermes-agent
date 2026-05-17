# LoRA Merge Recovery — Manual Merge on DGX

**Date:** May 10, 2026
**System:** DGX Spark
**Model:** Qwen3.6-27B-Uncensored + LoRA checkpoint

## Problem

Training script's `merge_and_unload()` fails silently:
- `final_model_merged/` contains only `config.json` + `generation_config.json`
- NO `.safetensors` or `.bin` weight files
- Process logged "Merging LoRA weights..." then died during compilation

## Root Cause

PEFT merge function is called but crashes during execution (OOM, missing config, or compilation failure). No error propagates to log — process just exits.

## Solution: Manual Merge Script

Write merge script to `/tmp/merge_lora.py` on DGX, run via SSH with `nohup`:

```python
import os
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM

base_model_path = '/data/models/Qwen3.6-27B-Uncensored'
adapter_path = '/data/SpecForge/custom_dflash/checkpoints/checkpoint_step_10000'
merged_output = '/data/SpecForge/custom_dflash/checkpoints/final_model_merged'

print(f'Loading base model from: {base_model_path}')
model = AutoModelForCausalLM.from_pretrained(
    base_model_path,
    torch_dtype=torch.bfloat16,
    device_map='auto',
    trust_remote_code=True
)
print('Base model loaded')

print('Loading LoRA adapter...')
model = PeftModel.from_pretrained(model, adapter_path)

print('Merging LoRA weights...')
merged_model = model.merge_and_unload()

print(f'Saving merged model to {merged_output}...')
os.makedirs(merged_output, exist_ok=True)
merged_model.save_pretrained(merged_output)

print('Merge complete!')
print(f'Files: {os.listdir(merged_output)}')
```

## Execution Method

**WRONG — terminal(background=true) over SSH:**
```bash
# This backgrounds on LOCAL machine, not DGX
terminal(background=true, command="ssh djg6228@dgx 'python3 merge.py'")
```

**RIGHT — execute_code with subprocess:**
```python
import subprocess

# Write script
subprocess.run(["ssh", "djg6228@spark-85e8.local", "cat > /tmp/merge_lora.py << 'PYEOF'\n...script...\nPYEOF"])

# Start background process, capture PID
result = subprocess.run(
    ["ssh", "djg6228@spark-85e8.local",
     "nohup python3 /tmp/merge_lora.py > /tmp/merge_lora.log 2>&1 & echo $!"],
    capture_output=True, text=True
)
pid = result.stdout.strip()
```

**Poll progress:**
```bash
ssh djg6228@spark-85e8.local "ps aux | grep merge_lora | grep -v grep; tail -5 /tmp/merge_lora.log"
```

## Common Issues

### Missing adapter_config.json
```bash
# Checkpoint only has adapter_model.bin + optimizer.pt
# Config is in final_model/ directory
ssh djg6228@spark-85e8.local "cp /data/SpecForge/custom_dflash/checkpoints/final_model/adapter_config.json /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_10000/"
```

### Missing LoRA Keys Warning
PEFT warns about missing adapter keys. This is expected when:
- Config targets all layers (64)
- Checkpoint only has attention LoRA on every 4th layer (16 layers: 3,7,11,...,63)
- MLP LoRA is present on all 64 layers

**Verification:**
```python
import torch
ckpt = torch.load("adapter_model.bin", map_location="cpu")
keys = list(ckpt.keys())
# Should show: 384 MLP keys + 128 attention keys = 512 total
```

Merge still succeeds — warning is cosmetic.

## Verification

After merge completes:
```bash
ssh djg6228@spark-85e8.local "ls -lh /data/SpecForge/custom_dflash/checkpoints/final_model_merged/"
```

Expected output:
```
-rw-rw-r-- 1 djg6228 djg6228 2.7K config.json
-rw-rw-r-- 1 djg6228 djg6228  224 generation_config.json
-rw-rw-r-- 1 djg6228 djg6228  47G model-00001-of-00002.safetensors
-rw-rw-r-- 1 djg6228 djg6228 3.7G model-00002-of-00002.safetensors
-rw-rw-r-- 1 djg6228 djg6228  82K model.safetensors.index.json
```

Total: ~51GB. If only config files exist → merge failed.
