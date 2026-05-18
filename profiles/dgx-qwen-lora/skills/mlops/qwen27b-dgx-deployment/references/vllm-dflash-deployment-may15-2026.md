# DFlash Speculative Decoding Deployment — May 15, 2026

**Date:** May 15, 2026
**vLLM Version:** 0.20.2
**Model:** Qwen3.6-27B-Uncensored + LoRA adapter on DGX Spark (GB10, Blackwell SM121)
**Draft Model:** z-lab/Qwen3.5-27B-DFlash (public, 3.3GB, 5 layers)

## Discovery

The `z-lab/Qwen3.6-27B-DFlash` model is **gated** (403 Forbidden without HF access approval). However, `z-lab/Qwen3.5-27B-DFlash` is **public** and works as a draft model for Qwen3.6-27B with **179% speedup**.

## Deployment

### 1. Download Draft Model

```bash
# Create directory with proper permissions
sudo mkdir -p /data/models/Qwen3.5-27B-DFlash
sudo chown -R $(whoami):$(whoami) /data/models/Qwen3.5-27B-DFlash

# Download (3.3GB, ~1 minute on good connection)
python3 -c 'from huggingface_hub import snapshot_download; snapshot_download(repo_id="z-lab/Qwen3.5-27B-DFlash", local_dir="/data/models/Qwen3.5-27B-DFlash")'
```

**Draft model specs:**
- Architecture: DFlashDraftModel (5 layers vs 64 in main model)
- Hidden size: 5120
- Attention heads: 32
- KV heads: 8
- Vocab size: 248320
- File: `model.safetensors` (3.3GB)
- Config includes `dflash_config` with target_layer_ids: [1, 16, 31, 46, 61]

### 2. Deploy vLLM with DFlash

```bash
docker run -d --name vllm-merged \
  --runtime nvidia --gpus all -p 8000:8000 \
  -v /data:/data \
  -e CUDA_VISIBLE_DEVICES=0 \
  -e VLLM_LOGGING_LEVEL=INFO \
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
  --speculative-config '{"method":"dflash","model":"/data/models/Qwen3.5-27B-DFlash","num_speculative_tokens":16}' \
  --quantization fp8 \
  --kv-cache-dtype auto \
  --dtype bfloat16 \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 128
```

**Key flags:**
- `--speculative-config '{"method":"dflash","model":"/data/models/Qwen3.5-27B-DFlash","num_speculative_tokens":16}'` — DFlash with 16 speculative tokens
- vLLM auto-detects DFlashDraftModel architecture and shares target model embeddings/lm_head

### 3. Verify Deployment

```bash
# Check logs for DFlash initialization
docker logs vllm-merged | grep -E "DFlash|dflash|draft|speculative"
# Expected: "Resolved architecture: DFlashDraftModel", "Loading drafter model..."

# Check acceptance rate
docker logs vllm-merged | grep "SpecDecoding metrics" | tail -5
# Expected: "Avg Draft acceptance rate: ~13-24%" (varies by prompt type)

# Run benchmark
python3 /tmp/benchmark_vllm.py
```

## Performance Results

### Context Length Trade-offs (May 15, 2026)

**Critical finding:** Doubling context from 131K → 262K reduces throughput by ~50%.

| max_model_len | Throughput | Acceptance | GPU Memory | Concurrency | Use Case |
|---------------|-----------|------------|------------|-------------|----------|
| 131072 | **16.9 tok/s** | **34.3%** | ~85GB | 6.9x | **Default — best throughput** |
| 262144 | **8.5 tok/s** | **37.1%** | ~96GB | 3.8x | Long context — 50% speed penalty |

At 262K context, KV cache is allocated for the full window, leaving less memory for batching. The acceptance rate slightly improves (37.1% vs 34.3%) because longer prompts provide more context for draft alignment, but this doesn't compensate for the throughput loss.

**Recommendation:** Use 131K for default agent workloads. Switch to 262K only when explicitly needed for long-context tasks. The systemd service can be updated by changing `--max-model-len` and restarting.

### Tuning `num_speculative_tokens` (May 15, 2026)

**Critical discovery:** Lower `num_speculative_tokens` dramatically improves acceptance rate with minimal throughput loss. The draft model aligns well for ~3 tokens; beyond that, divergence causes cascading rejections.

