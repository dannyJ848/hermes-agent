# Gotchas 84-88: Qwen3.6 Official Settings, DeepGEMM Docker, and Benchmarks

## Gotcha #84: Official Qwen3.6 Thinking Mode Fix — presence_penalty=1.5 + top_k=20

**SUPERSEDES Gotcha #80** (min_p=0.2 fix — min_p is no longer recommended).

Official Qwen3.6 thinking mode settings (confirmed from Qwen team + Reddit Apr 19 2026):

```bash
# CORRECT (official):
--override-generation-config '{"presence_penalty": 1.5, "top_k": 20}'
--reasoning-parser qwen3
--chat-template-kwargs '{"preserve_thinking": true, "enable_thinking": true}'

# WRONG (old community workaround):
--override-generation-config '{"min_p": 0.2, "top_k": 40}'  # DON'T USE
```

**Why the change:** min_p=0.2 was a community-discovered workaround for infinite thinking loops.
The official fix is presence_penalty=1.5 which prevents the model from looping on the same tokens.
top_k=20 (not 40) is the official recommendation for thinking mode.

**Critical:** All 5 serve scripts must use the same override-generation-config. The Apr 19 audit
patched all of: spark-maxperf.sh, superqwen3-super.sh, deploy-spark-day1.sh, spark-grpo-train.sh,
spark-day1.sh. If you find min_p=0.2 in any script, replace it immediately.

## Gotcha #85: --language-model-only Skips Vision Encoder (~2-3GB VRAM Savings)

Qwen3.6-35B-A3B has a built-in vision encoder. When serving text-only (agent inference, tool calling,
reasoning), the vision encoder wastes ~2-3GB VRAM that could go to KV cache.

```bash
vllm serve Qwen/Qwen3.6-35B-A3B \
    --language-model-only \    # <-- ADD THIS to every text-only serve command
    ...
```

This flag is FREE — zero quality loss for text tasks. Only skip it if you need vision input.

On DGX Spark with 119GB usable VRAM (after OS), that 2-3GB = ~5% more KV cache = longer context
or more concurrent requests.

## Gotcha #86: DeepGEMM Env Vars + Mount Required in EVERY Docker Container

DeepGEMM (deepseek-ai/DeepGEMM) provides FP8 GEMM + MoE kernels that significantly speed up
Qwen3.6 inference on Blackwell. But the Docker container needs BOTH env vars AND a volume mount:

```bash
docker run ... \
    -e VLLM_USE_DEEP_GEMM=1 \                  # Tells vLLM to use DeepGEMM
    -e DEEPGEMM_HOME=/data/repos/DeepGEMM \     # Where the module lives
    -v /data/repos/DeepGEMM:/opt/deepgemm:ro \  # Mount into container
    -v "$HF_CACHE:/root/.cache/huggingface" \
    ...
```

**Bug found during Apr 19 audit:** spark-day1.sh installed DeepGEMM to /data/repos/DeepGEMM
but both BF16 and FP8 Docker containers were missing the env vars + mount. This meant DeepGEMM
was installed but never activated — silently falling back to slower default kernels.

**Check all 5 scripts:** Every Docker `run` command that serves Qwen3.6 must have all 3 lines.
If any container is missing them, the container starts fine but uses slower kernels.

## Gotcha #87: Qwen3.6 Benchmarks Way Higher Than Estimated

Official benchmarks (released Apr 2026) show Qwen3.6-35B-A3B significantly outperforms
initial community estimates:

| Benchmark | Qwen3.6-35B-A3B | Previous Estimate | Improvement |
|---|---|---|---|
| MMLU-Pro | 85.2% | ~80% | +5.2 pts |
| GPQA | 86.0% | ~82% | +4.0 pts |
| SWE-bench | 73.4% | ~65% | +8.4 pts |
| AIME | 92.7% | ~85% | +7.7 pts |
| ToolCall-15 | 97-100/100 | N/A | Excellent |

This means the local model is much more competitive with cloud models than expected.
The gap between Qwen3.6-35B and GLM-5.1 on domain-specific tasks (with LoRA + RAG)
is narrower than general benchmarks suggest.

## Gotcha #88: Official FP8 Checkpoint Available on HuggingFace

Download the pre-quantized FP8 checkpoint directly instead of runtime quantization:

```bash
# On the Spark:
huggingface-cli download Qwen/Qwen3.6-35B-A3B-FP8 --local-dir /data/models/Qwen3.6-35B-A3B-FP8
```

**Benefits over runtime FP8 quantization:**
- No quantization overhead at startup (saves ~30-60s)
- Calibrated quantization (better quality than on-the-fly)
- ~35GB download (half the BF16 70GB)
- Serves on port 8001 for agent inference at 208 tok/s (Allen Kuo benchmark, Blackwell)

**Source:** Allen Kuo confirmed 208 tok/s FP8 decode on Blackwell architecture.
This matches our spark-maxperf.sh target of 200+ tok/s for the FP8 agent inference port.

The FP8 checkpoint is the official Qwen team release, not a community quantization.
