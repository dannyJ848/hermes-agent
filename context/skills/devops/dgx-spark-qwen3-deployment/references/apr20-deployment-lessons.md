# DGX Spark Deployment Lessons Learned (Apr 20 2026)

## Docker Image Entrypoint Bypass (Gotcha #95)

**Problem:** The AEON-7 DFlash image (`ghcr.io/aeon-7/vllm-dflash:latest`) has a broken entrypoint at `/usr/local/bin/dflash-entrypoint.sh` that auto-downloads `/models/target` and loops forever waiting for a model that never arrives.

**Solution:** Bypass the entrypoint completely and launch vLLM directly:

```bash
docker run -d --name qwen36-bf16 --gpus all --ipc host --shm-size 64gb \
  -p 8000:8000 -e HF_HUB_ENABLE_HF_TRANSFER=1 \
  -v /data/models:/root/.cache/huggingface \
  --restart unless-stopped \
  --entrypoint python3 \
  ghcr.io/aeon-7/vllm-dflash:latest \
  -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3.6-35B-A3B \
    --served-model-name qwen3.6-bf16 \
    --port 8000 --host 0.0.0.0 \
    --max-model-len 65536 \
    --max-num-batched-tokens 32768 \
    --max-num-seqs 512 \
    --max-cudagraph-capture-size 256 \
    --gpu-memory-utilization 0.90 \
    --kv-cache-dtype fp8_e5m2 \
    --enable-prefix-caching \
    --enable-chunked-prefill \
    --enforce-eager
```

**Key flags:**
- `--entrypoint python3` - CRITICAL: overrides broken dflash-entrypoint.sh
- `--enforce-eager` - See Gotcha #96 below

---

## vLLM V1 Torch.Compile OOMs on GB10 with 35B BF16 (Gotcha #96) — CORRECTED

**Problem:** vLLM V1 uses torch.compile + CUDA graph capture by default (`-O2`). On GB10 with Qwen3.6-35B-A3B BF16 (~65GB weights), the EngineCore crashes with NVRM OOM during model load or cudagraph context initialization.

**Empirical findings:**
- `-O2` (default): OOM during `torch.compile` kernel compilation
- `-O1` + `--gpu-memory-utilization 0.85` + `--max-cudagraph-capture-size 32`: STILL OOMs
- `--enforce-eager`: Boots in ~3-4 minutes, stable at ~29 tok/s
- The OOM signature in dmesg: `NVRM: kgrctxAllocMainCtxBuffer Out of memory`

**Root cause:** GB10 unified memory (128GB shared CPU/GPU) lacks sufficient contiguous GPU-addressable memory for cudagraph compilation scratch buffers after loading 65GB of BF16 weights. This is a hardware limit, not a config issue.

**Solution:** `--enforce-eager` is MANDATORY for 35B BF16 on GB10. Do NOT try -O1 or -O2.

```bash
# MANDATORY — no exceptions for this model on this hardware
--enforce-eager
```

**Performance:** ~29 tok/s single-request with `--enforce-eager`. The 40-50% speedup from CUDA graphs is unattainable on this hardware with this model size.

---

## BF16 + FP8 Cannot Coexist on 128GB GPU (Gotcha #97)

**Problem:** Attempting to run both BF16 and FP8 vLLM servers simultaneously fails with OOM errors.

**Empirical memory measurement:**
- BF16 model: ~65GB weights + ~15GB overhead/KV cache = ~80GB total
- FP8 model: ~34GB weights + ~15-20GB KV cache (at 64K context) = ~50GB total
- **Combined: ~130GB > 128GB available**

**Error messages:**
```
ValueError: Free memory on device cuda:0 (41.05/121.69 GiB) on startup is less than 
desired GPU memory utilization (0.9, 109.52 GiB)
```

**Solutions:**

1. **Run only one model at a time** (recommended):
   ```bash
   # Create switch script on Spark
   bash /data/switch-model.sh bf16  # stops FP8, starts BF16
   bash /data/switch-model.sh fp8   # stops BF16, starts FP8
   ```