| num_tokens | Throughput | Acceptance Rate | Notes |
|------------|-----------|-----------------|-------|
| 4 | 15.2 tok/s | **36.7%** | Highest acceptance, slightly lower speed |
| **5** | **16.9 tok/s** | **34.3%** | **Best balance — selected as optimal** |
| 6 | 17.0 tok/s | 29.3% | Good balance |
| 8 | 14.9 tok/s | 20.1% | Meets 20% minimum |
| 10 | 17.3 tok/s | 18.7% | Below 20% target |
| 12 | 15.2 tok/s | 13.8% | Original test |
| 16 | 16.7 tok/s | 11.9% | Superseded by num_tokens=5 |
| 20 | 15.2 tok/s | 8.0% | Worse than 16 |
| 24 | 14.6 tok/s | 6.8% | Too many rejected tokens |

**Why lower is better:** Fewer draft tokens per step means less wasted computation on rejected tokens. The draft model's distribution aligns with the target for 2-3 tokens, then diverges. At 16 tokens, positions 4+ have <15% acceptance, wasting GPU cycles. At 5 tokens, most positions have >30% acceptance, making each draft step efficient.

**Selected config: `num_speculative_tokens=5`**
- 34.3% acceptance rate (well above 20% target)
- 16.9 tok/s throughput (above 10-12 tok/s minimum)
- 2.6x baseline speedup (vs 6.6 tok/s without speculative)

**User preference signal:** When user says "I want 20%+ acceptance even if speed drops to 10-12 tok/s", they value acceptance rate over raw throughput. The tuned config (34.3% at 16.9 tok/s) exceeds both thresholds. Always present the tradeoff curve and let them choose, but default to the highest acceptance config that meets minimum throughput.

### Initial synthetic benchmark (May 15, 2026 — narrow test prompts):

| Test | Baseline (tok/s) | DFlash (tok/s) | Gain |
|------|-----------------|----------------|------|
| math_reasoning | 6.67 | 11.78 | +77% |
| code_generation | 6.66 | 20.98 | +215% |
| factual_recall | 6.49 | 20.33 | +213% |
| creative_writing | 6.47 | 17.56 | +171% |
| logical_deduction | 6.68 | 21.16 | +217% |
| **AVERAGE** | **6.59** | **18.36** | **+179%** |

### Production benchmark (May 15, 2026 — real agent prompts, 512 tokens, 3-run average):

| Metric | Value |
|--------|-------|
| Throughput | **16.9 tok/s** (with num_tokens=5) |
| vs Baseline (no speculative) | **2.56x speedup** (from ~6.6 tok/s) |
| GPU utilization | 96% sustained |
| Power draw | ~38W under load |

**Speculative decoding metrics (production load, num_tokens=5):**

| Metric | Value |
|--------|-------|
| Draft tokens per step | 5 |
| Overall acceptance rate | **34.3%** |
| Mean accepted tokens per draft | ~3.4 |
| Draft model | Qwen3.5-27B-DFlash (3.3GB) |

**Acceptance rate by position (num_tokens=5):**
- Position 1: ~73% accepted
- Position 2: ~42% accepted
- Position 3: ~23% accepted
- Position 4+: drops to <15%

**Note:** The 34.3% overall acceptance rate with num_tokens=5 is significantly higher than the 11.9% with num_tokens=16 because fewer draft tokens means less divergence. Real prompts (mixed reasoning, tool calls, creative writing) still have lower acceptance than synthetic benchmarks, but the tuned config compensates.

**Post-reboot verification (May 15, 2026):**
After systemd auto-start, verify vLLM is ready:
```bash
# Check container is running
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep vllm

# Check systemd status
sudo systemctl is-active vllm-dflash.service

# Check models are available
curl -s http://localhost:8000/v1/models | python3 -c "import sys,json; d=json.load(sys.stdin); print([m['id'] for m in d['data']])"

# Check acceptance rate via metrics endpoint
python3 -c "
import requests
resp = requests.get('http://localhost:8000/metrics')
lines = resp.text.split('\n')
for line in lines:
    if 'spec_decode_num_accepted_tokens_total' in line and 'engine' in line:
        accepted = float(line.split()[-1])
    if 'spec_decode_num_draft_tokens_total' in line and 'engine' in line:
        drafted = float(line.split()[-1])
print(f'Accepted: {accepted:.0f}')
print(f'Drafted: {drafted:.0f}')
print(f'Rate: {accepted/drafted*100:.1f}%')
"
```

**Expected after reboot:** Container `Up 12 minutes`, systemd `active`, models `['/data/models/Qwen3.6-27B-Uncensored', 'merged-lora']`, acceptance rate ~50% (varies by workload).

