# Vision-Preserving LoRA Merge for Qwen3.5/3.6 (May 16, 2026)

## Problem

Standard `peft.merge_and_unload()` strips vision components from multimodal models like Qwen3.5/3.6 because:
- LoRA adapters only contain text-layer weights
- `merge_and_unload()` only fuses adapter weights into target modules
- Vision encoder weights may be lost in `save_pretrained()`

## Symptoms

- `config.json` lacks `vision_config` section after merge
- vLLM loads model as `Qwen3_5ForCausalLM` instead of `Qwen3_5ForConditionalGeneration`
- Vision requests fail with shape mismatch: `RuntimeError: shape '[131072, -1, 2, 16, 16]' is invalid`
- Garbled text output even on text-only prompts (weight corruption during merge)

## Solution

Use vision-preserving merge script that:
1. Loads base model with ALL components (vision, text, projector) using `AutoModelForCausalLM`
2. Loads LoRA adapter
3. Merges LoRA into text layers only
4. Explicitly preserves vision components from base to merged model
5. Saves complete multimodal model

**Script location:** `lora-merge-recovery:scripts/merge_vision_preserving.py`

## Usage

```bash
python3 merge_vision_preserving.py \
    --base-model /data/models/Qwen3.6-27B-Uncensored \
    --lora-adapter /data/SpecForge/custom_dflash/checkpoints/final_model \
    --output /data/SpecForge/custom_dflash/checkpoints/final_model_merged_vision
```

## Verification

```bash
# Check vision_config present
python3 -c "import json; d=json.load(open('final_model_merged_vision/config.json')); print('Has vision:', 'vision_config' in d)"

# Check preprocessor_config.json exists
ls final_model_merged_vision/preprocessor_config.json

# Check model type
python3 -c "import json; d=json.load(open('final_model_merged_vision/config.json')); print('Model type:', d.get('model_type'))"
# Should show: qwen3_5 (or similar multimodal type)
```

## Critical Post-Merge Steps

1. **Copy `preprocessor_config.json`** from base model — image processing config
2. **Verify tokenizer files** are present (tokenizer.json, tokenizer_config.json)
3. **Test text inference first** — if garbled, merge failed
4. **Test vision inference** — send image+text prompt

## Deployment with vLLM

```bash
docker run -d --name vllm-vision-merged \
  --runtime nvidia --gpus all -p 8000:8000 \
  -v /data:/data \
  vllm/vllm-openai:latest \
  --model /data/SpecForge/custom_dflash/checkpoints/final_model_merged_vision \
  --max-model-len 131072 \
  --gpu-memory-utilization 0.90 \
  --dtype bfloat16
```

## Key Insight

The `AutoModelForCausalLM` class in transformers handles Qwen3.5/3.6's multimodal architecture internally — it loads vision encoder, text decoder, and projector as a unified model. Using this class (rather than `AutoModelForVision2Seq` or manual component loading) ensures all weights are properly preserved during the merge process.

## Result

- Merged model: 53.8 GB (base 50.8 GB + LoRA ~3 GB)
- Vision capabilities preserved
- Speculative decoding with DFlash draft model
- ~16.2 tok/s with DFlash (May 16, 2026)