2. **Reduce context length for secondary model** (if you must run both):
   ```bash
   # FP8 with minimal context to fit alongside BF16
   --max-model-len 8192  # Instead of 65536
   ```

3. **Use enforce-eager** to skip CUDA graph memory overhead

**Best practice:** Run BF16 as the primary server (quality mode). Switch to FP8 only when you need maximum speed and can tolerate the ~1% quality loss.

---

## FP8 KV Cache Incompatibility (Gotcha #98)

**Problem:** Using `--kv-cache-dtype fp8_e5m2` with FP8-quantized model weights causes a hard error.

**Error:**
```
ValueError: fp8_e5m2 kv-cache is not supported with fp8 checkpoints.
```

**Root cause:** FP8_e5m2 KV cache format is incompatible with FP8 model checkpoint format. The FP8 weights already use a specific quantization scheme that conflicts with the KV cache dtype.

**Solution:**
- For **BF16 models**: Use `--kv-cache-dtype fp8_e5m2` (works, gives 2x KV compression)
- For **FP8 models**: Omit `--kv-cache-dtype` entirely (vLLM auto-selects appropriate caching)

**BF16 launch (fp8_e5m2 works):**
```bash
--model Qwen/Qwen3.6-35B-A3B \
--kv-cache-dtype fp8_e5m2  # OK
```

**FP8 launch (no kv-cache-dtype flag):**
```bash
--model Qwen/Qwen3.6-35B-A3B-FP8
# Do NOT add --kv-cache-dtype fp8_e5m2
```

---

## HuggingFace Hub Install on Spark (Gotcha #99)

**Problem:** Fresh Spark installs don't have huggingface_hub, and standard pip install fails due to PEP 668 (system Python protection).

**Error:**
```
error: externally-managed-environment
```

**Solution:** Use `--break-system-packages` flag:

```bash
pip install --break-system-packages huggingface_hub
```

**Then authenticate in Python:**
```python
from huggingface_hub import login, snapshot_download
login(token="hf_...")

# For models
snapshot_download("Qwen/Qwen3.6-35B-A3B", local_dir="/data/models/Qwen3.6-35B-A3B")

# For datasets (CRITICAL: add repo_type='dataset')
snapshot_download(
    "nvidia/Nemotron-Post-Training-Dataset-v1",
    local_dir="/data/training-data/nemotron",
    repo_type='dataset'  # Required!
)
```

**Note:** The deprecated `huggingface-cli` command is not available on fresh Spark installs. Use the Python API directly.

---

## Dataset Download Requirements (Gotcha #100)

**Problem:** Dataset downloads fail with 404 or 401 errors if parameters are missing.

**Required for ALL dataset downloads:**

1. **`repo_type='dataset'` parameter**
   ```python
   # WRONG - causes 404
   snapshot_download("nvidia/Nemotron-Post-Training-Dataset-v1")
   
   # RIGHT
   snapshot_download("nvidia/Nemotron-Post-Training-Dataset-v1", repo_type='dataset')
   ```

2. **Authentication for gated repos**
   ```python
   from huggingface_hub import login
   login(token="hf_...")  # Must call before snapshot_download
   ```

**Full working example:**
```python
from huggingface_hub import login, snapshot_download
import os

# Authenticate with your HF token
login(token="hf_YOUR_TOKEN_HERE")

# Download Nemotron dataset
os.makedirs("/data/training-data/nemotron", exist_ok=True)
snapshot_download(
    "nvidia/Nemotron-Post-Training-Dataset-v1",
    local_dir="/data/training-data/nemotron",
    repo_type='dataset',  # REQUIRED
    local_dir_use_symlinks=False
)
```

---

## Summary: Updated Launch Commands

