# vLLM Speedup Landscape — May 15, 2026

**Date:** May 15, 2026
**vLLM Version:** 0.20.2 (stable), nightly available
**Model Context:** Qwen3.6-27B-Uncensored on DGX Spark (GB10, Blackwell SM121)

## Current vLLM (0.20.2) — What's Available

| Feature | Status | Speedup | Notes |
|---------|--------|---------|-------|
| **FlashAttention 2** | Stable | Baseline | Default, works everywhere |
| **FlashAttention 3** | Stable | ~1.2-1.5x | Hopper/Blackwell, automatic on SM121 |
| **FlashAttention 4** | **NOT in vLLM** | N/A | Only SGLang supports FA4; vLLM only FA2/FA3 |
| **CUDA Graphs** | Stable | ~1.1-1.3x | 96 sizes captured, 2.14 GiB pool |
| **torch.compile** | Stable | ~1.05-1.1x | Compilation caching, faster warm startup |
| **Chunked Prefill** | Stable | Better batching | max 8192 tokens, improves concurrency |
| **N-gram Speculative** | Stable | 0-20% | 60-85% acceptance, zero training needed |
| **EAGLE-3** | Stable | ~2-4x | Needs trained checkpoint, not available for Qwen3.6-27B |
| **P-EAGLE** | v0.16.0+ | ~1.05-1.69x over EAGLE-3 | Parallel draft generation, single forward pass |
| **DFlash** | v0.20.0+ | ~6x (claimed) | Block diffusion, needs gated HF checkpoint |
| **Prefix Caching** | **DISABLED for hybrid** | 0% | Qwen3.6 reports `is_prefix_caching_supported: False` |
| **Disaggregated Prefill/Decode** | Experimental | Variable | Separate prefill/decode instances |

## What's NOT Working for Qwen3.6-27B

### 1. FlashAttention 4
- vLLM does NOT support FA4 as an attention backend
- Only FA2 and FA3 are supported
- `VLLM_FLASH_ATTN_VERSION=4` triggers: `ValueError: Unsupported FA version: 4`
- SGLang supports FA4 on B200/Blackwell

### 2. Prefix Caching
- Model reports `is_prefix_caching_supported: False`
- `supports_mamba_prefix_caching: False`
- Hybrid architecture (48 linear + 16 full attention layers) fundamentally incompatible
- vLLM silently disables it regardless of `--enable-prefix-caching` flag
- See `references/hybrid-model-prefix-caching-limitations.md` for full root cause

### 3. DFlash / EAGLE-3 / P-EAGLE Checkpoints
- No trained speculative decoding checkpoints available for Qwen3.6-27B
- DFlash requires gated HF access to `z-lab/Qwen3.6-27B-DFlash`
- P-EAGLE checkpoints exist for GPT-OSS 120B, GPT-OSS 20B, Qwen3-Coder-30B — NOT Qwen3.6-27B

## SGLang Alternative — 3-5x Faster?

Community benchmarks show SGLang is **3.1-5.3x faster** than vLLM on Qwen3.5 models:
- https://github.com/vllm-project/vllm/issues/36215
- SGLang has RadixAttention (better prefix caching)
- SGLang supports FlashAttention 4
- SGLang has better scheduling for hybrid models

**Official Docker image:** `lmsysorg/sglang:latest` (11.8 GB, updated 2026-05-05)
- Pull: `docker pull lmsysorg/sglang:latest`
- Requires ~12GB disk space + model size
- Available tags: `latest`, `deepep`, `v{version}`
- Docker Hub: https://hub.docker.com/r/lmsysorg/sglang

**Trade-offs:**
- SGLang on GB10 requires `--disable-cuda-graph` (illegal memory access on sm_121a)
- SGLang uses `--attention-backend triton` instead of FlashInfer (kernel image missing)
- Without CUDA graphs, SGLang is ~28 tok/s vs vLLM+DFlash at ~42 tok/s
- SGLang+EAGLE-3 could reach ~60 tok/s (community claim, unverified)

**Pre-built image for GB10:** `scitrera/dgx-spark-sglang:0.5.8-t5`
- SGLang 0.5.8, PyTorch 2.10.0, CUDA 13.1.1, Triton 3.6.0
- Includes SM121a patches that standard SGLang installations lack

