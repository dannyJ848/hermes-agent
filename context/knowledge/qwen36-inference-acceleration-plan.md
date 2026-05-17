# qwen36-inference-acceleration-plan

*Researched: 2026-05-14 22:25 CDT*

# Qwen3.6-27B Inference Acceleration Plan

## Key Findings

### 1. DFlash Speculative Decoding (Highest Impact)
- z-lab provides purpose-built DFlash drafter for Qwen3.6-27B: `z-lab/Qwen3.6-27B-DFlash`
- Up to 6x lossless speedup via block diffusion drafting
- ~300MB drafter model, works with LoRA adapters
- Requires vLLM 0.20.1+
- Flag: `--speculative-config '{"method": "dflash", "model": "z-lab/Qwen3.6-27B-DFlash"}'`

### 2. KV Cache Optimization
- **Prefix caching**: `--enable-prefix-caching` — 30-50% faster for repeated tool call patterns
- **KV cache FP8 quantization**: `--kv-cache-dtype fp8` — 50% memory reduction, +20-40% throughput
- **Chunked prefill**: `--enable-chunked-prefill` — critical for 131K context, reduces TTFT 40-60%

### 3. Quantization
- Qwen3.6-27B-FP8 official weights available (Qwen/Qwen3.6-27B-FP8)
- FP8 preferred over GPTQ/AWQ for tool calling accuracy
- 27GB → ~14GB weights, +50-80% throughput from reduced memory bandwidth
- Need to merge LoRA into FP8 base or re-train

### 4. Continuous Batching Tuning
- For latency (tool calling): `--max-num-batched-tokens 4096 --max-num-seqs 64`
- For throughput: `--max-num-batched-tokens 32768 --max-num-seqs 256`

## Expected Combined Speedup
Realistic target: 4-5x end-to-end with DFlash + prefix caching + chunked prefill.

## Sources
- z-lab/dflash GitHub: https://github.com/z-lab/dflash
- Qwen speed benchmarks: https://qwen.readthedocs.io/en/latest/getting_started/speed_benchmark.html
- vLLM speculative decoding docs: https://docs.vllm.ai/en/stable/features/speculative_decoding/
- vLLM optimization guide: https://docs.vllm.ai/en/stable/configuration/optimization/
- LLMKube Qwen3.6-27B bakeoff: https://llmkube.com/blog/qwen3-6-27b-bakeoff


## Sources

- https://github.com/z-lab/dflash
- https://qwen.readthedocs.io/en/latest/getting_started/speed_benchmark.html
- https://docs.vllm.ai/en/stable/features/speculative_decoding/
- https://docs.vllm.ai/en/stable/configuration/optimization/
- https://llmkube.com/blog/qwen3-6-27b-bakeoff