### BF16 Quality Server (Primary)
```bash
docker run -d --name qwen36-bf16 --gpus all --ipc host --shm-size 64gb \
  -p 8000:8000 \
  -e HF_HUB_ENABLE_HF_TRANSFER=1 \
  -v /data/models:/root/.cache/huggingface \
  --restart unless-stopped \
  --entrypoint python3 \
  ghcr.io/aeon-7/vllm-dflash:latest \
  -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3.6-35B-A3B \
    --served-model-name qwen3.6-bf16 \
    --port 8000 --host 0.0.0.0 \
    --max-model-len 65536 \
    --max-num-batched-tokens 32768 \
    --max-num-seqs 512 \
    --max-cudagraph-capture-size 256 \
    --gpu-memory-utilization 0.90 \
    --kv-cache-dtype fp8_e5m2 \
    --enable-prefix-caching \
    --enable-chunked-prefill \
    --enforce-eager
```

### FP8 Speed Server (Switch to this when needed)
```bash
docker run -d --name qwen36-fp8 --gpus all --ipc host --shm-size 64gb \
  -p 8001:8000 \
  -e HF_HUB_ENABLE_HF_TRANSFER=1 \
  -v /data/models:/root/.cache/huggingface \
  --restart unless-stopped \
  --entrypoint python3 \
  ghcr.io/aeon-7/vllm-dflash:latest \
  -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3.6-35B-A3B-FP8 \
    --served-model-name qwen3.6-fp8 \
    --port 8000 --host 0.0.0.0 \
    --max-model-len 65536 \
    --max-num-batched-tokens 32768 \
    --max-num-seqs 512 \
    --max-cudagraph-capture-size 256 \
    --gpu-memory-utilization 0.90 \
    --enable-prefix-caching \
    --enable-chunked-prefill \
    --enforce-eager
```

**Note:** No `--kv-cache-dtype` flag for FP8 model!

---

## Health Daemon Grace Period (Gotcha #101) — APR 21 UPDATE

**Problem:** A health daemon with a 30-second check interval kills the vLLM container during model load (3-4 minutes), creating an infinite restart loop. Each restart leaves a zombie EngineCore holding GPU memory, making subsequent loads OOM.

**Symptoms:**
- Container starts, runs for 30-60s, then restarts
- nvidia-smi shows multiple zombie `VLLM::EngineCore` processes
- GPU memory shows high usage even though no container is "Up"

**Solution:** Health daemon MUST have a grace period for initial model load:
- **Plain BF16:** `GRACE_PERIOD=360` (6 minutes)
- **BF16 + DFlash:** `GRACE_PERIOD=720` (12 minutes) — DFlash load takes ~10 min

```bash
GRACE_PERIOD=360  # 6 minutes for plain BF16, 720 for DFlash

# Wait before FIRST health check
sleep "$GRACE_PERIOD"

# Also wait after EACH restart before checking again
sleep "$GRACE_PERIOD"
```

**Zombie cleanup after crash:**
```bash
# Nuclear reset — kills ALL vLLM processes and reclaims GPU memory
sudo killall -9 VLLM::EngineCore python3
```

---

## HF Token + Offline Mode Required for Startup (Gotcha #102)

**Problem:** Even with the model fully cached locally, the vLLM API server crashes during startup because it tries to download tokenizer metadata, generation config, or chat template from HuggingFace Hub. This happens inside the container where there may be no auth.

**Symptoms:**
- Container exits immediately after launch
- Logs show tokenizer fetch timeouts or 401 errors
- `huggingface_hub.utils._errors.LocalEntryNotFoundError`

**Solution:** Pass three env vars to EVERY vLLM container:

```bash
-e HF_TOKEN=hf_YOUR_TOKEN_HERE \
-e TRANSFORMERS_OFFLINE=1 \
-e HF_HUB_OFFLINE=1
```

The `HF_TOKEN` is needed even in "offline" mode because some tokenizers validate against the hub on first load. `TRANSFORMERS_OFFLINE=1` and `HF_HUB_OFFLINE=1` prevent any network fetch attempts.

---

## API Key Authentication (Gotcha #103)

**Problem:** vLLM serves on 0.0.0.0 with no auth by default. Anyone on the network can use your GPU.

**Solution:** Add `--api-key` to vLLM and mirror it in Hermes config:

```bash
# vLLM serve flag
--api-key $(openssl rand -hex 32)

# Hermes config.yaml
providers:
  spark-bf16:
    api_key: "YOUR_64_CHAR_HEX_KEY"
```

