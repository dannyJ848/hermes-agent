# Apr 21 2026 Performance Audit Findings

Live testing on DGX Spark (GB10, 10.0.0.171) with abliterated Qwen3.6-35B-A3B BF16 + DFlash.

## CRITICAL: Image Tag Corruption

### `flashkda-disabled` Tag = CORRUPTED OUTPUT
- **NEVER use `ghcr.io/aeon-7/vllm-dflash:flashkda-disabled`** for production serving
- Produces garbage/repeating tokens on both stock and abliterated Qwen3.6 weights
- Tested with stock model: output was repeating Chinese character "和" infinitely
- Root cause: unknown image corruption (not weight-related — stock model also failed)
- **Safe image:** `ghcr.io/aeon-7/vllm-dflash:latest` (digest e26c03b8738d, 18.1GB)

## Verified Results

### 1. `-O1`/`-O2` CUDA Graphs: SYSTEM CRASH
- **Test:** Removed `--enforce-eager`, added `-O1` to vLLM serve command
- **Result:** System lockup during CUDA graph capture. SSH daemon became unresponsive.
- **Recovery:** Required physical power cycle. Remote SSH unreachable for 5+ minutes.
- **Conclusion:** `--enforce-eager` is MANDATORY on GB10 with Qwen3.6 BF16 + DFlash.
- **Root cause:** NVRM context buffer allocation fails on unified memory architecture.
- **Note:** Even with `--language-model-only` freeing VRAM, -O1 still crashes.

### 2. `--language-model-only` + DFlash = DEADLOCK
- **Test:** Added `--language-model-only` to DFlash-enabled config
- **Result:** EngineCore runs at ~70% CPU but never processes requests. All chat completion requests timeout after 120s.
- **API server responds** to `/v1/models` (returns 200) but `/v1/chat/completions` hangs indefinitely.
- **Without DFlash:** `--language-model-only` works fine (~28.9 tok/s, clean output)
- **Without `--language-model-only`:** DFlash works fine (~40.7 tok/s, clean output)
- **Conclusion:** These two optimizations are MUTUALLY EXCLUSIVE on the `latest` AEON-7 image. Use DFlash, skip `--language-model-only`.

### 3. `--performance-mode throughput` + DFlash = DEADLOCK
- **Test:** Added `--performance-mode throughput` to DFlash-enabled config
- **Result:** Same deadlock pattern — EngineCore at ~70% CPU, requests timeout
- **Conclusion:** `--performance-mode throughput` is BROKEN with DFlash on vLLM 0.19.1rc1

### 4. Safe Config: Baseline + DFlash Only
Best verified configuration (clean output, no hangs, stable):
```bash
docker run -d --name qwen36-bf16 --gpus all --ipc host --shm-size 64gb -p 8000:8000 \
  -e VLLM_ATTENTION_BACKEND=FLASH_ATTN \
  -e HF_HUB_ENABLE_HF_TRANSFER=1 \
  -e HF_TOKEN=<token> \
  -e TRANSFORMERS_OFFLINE=1 \
  -e HF_HUB_OFFLINE=1 \
  -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
  -v /data/models:/root/.cache/huggingface \
  --restart unless-stopped \
  --entrypoint python3 ghcr.io/aeon-7/vllm-dflash:latest \
  -m vllm.entrypoints.openai.api_server \
  --model /root/.cache/huggingface/Qwen3.6-35B-A3B-Uncensored \
  --served-model-name qwen3.6-uncensored \
  --port 8000 --host 0.0.0.0 \
  --max-model-len 262144 \
  --max-num-batched-tokens 65536 \
  --max-num-seqs 512 \
  --gpu-memory-utilization 0.95 \
  --enable-prefix-caching \
  --enable-chunked-prefill \
  --enforce-eager \
  --api-key <key> \
  --speculative-config '{"method": "dflash", "model": "/root/.cache/huggingface/Qwen3.6-35B-A3B-DFlash", "num_speculative_tokens": 15}'
```

**Benchmarks:**
- Run 1: 256 tokens in 6.58s = 38.9 tok/s (DFlash warmup penalty)
- Run 2: 256 tokens in 6.06s = 42.2 tok/s
- Run 3: 256 tokens in 6.67s = 38.4 tok/s
- Run 4: 256 tokens in 6.08s = 42.1 tok/s
- Run 5: 256 tokens in 6.11s = 41.9 tok/s
- **Average: 40.7 tok/s sustained**

### 5. `--language-model-only` Alone: Marginal Improvement
- Without DFlash: 28.9 tok/s (no language-model-only) vs ~29.5 tok/s (with it) — negligible
- With DFlash: cannot use due to deadlock
- **Conclusion:** Skip this flag. The VRAM savings are irrelevant on 128GB unified memory.

