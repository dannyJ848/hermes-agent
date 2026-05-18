# LoRA Merge Session Details — May 10, 2026

## Context
- Training completed: 10,000 steps, LoRA r=256, alpha=512
- Checkpoint: `checkpoint_step_10000` (missing `adapter_config.json`)
- Base model: `/data/models/Qwen3.6-27B-Uncensored/`
- Host: DGX Spark (spark-85e8.local, 10.0.0.171)

## Problem: Missing adapter_config.json

The `checkpoint_step_10000` directory contained `adapter_model.safetensors` but NOT `adapter_config.json`. This prevented `PeftModel.from_pretrained()` from loading.

**Root cause**: The training script saves adapter weights but the config was only in `final_model/` directory.

**Fix**:
```bash
cp /data/SpecForge/custom_dflash/checkpoints/final_model/adapter_config.json \
   /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_10000/
```

## Problem: "Missing adapter keys" Warning

During merge, peft emitted warnings about missing adapter keys for many layers.

**Investigation**:
- `adapter_config.json` claims `target_modules` includes attention layers on all 64 layers
- Actual checkpoint only has LoRA weights on every 4th layer (layers 3, 7, 11, ..., 63)
- This is because the training script applied LoRA sparsely

**Resolution**: This is EXPECTED and HARMLESS. Peft merges the available weights and uses base model weights for layers without LoRA. The merge completed successfully.

## Merge Results

- Output: `/data/SpecForge/custom_dflash/checkpoints/final_model_merged/`
- Size: 51GB total
  - `model-00001-of-00002.safetensors`: ~47GB
  - `model-00002-of-00002.safetensors`: ~3.7GB
- Format: BF16
- Parameters: 26.9B

## Post-Merge Steps Required

1. Copy tokenizer files from base model:
```bash
cp /data/models/Qwen3.6-27B-Uncensored/tokenizer* /data/SpecForge/custom_dflash/checkpoints/final_model_merged/
cp /data/models/Qwen3.6-27B-Uncensored/vocab* /data/SpecForge/custom_dflash/checkpoints/final_model_merged/
```

2. Verify model loads:
```bash
python3 -c "from transformers import AutoModelForCausalLM; m = AutoModelForCausalLM.from_pretrained('/data/SpecForge/custom_dflash/checkpoints/final_model_merged', torch_dtype='bfloat16', device_map='auto'); print('OK')"
```

## Key Lessons

1. Always check for `adapter_config.json` before attempting merge
2. "Missing adapter keys" warning is normal for sparse LoRA
3. Tokenizer files must be copied manually after merge
4. Use `nohup` for merge operations — they take 10-15 minutes
5. Verify with `nvidia-smi` that GPU memory is allocated during merge
