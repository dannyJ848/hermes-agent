# vLLM LoRA Serving + Speed Benchmarks + Context Optimization

Date: May 14, 2026
Model: Qwen3.6-27B-Uncensored + FrankenV8 LoRA (rank 256)
GPU: NVIDIA GB10 (Blackwell) on DGX Spark
Container: ghcr.io/aeon-7/vllm-dflash:latest

## vLLM LoRA Serving Pattern

When a merged model (base + LoRA weights combined) fails in vLLM due to vision config issues (common with Qwen3.5-VL hybrid models), serve the base model with `--enable-lora` and load the adapter separately:

```bash
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
  --max-model-len 32768 \
  --gpu-memory-utilization 0.8 \
  --max-cudagraph-capture-size 256 \
  --enable-auto-tool-choice --tool-call-parser qwen3_coder \
  --kv-cache-dtype fp8_e5m2 \
  --load-format fastsafetensors \
  --attention-backend flashinfer \
  --enable-prefix-caching --enable-chunked-prefill \
  --dtype bfloat16 \
  --enable-lora --max-lora-rank 256 \
  --lora-modules merged-lora=/data/checkpoints/final_model
```

**Critical flags:**
- `--enable-lora` — Required for LoRA serving
- `--max-lora-rank 256` — Must match or exceed your LoRA rank (default 16 fails for r=256)
- `--lora-modules merged-lora=/path/to/adapter` — Names the LoRA module
- `--dtype bfloat16` — FP8 weight quantization fails with torch.compile pickling errors
- `--max-model-len 32768` — 32K is the sweet spot for agent workloads (see below)

**API usage:**
```bash
# Use the LoRA adapter
curl http://localhost:8000/v1/chat/completions \
  -d '{"model":"merged-lora","messages":[{"role":"user","content":"Hello"}]}'

# Use the base model (no LoRA)
curl http://localhost:8000/v1/chat/completions \
  -d '{"model":"/data/models/Qwen3.6-27B-Uncensored","messages":[{"role":"user","content":"Hello"}]}'
```

## FP8 Weight Quantization Failure

**Do NOT use `--quantization fp8`** with Qwen3.6 on this vLLM build:

1. With `--kv-cache-dtype fp8_e5m2`: `ValueError: fp8_e5m2 kv-cache is not supported with fp8 checkpoints`
2. Without FP8 KV: `PicklingError: Can't pickle <function launcher>` (torch.compile incompatibility)

**Workaround:** Use BF16 weights + FP8 KV cache:
```bash
--dtype bfloat16 --kv-cache-dtype fp8_e5m2
```

This gives 2x KV cache compression while keeping weights in BF16 for quality.

## Context Length Optimization

| Context | GPU Memory | Concurrency | Use Case |
|---------|-----------|-------------|----------|
| 262K | ~96GB | 4.3x | Theoretical max |
| 32K | ~59GB | 27.5x | **Recommended for agents** |
| 16K | ~55GB | 55x | Ultra-fast, most tasks |

**Why 32K is enough:**
- Training seq_len: 1024 tokens
- Typical agent turn: 512-2048 tokens
- Long code analysis: 4096-8192 tokens
- 32K handles 99% of agent use cases
- 64K handles 99.9%

**Command:** `--max-model-len 32768`

## Speed Benchmarks

| Mode | Speed | Notes |
|------|-------|-------|
| No thinking | ~20 tok/s | After CUDA graph warmup |
| With thinking | ~4-8 tok/s | Generates reasoning tokens first |
| Thinking overhead | ~5-10x slower | Model behavior, not hardware |

**Thinking mode control:**
```bash
# Enable thinking (default)
curl ... -d '{"chat_template_kwargs":{"enable_thinking":true}}'

# Disable thinking
curl ... -d '{"chat_template_kwargs":{"enable_thinking":false}}'
```

**Qwen3.6 thinking tokens:**
- `<think>` : ID 248068
- `</think>` : ID 248069

## Batch Inference Quality

**Batch inference is quality-neutral.** vLLM uses continuous batching — each request is processed independently. Zero quality loss, just better GPU utilization.

## Hermes Config for DGX

```yaml
model:
  provider: custom
  base_url: http://localhost:8000/v1
  api_key: not-needed
  default: merged-lora
  chat_template_kwargs:
    enable_thinking: true

providers:
  custom:
    api: http://localhost:8000/v1
    api_key: not-needed
    models:
      merged-lora:
        context_length: 32768
        supports_tools: true
        supports_reasoning: true
```

## Verification Commands

```bash
# Check vLLM running
curl -s http://localhost:8000/v1/models | grep '"id"'

# Check GPU memory
nvidia-smi | grep 'MiB' | tail -1

# Speed test (no thinking)
time curl -s http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"merged-lora","messages":[{"role":"user","content":"Hi"}],"max_tokens":50,"chat_template_kwargs":{"enable_thinking":false}}' > /dev/null

# Speed test (with thinking)
time curl -s http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"merged-lora","messages":[{"role":"user","content":"Hi"}],"max_tokens":50,"chat_template_kwargs":{"enable_thinking":true}}' > /dev/null
```
