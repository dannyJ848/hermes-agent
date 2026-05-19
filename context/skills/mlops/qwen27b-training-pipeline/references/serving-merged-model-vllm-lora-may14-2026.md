# Serving Merged Qwen Models via vLLM with LoRA Adapter

**Date:** May 14, 2026
**Context:** Merged model (base + LoRA weights combined) fails in vLLM due to vision config mismatches. Workaround: serve base model + LoRA adapter separately.

## Problem

The merged model at `/data/SpecForge/custom_dflash/checkpoints/final_model_merged/` loads fine in transformers but fails in vLLM with:

```
TypeError: Qwen3_5Config.__init__() got an unexpected keyword argument 'vision_config'
```

This happens because:
1. The base model is `Qwen3.5-VL` (vision-language variant)
2. vLLM's Qwen3.5 loader expects either pure text config or VL config, not a hybrid
3. Merging LoRA weights into the base model preserves the vision config structure
4. Flattening `text_config` into root config doesn't help — vLLM still sees `Qwen3_5ForCausalLM` as VL

## Solution: Serve Base + LoRA Separately

Instead of merging weights, keep the base model and LoRA adapter separate, and let vLLM load both:

```bash
# 1. Ensure base model is at expected path
ls /data/models/Qwen3.6-27B-Uncensored/*.safetensors

# 2. Ensure LoRA adapter is at expected path
ls /data/SpecForge/custom_dflash/checkpoints/final_model/adapter_*.safetensors
ls /data/SpecForge/custom_dflash/checkpoints/final_model/adapter_config.json

# 3. Launch vLLM with LoRA support
docker run -d --name vllm-merged \
  --gpus all --privileged --ipc host --network host \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints:/data/checkpoints \
  -e VLLM_MARLIN_USE_ATOMIC_ADD=1 \
  --entrypoint python3 \
  ghcr.io/aeon-7/vllm-dflash:latest \
  -m vllm.entrypoints.openai.api_server \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --port 8000 --host 0.0.0.0 \
  --max-model-len 262144 --gpu-memory-utilization 0.8 \
  --max-cudagraph-capture-size 256 \
  --enable-auto-tool-choice --tool-call-parser qwen3_coder \
  --kv-cache-dtype fp8_e5m2 --load-format fastsafetensors \
  --attention-backend flashinfer --enable-prefix-caching \
  --enable-chunked-prefill --dtype bfloat16 \
  --enable-lora --max-lora-rank 256 \
  --lora-modules merged-lora=/data/checkpoints/final_model
```

## Critical Flags

| Flag | Value | Why |
|------|-------|-----|
| `--enable-lora` | (no value) | Required for LoRA serving |
| `--max-lora-rank` | 256 | Must match or exceed LoRA rank. Default 16 fails for r=256 with: `LoRA rank 256 is greater than max_lora_rank 16` |
| `--lora-modules` | `merged-lora=/path` | Names the LoRA module. Use this name as `model` in API calls |

## API Usage

```bash
# Using the LoRA adapter (post-trained model)
curl http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"merged-lora","messages":[{"role":"user","content":"Hello"}],"max_tokens":50}'

# Using base model (no LoRA)
curl http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"/data/models/Qwen3.6-27B-Uncensored","messages":[{"role":"user","content":"Hello"}],"max_tokens":50}'

# List available models
curl http://localhost:8000/v1/models
```

## Qwen3.5 Thinking Tokens

Qwen3.5 has built-in thinking tokens:
- `<think>`: token ID 248068
- `</think>`: token ID 248069

**Without `--reasoning-parser qwen3`:**
- Thinking content appears in `content` field
- Response includes "Here's a thinking process:..." before the actual answer

**With `--reasoning-parser qwen3`:**
- Thinking content moves to `reasoning` field
- `content` field may be null if model only outputs thinking

**Recommendation:** For most clients, omit `--reasoning-parser` and let thinking appear in `content`. The client can strip `<think>...</think>` blocks if needed. For structured clients that need separation, use the parser.

## Verification Steps

```bash
# 1. Check container is running
sudo docker ps | grep vllm-merged

# 2. Check logs for successful LoRA load
sudo docker logs vllm-merged --tail 20 | grep -i lora

# 3. Test API
curl -s http://localhost:8000/v1/models | python3 -m json.tool

# 4. Test chat with LoRA
curl -s http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"merged-lora","messages":[{"role":"user","content":"What is 2+2?"}],"max_tokens":20}'

# 5. Check GPU
nvidia-smi | grep VLLM
```

## Hermes Config

```yaml
model:
  default: merged-lora
  provider: local-dgx

providers:
  local-dgx:
    api: http://localhost:8000/v1
    api_key: not-needed
    models:
      merged-lora:
        context_length: 262144
        supports_tools: true
        supports_reasoning: true
```

## Common Errors

**`LoRA rank 256 is greater than max_lora_rank 16`**
→ Add `--max-lora-rank 256`

**`Call to add_lora method failed`**
→ Check that adapter_config.json exists and has correct `base_model_name_or_path`

**Model loads but API returns empty content**
→ This is normal with `--reasoning-parser qwen3` — check `reasoning` field instead

**vLLM takes 3-4 minutes to start**
→ Normal. Includes model loading (~40s), torch.compile (~75s), CUDA graph capture (~50s)