**Test with auth:**
```bash
curl -H "Authorization: Bearer $API_KEY" http://spark-ip:8000/v1/models
```

---

## DFlash Speculative Decoding Status (Gotcha #104) — APR 21 UPDATE

**Current status:** The finalized DFlash weights (`z-lab/Qwen3.6-35B-A3B-DFlash`, 905MB) are downloaded. The `ghcr.io/aeon-7/vllm-dflash:latest` image accepts `--speculative-config '{"method": "dflash", "model": "/root/.cache/huggingface/Qwen3.6-35B-A3B-DFlash", "num_speculative_tokens": 15}'` without config validation errors.

**APR 21 TESTED AND CONFIRMED WORKING with --enforce-eager:**
- DFlash works WITH `--enforce-eager` (no CUDA graphs needed)
- Actual speedup: 29 tok/s (plain BF16) → 38-42 tok/s (DFlash) = ~1.3x
- 512-token requests: 34-37 tok/s
- Short requests (50 tokens): ~29 tok/s (unchanged)
- **Load time: ~10 minutes** (vs ~4 min plain BF16)
- **First request penalty: ~37 seconds** (DFlash draft model warmup)

**CRITICAL: DFlash is INCOMPATIBLE with `--kv-cache-dtype fp8_e5m2`**
The draft model uses non-causal attention. None of the attention backends support both non-causal attention AND fp8_e5m2 KV cache:
```
FLASH_ATTN: [kv_cache_dtype not supported]
FLASHINFER: [non-causal attention not supported]
TRITON_ATTN: [non-causal attention not supported]
FLEX_ATTENTION: [kv_cache_dtype not supported, non-causal attention not supported]
```
**Fix:** Omit `--kv-cache-dtype fp8_e5m2` when using DFlash. vLLM will use the default KV cache dtype.

**Health daemon grace period for DFlash:**
DFlash load takes ~10 minutes. A 6-minute grace period causes the daemon to kill the container mid-load, creating an infinite restart loop.
**Fix:** Use `GRACE_PERIOD=720` (12 minutes) when DFlash is enabled.

**Updated BF16+DFlash launch command:**
```bash
docker run -d --name qwen36-bf16 --gpus all --ipc host --shm-size 64gb \
  -p 8000:8000 \
  -e HF_HUB_ENABLE_HF_TRANSFER=1 \
  -e HF_TOKEN=hf_YOUR_TOKEN_HERE \
  -e TRANSFORMERS_OFFLINE=1 \
  -e HF_HUB_OFFLINE=1 \
  -v /data/models:/root/.cache/huggingface \
  --restart unless-stopped \
  --entrypoint python3 \
  ghcr.io/aeon-7/vllm-dflash:latest \
  -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3.6-35B-A3B \
    --served-model-name qwen3.6-bf16 \
    --port 8000 --host 0.0.0.0 \
    --max-model-len 65536 \
    --max-num-batched-tokens 32768 \
    --max-num-seqs 512 \
    --max-cudagraph-capture-size 256 \
    --gpu-memory-utilization 0.90 \
    --enable-prefix-caching \
    --enable-chunked-prefill \
    --enforce-eager \
    --api-key $(openssl rand -hex 32) \
    --speculative-config '{"method": "dflash", "model": "/root/.cache/huggingface/Qwen3.6-35B-A3B-DFlash", "num_speculative_tokens": 15}'
```

**Note:** The DFlash model path inside the container is `/root/.cache/huggingface/Qwen3.6-35B-A3B-DFlash` (via volume mount `-v /data/models:/root/.cache/huggingface`). Using the HuggingFace hub ID `z-lab/Qwen3.6-35B-A3B-DFlash` fails with "Invalid repository ID or local directory specified" because the container runs in offline mode.

**Previous estimate was wrong:** The "expected 1.5-2x speedup (45-55 tok/s)" was based on B200 benchmarks. On GB10 with `--enforce-eager`, actual speedup is ~1.3x (38-42 tok/s). Still worth keeping for 24/7 deployments.
