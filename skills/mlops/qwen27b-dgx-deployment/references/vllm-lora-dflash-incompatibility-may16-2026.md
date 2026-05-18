# vLLM LoRA + DFlash Speculative Decoding Incompatibility

**Date:** May 16, 2026
**System:** DGX Spark, vLLM 0.20.2, Qwen3.6-27B-Uncensored + merged-lora
**Issue:** LoRA adapter becomes catastrophically slow when DFlash speculative decoding is enabled

## Symptoms

- Base model (`/data/models/Qwen3.6-27B-Uncensored`): ~12 tok/s — normal performance
- LoRA adapter (`merged-lora`): ~0.6 tok/s, requests timeout after 60s
- vLLM container shows `cudagraph_specialize_lora=True` in compilation config
- DFlash draft model loads and initializes normally
- No error messages in logs — just extreme slowness

## Root Cause Analysis

1. **Draft model assumes base weights:** DFlash generates speculative tokens using the base model (Qwen3.6-27B-Uncensored). The draft has no knowledge of LoRA weights.

2. **High rejection rate during verification:** When the target model verifies draft tokens with LoRA weights applied, the tokens don't match the LoRA-modified distribution. This causes near-constant rejection and rollback.

3. **CUDA graph specialization overhead:** vLLM compiles separate CUDA graphs for each LoRA (`cudagraph_specialize_lora=True`). With speculative decoding, each rejected token triggers re-specialization, compounding the overhead.

4. **The combination is multiplicative:** Draft overhead × LoRA overhead × rejection rate = ~20x slowdown.

## Verification Commands

```bash
# Test base model speed
python3 << 'PYEOF'
import time, requests
url = "http://localhost:8000/v1/chat/completions"
payload = {
    "model": "/data/models/Qwen3.6-27B-Uncensored",
    "messages": [{"role": "user", "content": "Hi"}],
    "max_tokens": 20,
    "temperature": 0.7
}
start = time.time()
resp = requests.post(url, json=payload, timeout=60)
elapsed = time.time() - start
tokens = resp.json()["usage"]["completion_tokens"]
print(f"Base model: {tokens} tokens in {elapsed:.1f}s = {tokens/elapsed:.1f} tok/s")
PYEOF

# Test LoRA speed
python3 << 'PYEOF'
import time, requests
url = "http://localhost:8000/v1/chat/completions"
payload = {
    "model": "merged-lora",
    "messages": [{"role": "user", "content": "Hi"}],
    "max_tokens": 20,
    "temperature": 0.7
}
start = time.time()
resp = requests.post(url, json=payload, timeout=60)
elapsed = time.time() - start
tokens = resp.json()["usage"]["completion_tokens"]
print(f"LoRA: {tokens} tokens in {elapsed:.1f}s = {tokens/elapsed:.1f} tok/s")
PYEOF
```

**Interpretation:**
- Base >10 tok/s + LoRA <2 tok/s = speculative decoding incompatible with LoRA
- Both >10 tok/s = issue is elsewhere (check LoRA weights, model compatibility)
- Both <2 tok/s = vLLM is stuck or GPU issue (restart container)

## Solutions

### Option 1: Serve LoRA without speculative decoding (recommended)

Remove `--speculative-config` from the deploy script. Stable but slower overall throughput.

Deploy script: `/tmp/deploy_vllm_lora_only.sh`

```bash
docker run -d --name vllm-merged \
  --runtime nvidia --gpus all -p 8000:8000 \
  -v /data:/data \
  -e CUDA_VISIBLE_DEVICES=0 \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --enable-lora \
  --lora-modules merged-lora=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --max-lora-rank 256 \
  --max-model-len 131072 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.90 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --enable-chunked-prefill \
  --quantization fp8 \
  --kv-cache-dtype auto \
  --dtype bfloat16 \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 128
```

**Tradeoffs:**
- + Stable LoRA performance
- + No compatibility issues
- - ~2x slower than with speculative decoding
- - No speedup from draft model

### Option 2: Merge LoRA into base model permanently