### 6. SM121 Gencode Audit: `sm_121f` Missing
- AEON-7 image (`ghcr.io/aeon-7/vllm-dflash:latest`) analyzed via `strings` and `cuobjdump`
- **2,784 occurrences** of `-arch sm_121a -m 64` cubins
- **1 occurrence each** of `sm_121f` metadata only (mcpu, opt-arch)
- No actual `sm_121f` compiled cubins present
- Community "50%+ improvement" fix requires `compute_120f`/`compute_121f` for TMA Warp-Specialized grouped GEMM
- **Impact:** MoE throughput potentially 30-50% below theoretical max on workstation Blackwell

### 7. FlashInfer Hybrid Attention Bug: Not Affected
- Bug (vLLM #36241) causes precision loss on hybrid models with FlashInfer 0.4+
- Our container uses `VLLM_ATTENTION_BACKEND=FLASH_ATTN` (verified via `docker inspect`)
- 3-turn conversation test passed cleanly (math + tool calling + code generation)
- No action needed

### 8. SGLang: WORKING via Pre-Built Docker Image (UPDATED Apr 22)

**Previous conclusion was wrong.** Standard sglang-venv installation fails on SM121a, but a community pre-built Docker image works.

#### Standard sglang-venv: FAILURE CHAIN
1. CPU-only PyTorch (`2.9.1+cpu`) → install `torch==2.9.1+cu128`
2. Triton 3.5.1 ptxas error: `sm_121a` not recognized → upgrade to Triton 3.6.0
3. FlashInfer JIT requires `ninja-build` → install via apt
4. `cudaErrorNoKernelImageForDevice` → FlashInfer kernels don't support SM121a
5. Docker container approach: `pip install sglang` overwrites custom `torch 2.12.0+cu130`

**Verdict:** sglang-venv path is dead. Use pre-built image.

#### Working Config: Pre-Built Docker Image
```bash
docker run -d --name sglang-dgx --gpus all --privileged --ipc host --network host \
  -v /data/models:/root/.cache/huggingface \
  scitrera/dgx-spark-sglang:0.5.8-t5 \
  sglang serve \
    --model-path /root/.cache/huggingface/Qwen3.6-35B-A3B-Uncensored \
    --port 8000 --host 0.0.0.0 \
    --mem-fraction-static 0.95 \
    --max-running-requests 512 \
    --chunked-prefill-size 65536 \
    --disable-cuda-graph \
    --attention-backend triton
```

**Critical flags for GB10:**
- `--disable-cuda-graph` : Required to avoid illegal memory access on sm_121a (GitHub #19799)
- `--attention-backend triton` : Required for hybrid GDN models (FlashInfer backend crashes with kernel image error)

**Performance:** ~28 tok/s sustained on Qwen3.6-35B-A3B BF16. Slower than vLLM+DFlash (~42 tok/s) because CUDA graphs are disabled and Triton attention replaces FlashInfer.

**EAGLE-3 speedup potential:** Reddit reports 60 tok/s on DGX Spark with SGLang + EAGLE-3 using `togethercomputer/Aurora-Spec-Qwen3-Coder-Next-FP8` draft model. Training an EAGLE-3 draft model for Qwen3.6 is possible via SafeAILab/EAGLE or BaldEagle repos (~1 day project on GB10).

**Image details:**
- `scitrera/dgx-spark-sglang:0.5.8-t5` : SGLang 0.5.8, PyTorch 2.10.0, CUDA 13.1.1, Triton 3.6.0, FlashInfer 0.6.3, Transformers 5.1.0
- Also available: `scitrera/dgx-spark-sglang:0.5.8-t4` (Transformers 4.57.6)

**Build from source alternative:** NVIDIA forums guide at https://forums.developer.nvidia.com/t/build-sglang-from-source-on-blackwell-pro-6000-dgx-spark/360785 — requires compiling `sgl-kernel` with `TORCH_CUDA_ARCH_LIST="12.1a"`.

### 9. Triton Cache Can Corrupt Between Restarts
- Path: `/data/.triton_cache` (host-mounted, persists across `docker rm`)
- Corrupted cache (from `-O1` crash or `--performance-mode throughput` deadlock) can cause EngineCore to hang at 70% CPU
- **Fix:** `rm -rf /data/.triton_cache` before starting a fresh container after any crash/deadlock

### 10. `--performance-mode throughput` Alone: Deadlock
- Same hang behavior as with DFlash — EngineCore stuck, requests timeout
- **Conclusion:** This flag is fundamentally broken on vLLM 0.19.1rc1 with Qwen3.6 GDN hybrid. Do not use.

## Recommendations

1. **Use `ghcr.io/aeon-7/vllm-dflash:latest` ONLY** — never `flashkda-disabled`
2. **Keep `--enforce-eager`** — never test -O1/-O2 on GB10 again
3. **Use DFlash, skip `--language-model-only`** — they deadlock when combined
4. **Skip `--performance-mode throughput`** — causes deadlock on this vLLM build
5. **Clear `/data/.triton_cache` after any crash** — prevents persistent corruption
6. **SGLang needs CUDA PyTorch reinstall** before benchmarking
7. **Investigate `sm_121f` rebuild** — requires rebuilding AEON-7 image with `compute_121f` gencode
8. **Monitor FlashInfer** — if switching backend in future, verify PR #36241 fix is included