**Docker Compose deployment (official image):**
```yaml
services:
  sglang:
    image: lmsysorg/sglang:latest
    container_name: sglang
    volumes:
      - ${HOME}/.cache/huggingface:/root/.cache/huggingface
    restart: always
    network_mode: host
    privileged: true
    environment:
      - HF_TOKEN=<secret>
    entrypoint: python3 -m sglang.launch_server
    command: --model-path /data/models/Qwen3.6-27B-Uncensored --host 0.0.0.0 --port 30000
    ulimits:
      memlock: -1
      stack: 67108864
    ipc: host
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:30000/health || exit 1"]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## Upcoming vLLM Features (Roadmap Q2 2026)

From vLLM GitHub issue #39749 (Roadmap Q2 2026):

### Model Runner V2 (MRV2)
- Modular, faster core
- Better out-of-box performance
- Auto-tuning

### Large Scale Serving
- Zero-cost async EPLB (expert load balancing)
- Fault-tolerant EP
- Elastic EP (scale up/down)
- Bidirectional KV transfers
- PD (prefill-decode) disaggregation

### Speculative Decoding Hardening
- "Pay off technical debt accumulated in V1's speculative decoding"
- Production-ready speculative decoding features
- Better integration with thinking/reasoning budgets

### FlashAttention 4 Integration
- Open PR exists but not merged
- No official timeline for SM100 (B200) support
- Currently only FA2/FA3 in stable releases

## Verification Commands

### Check vLLM version and features
```bash
docker exec vllm-merged python3 -c "import vllm; print(vllm.__version__)"
```

### Check model prefix caching support
```bash
docker exec vllm-merged python3 -c '
from vllm.engine.arg_utils import EngineArgs
args = EngineArgs(model="/data/models/Qwen3.6-27B-Uncensored", max_model_len=131072, enable_prefix_caching=True, gpu_memory_utilization=0.9)
ec = args.create_engine_config()
print("is_hybrid:", ec.model_config.is_hybrid)
print("supports_mamba_prefix_caching:", ec.model_config.supports_mamba_prefix_caching)
print("is_prefix_caching_supported:", ec.model_config.is_prefix_caching_supported)
'
```

### Check FlashAttention version
```bash
docker exec vllm-merged python3 -c '
from vllm.attention.utils.fa_utils import get_flash_attn_version
print("FA version:", get_flash_attn_version())
'
```

### Check speculative decoding status
```bash
docker exec vllm-merged python3 -c '
from vllm.engine.arg_utils import EngineArgs
args = EngineArgs(model="/data/models/Qwen3.6-27B-Uncensored", max_model_len=131072)
ec = args.create_engine_config()
print("speculative config:", ec.speculative_config)
'
```

## Recommendations

### For Maximum Speed on Qwen3.6-27B (Today)
1. **vLLM 0.20.2 with FP8 weights** — Working, ~1.5x over BF16
2. **N-gram speculative decoding** — Working, 0-20% variable
3. **Chunked prefill + CUDA graphs** — Working, better batching
4. **Concurrent request tuning** — Sweet spot 64-128 requests

### For Future Speedups
1. **Track vLLM nightly** — Check if hybrid prefix caching is fixed
2. **Train/obtain EAGLE-3/P-EAGLE checkpoint** — 2-4x potential
3. **Evaluate SGLang** — 3-5x claimed, but CUDA graph issues on GB10
4. **Wait for Model Runner V2** — Better out-of-box performance

### What NOT to Waste Time On
1. **FlashAttention 4 in vLLM** — Not supported, no timeline
2. **Prefix caching on Qwen3.6 hybrid** — Architecture-disabled, unfixable via config
3. **DFlash without checkpoint** — Requires gated HF model access
4. **torch.compile for speed** — Marginal gains, compilation overhead

## Key Sources

- vLLM releases: https://github.com/vllm-project/vllm/releases
- vLLM roadmap Q2 2026: https://github.com/vllm-project/vllm/issues/39749
- P-EAGLE in vLLM: https://aws.amazon.com/blogs/machine-learning/p-eagle-faster-llm-inference-with-parallel-speculative-decoding-in-vllm/
- DFlash overview: https://www.spheron.network/blog/dflash-block-diffusion-speculative-decoding-gpu-cloud/
- SGLang vs vLLM on Qwen3.5: https://github.com/vllm-project/vllm/issues/36215
- vLLM forums (FA4): https://discuss.vllm.ai/t/how-to-apply-fa4-on-b200/2133