```python
from peft import AutoPeftModelForCausalLM
import torch

model = AutoPeftModelForCausalLM.from_pretrained(
    "/data/SpecForge/custom_dflash/checkpoints/final_model",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
merged = model.merge_and_unload()
merged.save_pretrained("/data/models/Qwen3.6-27B-Uncensored-Merged")

# Copy tokenizer files
import shutil, os
base = "/data/models/Qwen3.6-27B-Uncensored"
merged_dir = "/data/models/Qwen3.6-27B-Uncensored-Merged"
for f in ["tokenizer.json", "tokenizer_config.json", "vocab.json"]:
    if os.path.exists(os.path.join(base, f)):
        shutil.copy(os.path.join(base, f), os.path.join(merged_dir, f))
```

Then serve with DFlash:
```bash
--model /data/models/Qwen3.6-27B-Uncensored-Merged \
--speculative-config '{"method":"dflash","model":"/data/models/Qwen3.5-27B-DFlash","num_speculative_tokens":5}'
```

**Tradeoffs:**
- + Best performance (speculative decoding works)
- + No LoRA overhead
- - Cannot swap LoRAs at runtime
- - Requires re-merge after each training iteration
- - Uses 2x disk space (~110GB for base + merged)

### Option 3: Hybrid routing

Use base model for speed-critical tasks, LoRA for quality-critical tasks:

```yaml
# Hermes config
providers:
  local-dgx-base:
    base_url: http://localhost:8000/v1
    model: /data/models/Qwen3.6-27B-Uncensored  # fast, no LoRA
  local-dgx-lora:
    base_url: http://localhost:8000/v1
    model: merged-lora  # slow, high quality

routing_rules:
  - pattern: "^(code|debug|shell|system).*"
    provider: local-dgx-base
    priority: 1
  - pattern: "^(write|analyze|reason|evaluate).*"
    provider: local-dgx-lora
    priority: 2
```

**Tradeoffs:**
- + Best of both worlds
- - Complex routing logic
- - User must know which model to use

## Related Issues

- EAGLE-3 speculative decoding also incompatible with Qwen3.6 (different reasons) — see `references/eagle3-qwen36-investigation-may15-2026.md`
- SGLang incompatible with Qwen3.6 hybrid architecture — see `dgx-spark-qwen3-deployment:references/sglang-qwen36-hybrid-mamba-incompatibility.md`
- DFlash is the only working speculative decoding method for Qwen3.6, but NOT with LoRA

## Decision Log

**May 16, 2026:** Discovered during speed testing. Base model 12 tok/s, LoRA 0.6 tok/s. Investigated CUDA graphs, speculative config, LoRA compatibility. Confirmed DFlash + LoRA interaction is the cause.

**Decision:** Document as pitfall #35 in qwen27b-dgx-deployment skill. Provide three solutions with tradeoffs. Default recommendation: serve without speculative decoding for stability, merge permanently for production.

**May 16, 2026 (Update):** Deployed permanently merged model (`final_model_merged`) with DFlash speculative decoding. The merged model is located at `/data/SpecForge/custom_dflash/checkpoints/final_model_merged` (51GB). vLLM serves it directly without `--enable-lora` or `--lora-modules`. DFlash draft model (`/data/models/Qwen3.5-27B-DFlash`) works at full speed with `num_speculative_tokens=5`. Performance: ~16.2 tok/s.

**Merged model deploy command:**
```bash
docker run -d --name vllm-merged \
  --runtime nvidia --gpus all -p 8000:8000 \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints:/data/SpecForge/custom_dflash/checkpoints \
  -e CUDA_VISIBLE_DEVICES=0 \
  vllm/vllm-openai:latest \
  --model /data/SpecForge/custom_dflash/checkpoints/final_model_merged \
  --max-model-len 131072 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.90 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --enable-chunked-prefill \
  --speculative-config '{"method":"dflash","model":"/data/models/Qwen3.5-27B-DFlash","num_speculative_tokens":5}' \
  --quantization fp8 \
  --kv-cache-dtype auto \
  --dtype bfloat16 \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 128
```

**Key differences from LoRA deploy:**
- No `--enable-lora` or `--lora-modules`
- `--model` points directly to merged weights
- `--speculative-config` works normally (no LoRA conflict)
- Hermes config uses `default: merged-lora` (name preserved for compatibility) pointing to vLLM at `http://localhost:8000/v1`

**Verification:**
```bash
# POST to merged model (GET /v1/models returns 404 for merged models — use POST)
curl -s --max-time 30 -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "merged-lora", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 20}'
```
