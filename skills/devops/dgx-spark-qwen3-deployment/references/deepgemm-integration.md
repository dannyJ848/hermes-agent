# DeepGEMM Integration Reference

## Overview

DeepSeek's DeepGEMM is integrated as a DEFAULT-ON optimization for Qwen3.6 MoE
inference on DGX Spark. It provides FP8 GEMM kernels with fine-grained scaling
and MoE-optimized grouped GEMMs — the same kernels DeepSeek uses in production
for V3/R1 inference.

## What DeepGEMM Does for MoE

Qwen3.6-35B-A3B has 256 experts (8 routed + 1 shared per token). Each token's
forward pass routes through expert-specific MLP layers, which are just batched
GEMM operations. DeepGEMM optimizes these grouped GEMMs with:

1. **Fine-grained FP8 scaling** — per-sub-group scale factors instead of per-tensor
2. **M-axis grouped GEMMs** — batches all expert matmuls into one kernel launch
3. **JIT compilation** — runtime kernel compile tailored to exact problem size
4. **Contiguous layout** — tokens concatenated, M-axis grouped (N/K fixed)

## vLLM Native Support

vLLM has native DeepGEMM support since ~v0.19. Module:
`vllm.model_executor.layers.fused_moe.experts.deep_gemm_moe`

Auto-detection via `has_deep_gemm()` and `is_deep_gemm_supported()`.
Enabled by default via `VLLM_USE_DEEP_GEMM=1` (this is the vLLM default).

vLLM's logic in `_valid_deep_gemm()`:
- Returns False if DeepGEMM not installed
- Returns False if N <= 512 (Triton faster for small N)
- Returns False if shapes unaligned to `get_mk_alignment_for_contiguous_layout()`
- Returns False if weight dtype != torch.float8_e4m3fn
- Returns False if tensors not contiguous

When _valid_deep_gemm returns False, vLLM falls back to Triton/CUTLASS kernels
SEAMLESSLY — no error, just different kernel path.

## Deployment Checklist

When adding DeepGEMM to a new vLLM serving script:

1. **Install:** `git clone --recursive deepseek-ai/DeepGEMM && ./develop.sh && pip install -e .`
2. **Docker env:** `-e VLLM_USE_DEEP_GEMM=1 -e DEEPGEMM_HOME=/data/repos/DeepGEMM`
3. **Docker mount:** `-v /data/repos/DeepGEMM:/opt/deepgemm:ro`
4. **Native env:** Export VLLM_USE_DEEP_GEMM=1 + PYTHONPATH with DeepGEMM dir
5. **Fallback:** Set VLLM_USE_DEEP_GEMM=0 if SM121 causes CUDA errors
6. **Verify:** `python3 -c "import deep_gemm; print(deep_gemm.__version__)"`

## Consistency Check

All serving scripts must have these 4 env vars in Docker containers:
- VLLM_MARLIN_USE_ATOMIC_ADD=1
- PYTORCH_TUNABLEOP_TUNING=1
- HF_ENABLE_PARALLEL_LOADING=1
- VLLM_USE_DEEP_GEMM=1

Run: `grep -c 'VLLM_USE_DEEP_GEMM\|MARLIN_USE_ATOMIC_ADD\|PYTORCH_TUNABLEOP\|HF_ENABLE_PARALLEL' <script>`

Expected: each env var >= 1 occurrence per Docker container.