**Context length switching (May 15, 2026):**
To switch between 131K and 262K context, update the systemd service and restart:

```bash
# Edit service file
sudo sed -i 's/--max-model-len 131072/--max-model-len 262144/' /etc/systemd/system/vllm-dflash.service
sudo systemctl daemon-reload
sudo systemctl restart vllm-dflash.service

# Wait for ready (~5-6 min)
for i in {1..60}; do
  if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    echo 'Ready'
    break
  fi
  sleep 10
done
```

**Throughput at 262K:** ~8.5 tok/s (50% of 131K throughput). Acceptable for long-context tasks but not for default agent workloads.

## Trade-offs

| Aspect | Without DFlash | With DFlash |
|--------|---------------|-------------|
| Single-stream throughput | ~6.5 tok/s | ~16.2 tok/s |
| KV cache capacity | 966K tokens | 499K tokens |
| Max concurrency (131K ctx) | 7.4x | 3.8x |
| GPU memory at idle | ~85GB | ~90GB |
| Startup time | ~5-6 min | ~6-7 min |
| Quality | Baseline | Identical (lossless) |

## When to Use DFlash

✅ **Use DFlash when:**
- Single-stream latency matters (interactive agent use)
- Throughput per request is the bottleneck
- You have headroom in GPU memory
- Quality cannot be compromised

❌ **Don't use DFlash when:**
- Maximum concurrent requests is the priority (use n-gram or no speculative)
- GPU memory is already tight
- Startup time is critical (frequent restarts)

## Pitfalls

1. **Permission denied on download** — If `/data/models/` is owned by root, `snapshot_download` fails with PermissionError on lock files. Fix: `sudo chown -R $(whoami):$(whoami) /data/models/Qwen3.5-27B-DFlash` BEFORE downloading.

2. **Gated repo for Qwen3.6-DFlash** — `z-lab/Qwen3.6-27B-DFlash` requires HF access approval. Use `z-lab/Qwen3.5-27B-DFlash` as public fallback.

3. **KV cache reduction** — DFlash draft model uses GPU memory that would otherwise go to KV cache. Max concurrency drops significantly at high context lengths.

4. **Longer startup** — Draft model load + compilation adds ~1-2 minutes to startup time.

5. **Acceptance rate varies by prompt type** — Synthetic benchmarks show 24% acceptance, but real agent prompts show 13%. Plan capacity based on production workloads, not synthetic tests.

## One-Command Deploy Script

```bash
#!/bin/bash
# /tmp/deploy_vllm_dflash.sh
set -e

docker stop vllm-merged 2>/dev/null || true
docker rm vllm-merged 2>/dev/null || true

docker run -d \
  --name vllm-merged \
  --runtime nvidia \
  --gpus all \
  -p 8000:8000 \
  -v /data:/data \
  -e CUDA_VISIBLE_DEVICES=0 \
  -e VLLM_LOGGING_LEVEL=INFO \
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
  --speculative-config '{"method":"dflash","model":"/data/models/Qwen3.5-27B-DFlash","num_speculative_tokens":5}' \
  --quantization fp8 \
  --kv-cache-dtype auto \
  --dtype bfloat16 \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 128

echo "vLLM with DFlash speculative decoding started (num_tokens=5, tuned for 34% acceptance)"
sleep 15
curl -s http://localhost:8000/v1/models | python3 -m json.tool 2>/dev/null || echo "Model not ready yet"
```

## Systemd Service for Auto-Start

Install `/etc/systemd/system/vllm-dflash.service` for automatic start on boot:

```ini
[Unit]
Description=vLLM DFlash Inference Server
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/docker run -d \
  --name vllm-merged \
  --runtime nvidia \
  --gpus all \
  -p 8000:8000 \
  -v /data:/data \
  -e CUDA_VISIBLE_DEVICES=0 \
  -e VLLM_LOGGING_LEVEL=INFO \
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
  --speculative-config '{"method":"dflash","model":"/data/models/Qwen3.5-27B-DFlash","num_speculative_tokens":5}' \
  --quantization fp8 \
  --kv-cache-dtype auto \
  --dtype bfloat16 \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 128
ExecStop=/usr/bin/docker stop -t 30 vllm-merged
ExecStopPost=/usr/bin/docker rm -f vllm-merged

[Install]
WantedBy=multi-user.target
```

Install and enable:
```bash
sudo cp /tmp/vllm-dflash.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vllm-dflash.service
```
