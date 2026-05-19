# vLLM LoRA Serving + Tool Calling Configuration — May 14, 2026

## Problem

Serving Qwen3.5/3.6 with LoRA adapter AND tool calling requires specific vLLM flags. Multiple failure modes:

1. **Merged model fails** — `Qwen3_5Config` triggers vision-language loading, vLLM expects text-only
2. **Wrong parser name** — `qwen25` doesn't exist; correct name is `qwen3_xml`
3. **Context mismatch** — vLLM `max_model_len` and Hermes `context_length` must match
4. **Tool choice rejected** — Without `--enable-auto-tool-choice`, Hermes "auto" tool_choice returns HTTP 400

## Working Docker Launch

```bash
docker run -d --name vllm-merged \
  --runtime nvidia --gpus all \
  -p 8000:8000 \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints/final_model:/data/checkpoints/final_model \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --enable-lora \
  --lora-modules merged-lora=/data/checkpoints/final_model \
  --max-lora-rank 256 \
  --max-model-len 131072 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.95 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml
```

## Flag Reference

| Flag | Value | Purpose |
|------|-------|---------|
| `--model` | `/data/models/Qwen3.6-27B-Uncensored` | Base model (NOT merged) |
| `--enable-lora` | — | Enable LoRA serving |
| `--lora-modules` | `merged-lora=/data/checkpoints/final_model` | Named LoRA adapter |
| `--max-lora-rank` | `256` | Must match adapter config |
| `--max-model-len` | `131072` | 128K context window |
| `--gpu-memory-utilization` | `0.95` | 95% GPU memory for KV cache |
| `--enable-auto-tool-choice` | — | Required for "auto" tool_choice |
| `--tool-call-parser` | `qwen3_xml` | Qwen3.5/3.6 XML parser |

## Hermes Config (config.yaml)

```yaml
model:
  context_length: 131072  # MUST match vLLM max_model_len
  provider: custom

providers:
  custom:
    base_url: http://localhost:8000/v1
    models:
      merged-lora:
        context_length: 131072
```

## Verification Commands

```bash
# Check server is up
curl -s http://localhost:8000/v1/models | python3 -m json.tool

# Test basic inference
curl -s http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "merged-lora",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'

# Test tool calling
curl -s http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "merged-lora",
    "messages": [{"role": "user", "content": "test"}],
    "tools": [{"type": "function", "function": {"name": "test", "description": "test", "parameters": {"type": "object", "properties": {}}}}],
    "tool_choice": "auto"
  }'
```

## Error Signatures and Fixes

### Error: "auto tool choice requires --enable-auto-tool-choice"
**Fix:** Add `--enable-auto-tool-choice` to docker run command.

### Error: "invalid tool call parser: qwen25"
**Fix:** Use `--tool-call-parser qwen3_xml` (not `qwen25`).

### Error: "Qwen3_5Config has no num_attention_heads"
**Fix:** Serve base model + LoRA adapter, NOT merged weights.

### Error: Context window still 65K in Hermes
**Fix:** Update BOTH vLLM `--max-model-len` AND Hermes `context_length` to 131072.

## Startup Timeline

| Phase | Duration | Memory |
|-------|----------|--------|
| Model load | ~4 min | 55GB |
| torch.compile | ~46s | +2GB |
| Warmup | ~40s | stable |
| CUDA graphs (PIECEWISE) | ~39s | +2GB |
| CUDA graphs (FULL) | ~26s | stable |
| **Total** | **~8 min** | **~59GB** |

## Resource Usage

- **GPU memory:** ~55GB model + ~5GB LoRA + KV cache
- **KV cache size:** 833,955 tokens (at 131K context)
- **Max concurrency:** 6.36x at 131K tokens/request
- **Speed:** ~20 tok/s (no thinking), ~4-8 tok/s (with thinking)
