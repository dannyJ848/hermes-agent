---
name: lora-merge-recovery
description: Recover from silent LoRA merge failures on DGX — manual merge script, missing config handling, expected warnings
version: 1.0.0
category: mlops
tags: [lora, merge, peft, qwen, dgx, troubleshooting]
---

# LoRA Merge Recovery

## When to Use

When a training script's `merge_and_unload()` fails silently (creates config files but no weight files), or when checkpoint directory lacks required metadata.

## Prerequisites

- DGX Spark access: `djg6228@spark-85e8.local`
- Base model downloaded: `/data/models/Qwen3.6-27B-Uncensored/`
- LoRA checkpoint with `adapter_model.bin`

## Symptoms

- `final_model_merged/` directory exists but only contains `.json` files
- No `.safetensors` or `.bin` weight files
- `ls -lh` shows directory size < 1MB

## Recovery Steps

### 1. Verify Checkpoint Has Config

```bash
ssh djg6228@spark-85e8.local "ls /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_10000/"
```

**Must contain**: `adapter_model.bin` + `adapter_config.json`

**If missing config**:
```bash
cp /data/SpecForge/custom_dflash/checkpoints/final_model/adapter_config.json \
   /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_10000/
```

### 2. Write Merge Script

```bash
ssh djg6228@spark-85e8.local "cat > /tmp/merge_lora.py << 'PYEOF'
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
PYEOF"
```

### 3. Run in Background (CRITICAL: Use nohup on DGX)

```bash
# CORRECT: nohup on DGX
ssh djg6228@spark-85e8.local "nohup python3 /tmp/merge_lora.py > /tmp/merge_lora.log 2>&1 & echo \$!"

# INCORRECT: This backgrounds on MacBook, not DGX
# terminal(background=true) with SSH command
```

### 4. Monitor Progress

```bash
ssh djg6228@spark-85e8.local "ps aux | grep merge_lora | grep -v grep"
ssh djg6228@spark-85e8.local "tail -10 /tmp/merge_lora.log"
```

### 5. Verify Completion

```bash
ssh djg6228@spark-85e8.local "ls -lh /data/SpecForge/custom_dflash/checkpoints/final_model_merged/"
```

Should show `model-00001-of-00002.safetensors` (~47GB) and `model-00002-of-00002.safetensors` (~3.7GB).

### 6. Copy Tokenizer Files (REQUIRED)

The merged model directory does NOT inherit tokenizer files from the base model. You MUST copy them manually:

```bash
ssh djg6228@spark-85e8.local "cp /data/models/Qwen3.6-27B-Uncensored/tokenizer* /data/SpecForge/custom_dflash/checkpoints/final_model_merged/"
ssh djg6228@spark-85e8.local "cp /data/models/Qwen3.6-27B-Uncensored/vocab* /data/SpecForge/custom_dflash/checkpoints/final_model_merged/"
```

Without this step, `AutoTokenizer.from_pretrained()` and `lm_eval` will fail with `ValueError: Couldn't instantiate the backend tokenizer`.

### 7. Vision-Preserving Merge (for Multimodal Models)

**CRITICAL**: Standard `peft.merge_and_unload()` strips vision components from multimodal models like Qwen3.5/3.6. The vision encoder and projector weights are lost, resulting in a text-only model.

**Symptoms of vision loss**:
- `config.json` lacks `vision_config` section
- vLLM loads model as `Qwen3_5ForCausalLM` instead of `Qwen3_5ForConditionalGeneration`
- Vision requests fail with shape mismatch errors: `RuntimeError: shape '[131072, -1, 2, 16, 16]' is invalid`

**Fix**: Use vision-preserving merge script:

```bash
# The script loads with AutoModelForCausalLM (which handles vision internally),
# merges LoRA into text layers only, and explicitly preserves vision weights
python3 merge_vision_preserving.py \
    --base-model /data/models/Qwen3.6-27B-Uncensored \
    --lora-adapter /data/SpecForge/custom_dflash/checkpoints/final_model \
    --output /data/SpecForge/custom_dflash/checkpoints/final_model_merged_vision
```

**After merge, verify vision is preserved**:
```bash
python3 -c "import json; d=json.load(open('final_model_merged_vision/config.json')); print('Has vision:', 'vision_config' in d)"
```

**Also copy preprocessor_config.json** for image processing:
```bash
cp /data/models/Qwen3.6-27B-Uncensored/preprocessor_config.json final_model_merged_vision/
```

## Expected Warnings

### "Missing adapter keys" — EXPECTED and HARMLESS
Config claims LoRA on more layers than actually trained. Peft merges available weights, uses base weights for missing ones. Verify by inspecting `adapter_model.bin` keys.

**Actual behavior observed (May 10, 2026)**:
- Config claims all 64 layers have attention LoRA
- Checkpoint only has it on every 4th layer (3, 7, 11, ..., 63)
- Peft warns about "missing adapter keys" but merges successfully with available weights
- This is NORMAL for sparse LoRA training — do not attempt to "fix" it

### "torch_dtype is deprecated" — Cosmetic
Doesn't affect merge.

### "Fast path not available" — Optional libs missing
Merge works but slower.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `Can't find 'adapter_config.json'` | Config missing | Copy from `final_model/` |
| No weight files in merged dir | Silent failure | Use manual script |
| Process dies immediately | OOM/import error | Check log |
| Merge hangs at 0% | GPU memory | Check `nvidia-smi` |

## Related

- `qwen27b-training-pipeline` — Training setup
- `dgx-spark-qwen3-deployment` — vLLM deployment
- `qwen27b-dgx-deployment` — Full deployment including evaluation

## References

- `references/merge-session-may2026.md` — Actual merge session from May 10, 2026 with missing config recovery and "missing adapter keys" warning details
- `scripts/merge_vision_preserving.py` — Vision-preserving LoRA merge script for Qwen3.5/3.6 multimodal models. Standard peft.merge_and_unload() strips vision; this script preserves vision encoder + projector weights
- `references/dflash-optimization-may2026.md` — DFlash speculative decoding optimization findings: num_speculative_tokens=8 gives 25-30% acceptance vs 12% at 15
- `references/dflash-lora-optimization-deep-dive-may16-2026.md` — Complete research on base + dynamic LoRA + speculative decoding alternatives. vLLM issue #6912 (closed as not planned), SGLang S-LoRA as best alternative, hybrid deployment pattern
