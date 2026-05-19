# DGX Qwen3.6-27B-Uncensored vLLM Optimization Reference
# Generated: 2026-05-18
# Branch: qwen27b-training-artifacts-may3-2026 (local, not pushed due to remote divergence)

## Optimized Launch Command

```bash
export PATH=/data/SpecForge/venv/bin:$PATH
export CUDA_VISIBLE_DEVICES=0

vllm serve /data/models/Qwen3.6-27B-Uncensored \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype bfloat16 \
  --max-model-len 262144 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --chat-template /data/models/Qwen3.6-27B-Uncensored/chat_template.jinja \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.95 \
  --trust-remote-code \
  --no-enable-prefix-caching \
  --kv-cache-dtype fp8_e5m2 \
  --max-num-seqs 1
```

## Key Optimizations Applied

1. **BF16 weights (native)** — no model quantization, preserves training quality
2. **FP8 KV cache** (`--kv-cache-dtype fp8_e5m2`) — 2x KV cache compression, safe with BF16 weights
3. **0.95 GPU memory utilization** — maximizes available KV cache memory
4. **Single sequence mode** (`--max-num-seqs 1`) — dedicates all memory to one long-context request
5. **262K max model len** — Qwen3.6's native context window

## Tested Context Lengths

| Characters | ~Tokens | Latency | Status |
|-----------|---------|---------|--------|
| 16K | ~4K | 43s | ✅ Responsive |
| 32K | ~8K | 22s | ✅ Responsive |
| 64K | ~16K | 118s | ✅ Works |
| 128K | ~32K | 237s | ✅ Works |
| 200K | ~50K | ~300s | ✅ Works (slow) |
| 256K | ~64K | ~600s | ✅ Works (very slow) |

## GPU Memory Breakdown (GB10, 130GB VRAM)

- Model weights: 51.1 GiB
- Available KV cache: ~59 GiB (with FP8 + 0.95 utilization)
- Total GPU usage during inference: ~114GB

## Hermes Config Update

In `profiles/dgx-qwen-lora/config.yaml`:
```yaml
spark-bf16:
  models:
    merged-lora:
      context_length: 262144  # Updated from 32768
    qwen3.6-27b-uncensored:
      context_length: 262144  # Updated from 32768
```

## Iteration Budget

Updated in `gateway/run.py`:
```python
max_iterations = int(os.getenv("HERMES_MAX_ITERATIONS", "180"))  # Was 90
```

## Files Changed

- `gateway/run.py` — iteration budget 90→180
- `profiles/dgx-qwen-lora/config.yaml` — context_length 32768→262144
- `profiles/dgx-qwen-lora/scripts/start_vllm_optimized.sh` — new launch script

## Notes

- 262K is the *configured maximum*. Practical responsive limit for agent use: 32K-64K tokens.
- 128K+ works for batch processing or document ingestion (2-10 min latency).
- Chunked prefill enabled by default in vLLM 0.21+.
- N-gram speculative decoding flags (`--speculative-model [ngram]`) are NOT valid in vLLM 0.21.0.
