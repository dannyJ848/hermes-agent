# Gotchas 77-78: DeepGEMM Integration

## #77: DeepGEMM — vLLM Has NATIVE Support (No Monkey-Patch Needed)

DeepSeek open-sourced DeepGEMM (deepseek-ai/DeepGEMM) — FP8 GEMM kernel library
with fine-grained scaling, MoE-optimized grouped GEMMs, 1550 TFLOPS on H800.

**CRITICAL DISCOVERY:** vLLM already has native DeepGEMM support. No monkey-patching
or custom integration code needed. The integration already exists in:
`vllm.model_executor.layers.fused_moe.experts.deep_gemm_moe`

Just set `VLLM_USE_DEEP_GEMM=1` (this is DEFAULT=1 in vLLM — it auto-enables).

**Wiring pattern for Docker containers:**
```
-e VLLM_USE_DEEP_GEMM=1
-e DEEPGEMM_HOME=/data/repos/DeepGEMM
-v /data/repos/DeepGEMM:/opt/deepgemm:ro
```

**Wiring pattern for native vLLM (no Docker):**
```
export VLLM_USE_DEEP_GEMM=1
export DEEPGEMM_HOME=/data/repos/DeepGEMM
if [[ -d "$DEEPGEMM_HOME" ]]; then
    export PYTHONPATH="${DEEPGEMM_HOME}:${PYTHONPATH:-}"
fi
```

**Day-1 install (spark-day1.sh step 2G):**
```bash
git clone --recursive https://github.com/deepseek-ai/DeepGEMM.git /data/repos/DeepGEMM
cd /data/repos/DeepGEMM
./develop.sh   # Build CPP JIT module
pip install -e .
```

**Dual-path safety:** kernels-community/deep-gemm (HF Kernel Hub) is installed
in step 2E as a fallback. The standalone DeepGEMM repo (step 2G) is the primary.
If standalone import fails, vLLM falls back to kernels-community version.

**DeepGEMM quantization requirements:**
- FP8 weights (torch.float8_e4m3fn) with static 128-block symmetric quant
- Our fp8_e5m2 KV cache + FP8 model weights match these requirements
- Block shape: `get_mk_alignment_for_contiguous_layout()` alignment required
- N must be > 512 (small N falls back to Triton, which is faster for small ops)

**Scripts wired (as of Apr 19):**
1. spark-day1.sh — step 2G clone+install + parallel marker "deepgemm"
2. spark-maxperf.sh — VLLM_USE_DEEP_GEMM=1 + DEEPGEMM_HOME + PYTHONPATH
3. superqwen3-super.sh — env + mount in both BF16+FP8 Docker containers
4. deploy-spark-day1.sh — env + mount in both containers
5. spark-grpo-train.sh — env + mount in GRPO container

## #78: DeepGEMM SM121 Fallback Path

DeepGEMM officially supports SM90 (Hopper) and SM100 (Blackwell).
DGX Spark uses SM121 (GB10, Blackwell variant).

**Risk:** SM121 is Blackwell-based but not explicitly listed. DeepGEMM's SM100
JIT kernels *should* work on SM121 since they share the same Blackwell tensor
core ISA (mma.sync SM80-compatible). But this is UNTESTED at time of writing.

**Fallback if DeepGEMM breaks on SM121:**
```bash
export VLLM_USE_DEEP_GEMM=0  # Disables DeepGEMM, uses vLLM default GEMM
```

This is a ZERO-RISK fallback — just set the env var and restart vLLM.
vLLM will use its built-in CUTLASS/Triton GEMM kernels instead.

**Symptoms of DeepGEMM+SM121 failure:**
- CUDA illegal memory access in grouped GEMM
- NaN outputs after first inference
- vLLM crash at model loading with DeepGEMM import errors

**Diagnosis:**
```python
import deep_gemm
print(deep_gemm.__version__)
# Test basic GEMM on SM121:
import torch
a = torch.randn(128, 4096, device='cuda', dtype=torch.float8_e4m3fn)
b = torch.randn(4096, 4096, device='cuda', dtype=torch.float8_e4m3fn)
# If this crashes, set VLLM_USE_DEEP_GEMM=0
```

**Aggressive integration decision:** We wire DeepGEMM aggressively (enabled by
default). If it breaks, validation tests (superqwen3-validate.py) catch it,
and we fall back with VLLM_USE_DEEP_GEMM=0. Zero risk, maximum potential upside.

**Architecture note on Mega MoE:** DeepGEMM's Mega MoE fused kernel overlaps
NVLink communication with compute for EP (Expert Parallelism). On single Spark,
we don't use EP — all experts are on one GPU. So the Mega MoE path is irrelevant
for us. We only benefit from the grouped GEMMs (MoE expert batched matmuls).
