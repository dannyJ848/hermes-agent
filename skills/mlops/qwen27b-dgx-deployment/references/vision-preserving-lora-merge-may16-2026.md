# Vision-Preserving LoRA Merge for Qwen3.5/3.6 — May 16, 2026

## Problem

Standard `peft.merge_and_unload()` strips vision components from multimodal Qwen3.5/3.6 models because:
- LoRA adapters only contain text-layer weights (q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj)
- `merge_and_unload()` only fuses adapter weights into modules that have LoRA adapters
- Vision encoder weights are untouched but may be lost when `save_pretrained()` saves only the text model config
- vLLM 0.20.2 then fails to load the merged model with `RuntimeError: shape '[131072, -1, 2, 16, 16]' is invalid for input of size 154140672` because it tries to initialize the vision patch embedder with text-only shapes

## Root Cause

The Qwen3.5/3.6 architecture uses `Qwen3_5ForConditionalGeneration` which includes:
- Vision encoder (ViT-style patch embedder + transformer)
- Vision-language projector (MLP that maps vision features to text space)
- Text decoder (the actual causal LM)

When LoRA is applied, only the text decoder layers get adapter weights. The vision encoder and projector are untouched. However, `save_pretrained()` on the merged model may not preserve the `vision_config` in the saved `config.json`, causing vLLM to fail initialization.

## Solution

Use a custom merge script that:
1. Loads the base model with `AutoModelForCausalLM.from_pretrained()` (handles both text and vision internally for Qwen3.5)
2. Loads the LoRA adapter with `PeftModel.from_pretrained()`
3. Calls `merge_and_unload()` — this only affects text layers with LoRA weights, vision components remain intact
4. Saves the merged model with `save_pretrained()`
5. Explicitly copies `preprocessor_config.json` from base model to merged directory (vLLM needs this for image processor initialization)
6. Verifies `vision_config` exists in saved `config.json`

## Usage

```bash
python3 merge_vision_preserving.py \
    --base-model /data/models/Qwen3.6-27B-Uncensored \
    --lora-adapter /data/SpecForge/custom_dflash/checkpoints/final_model \
    --output /data/SpecForge/custom_dflash/checkpoints/final_model_merged_vision \
    --skip-if-exists
```

## Key Details

### Why AutoModelForCausalLM, not AutoModelForVision2Seq?

`AutoModelForVision2Seq` is not available in all transformers versions. For Qwen3.5/3.6, `AutoModelForCausalLM.from_pretrained()` with `trust_remote_code=True` correctly loads the multimodal model class which handles both text and vision internally.

### Why copy preprocessor_config.json?

vLLM's image processor initialization looks for `preprocessor_config.json` in the model directory. The LoRA merge does not copy this file from the base model. Without it, vLLM fails with:
```
OSError: Can't load image processor for '/path/to/merged/model'. 
If you were trying to load it from 'https://huggingface.co/models', 
make sure you don't have a local directory with the same name. 
Otherwise, make sure '/path/to/merged/model' is the correct path 
to a directory containing a preprocessor_config.json file
```

### Model Size

The merged model with vision preserved is ~53.8 GB (12 safetensors shards at ~5GB each). This is larger than a text-only merge because it includes:
- Text decoder weights (merged with LoRA): ~48 GB
- Vision encoder weights: ~3 GB
- Projector weights: ~2 GB

### vLLM Deployment

Deploy with standard vLLM serve command — no `--language-model-only` flag needed since vision is preserved:

```bash
docker run -d --name vllm-vision-merged \
    --runtime nvidia --gpus all -p 8000:8000 \
    -v /data/models:/data/models \
    -v /data/SpecForge/custom_dflash/checkpoints:/data/SpecForge/custom_dflash/checkpoints \
    -e CUDA_VISIBLE_DEVICES=0 \
    vllm/vllm-openai:latest \
    --model /data/SpecForge/custom_dflash/checkpoints/final_model_merged_vision \
    --max-model-len 131072 \
    --dtype bfloat16 \
    --quantization fp8 \
    --gpu-memory-utilization 0.9 \
    --enable-chunked-prefill \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_xml \
    --speculative-config '{"method": "dflash", "model": "/data/models/Qwen3.5-27B-DFlash", "num_speculative_tokens": 5}'
```

### Verification

Check that the model has vision:
```bash
python3 -c "import json; d=json.load(open('/data/SpecForge/custom_dflash/checkpoints/final_model_merged_vision/config.json')); print('vision_config:', 'vision_config' in d)"
# Expected: vision_config: True

# Test with curl
curl -s http://localhost:8000/v1/models | grep -o '"id":"[^"]*"'
# Expected: "id":"/data/SpecForge/custom_dflash/checkpoints/final_model_merged_vision"
```

## Alternative: Text-Only Merge

If vision is NOT needed, use `--language-model-only` flag with vLLM:

```bash
vllm serve /path/to/merged/model --language-model-only
```

This disables vision encoder loading and prevents the shape mismatch. The model will be text-only but loads faster and uses less memory.

## Related Pitfalls

- **Pitfall #35**: LoRA + DFlash speculative decoding = catastrophic slowdown. The vision-preserving merge fixes this by eliminating dynamic LoRA loading.
- **Pitfall #36**: vLLM 0.20.2 loads Qwen3_5ForCausalLM as vision model causing shape mismatch. The `--language-model-only` flag is the quick fix, but this merge script is the proper fix for preserving vision.

## Files

- Merge script: `scripts/merge_vision_preserving.py` (in this skill directory)
- Deploy script: `/tmp/deploy_vllm_vision_merged.sh` (generated during session)
- Model path: `/data/SpecForge/custom_dflash/checkpoints/final_model_merged_vision`
