# qwen27b-lora-merge-complete

*Researched: 2026-05-10 17:42 CDT*

# Qwen 27B LoRA Merge — Complete Technical Reference

## Overview
Full training pipeline for Qwen3.6-27B-Uncensored with LoRA + SAE + teacher distillation, completed May 10 2026.

## Infrastructure
- **Host**: spark-85e8.local (10.0.0.171)
- **User**: djg6228
- **SSH**: Key auth, passwordless sudo
- **Base Model**: /data/models/Qwen3.6-27B-Uncensored/
- **Training Directory**: /data/SpecForge/custom_dflash/

## Training Configuration
- **Method**: LoRA + SAE + Teacher Distillation
- **Steps**: 10,000/10,000 (100%)
- **LoRA Rank (r)**: 256
- **LoRA Alpha**: 512
- **Dropout**: 0.05
- **Target Modules**: 
  - Config claims: all MLP (gate_proj, up_proj, down_proj) + all attention (q_proj, k_proj, v_proj, o_proj) on all 64 layers
  - Actual checkpoint: MLP on all 64 layers, attention only on every 4th layer (3, 7, 11, 15, 19, 23, 27, 31, 35, 39, 43, 47, 51, 55, 59, 63)

## File Locations

### Checkpoints
```
/data/SpecForge/custom_dflash/checkpoints/
├── checkpoint_step_10000/
│   ├── adapter_model.bin          (4.8GB — LoRA weights)
│   ├── optimizer.pt               (2.4GB)
│   └── adapter_config.json        (copied from final_model/ post-training)
├── final_model/
│   ├── adapter_model.bin
│   └── adapter_config.json        (original training config)
└── final_model_merged/            ← MERGED MODEL (51GB)
    ├── config.json
    ├── generation_config.json
    ├── model-00001-of-00002.safetensors  (47GB)
    ├── model-00002-of-00002.safetensors  (3.7GB)
    └── model.safetensors.index.json      (82K)
```

## Merge Process

### Issue: Silent Merge Failure
The training script's built-in `merge_and_unload()` failed silently — created `final_model_merged/` with only config files, no actual weight files.

### Root Cause
- `checkpoint_step_10000/` was missing `adapter_config.json`
- Peft requires this file to know how to load the adapter

### Solution
1. Copy `adapter_config.json` from `final_model/` to `checkpoint_step_10000/`
2. Run manual merge script on DGX:

```python
import os
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM

base_model_path = '/data/models/Qwen3.6-27B-Uncensored'
adapter_path = '/data/SpecForge/custom_dflash/checkpoints/checkpoint_step_10000'
merged_output = '/data/SpecForge/custom_dflash/checkpoints/final_model_merged'

model = AutoModelForCausalLM.from_pretrained(
    base_model_path,
    torch_dtype=torch.bfloat16,
    device_map='auto',
    trust_remote_code=True
)

model = PeftModel.from_pretrained(model, adapter_path)
merged_model = model.merge_and_unload()
merged_model.save_pretrained(merged_output)
```

### Execution Method
- SSH to DGX, write script to `/tmp/merge_lora.py`
- Run with `nohup python3 /tmp/merge_lora.py > /tmp/merge_lora.log 2>&1 &`
- Poll progress with separate SSH commands: `tail -5 /tmp/merge_lora.log`
- **Critical**: `terminal(background=true)` does NOT work over SSH — it backgrounds on the MacBook side, not the DGX

### Expected Warning: "Missing Adapter Keys"
During merge, peft warns about missing adapter keys. This is **EXPECTED and HARMLESS**:
- Config claims attention LoRA on all 64 layers
- Checkpoint only has attention LoRA on 16 layers (every 4th)
- Peft merges the keys that exist, uses base weights for missing ones
- Merge completes successfully

## Verification
```bash
# Check merged model exists and has weight files
ls -lh /data/SpecForge/custom_dflash/checkpoints/final_model_merged/
# Should show: model-00001-of-00002.safetensors (47GB), model-00002-of-00002.safetensors (3.7GB)

# Check total size
du -sh /data/SpecForge/custom_dflash/checkpoints/final_model_merged/
# Should be ~51GB
```

## Next Steps
1. **Evaluation**: Run MMLU, GSM8K benchmarks on merged model
2. **Deployment**: Serve with vLLM if metrics are acceptable
3. **Config cleanup**: Consider updating `adapter_config.json` target_modules to match actual trained layers (remove attention modules from layers without LoRA)

## Key Learnings
1. Always verify checkpoint has `adapter_config.json` before merge
2. Use `nohup` over SSH for long-running GPU tasks, not local backgrounding
3. "Missing adapter keys" warning during merge is usually benign — indicates selective layer training
4. Manual merge is reliable fallback when training script's merge fails silently

## Related Skills
- `dgx-spark-qwen3-deployment` — vLLM deployment
- `qwen27b-training-pipeline` — Training configuration
- `lora-merge-recovery` — This merge process (see skill)

