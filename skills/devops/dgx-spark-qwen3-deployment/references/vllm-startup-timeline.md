# vLLM Startup Timeline and Timing (Qwen3.6-27B on DGX Spark)

## Startup Phases

When launching vLLM with Qwen3.6-27B, the container goes through distinct phases before it's ready to serve requests:

| Phase | Duration | Description | Log Indicator |
|-------|----------|-------------|---------------|
| Container start | Instant | Docker container creation | `docker run -d` returns immediately |
| Model shard loading | ~3 minutes | Loading 15 model shards sequentially | `Loading model weights took ...` |
| Drafter model load | Instant (n-gram) or ~2 min (DFlash) | Loading speculative decoding draft | `Loading draft model...` (DFlash only) |
| torch.compile | ~66 seconds | JIT compilation of model graph | `torch.compile` messages |
| CUDA graph capture | ~74 seconds | Capturing CUDA graphs for inference | `Capturing CUDA graph` |
| **Total to ready** | **~5-6 minutes** | First request can be served | `Engine 000: Avg prompt throughput` |

## First Boot vs Subsequent Boots

| Boot Type | torch.compile | CUDA graphs | Total Time |
|-----------|-------------|-------------|------------|
| First boot (cold) | ~66s (no cache) | ~74s (no cache) | ~5-6 min |
| Subsequent boot | ~5-10s (cached) | ~10-15s (cached) | ~3-4 min |

The torch.compile cache and CUDA graph cache persist across container restarts if the model path and config are identical.

## Verification Commands

### Check if vLLM is ready
```bash
# Method 1: Check logs for throughput messages
docker logs vllm-merged 2>&1 | grep "Avg prompt throughput"
# Should show: "Engine 000: Avg prompt throughput: X tokens/s"

# Method 2: Check if port is responding
curl -s http://localhost:8000/v1/models | head -1
# Should return: {"object":"list","data":[...]}

# Method 3: Check GPU utilization
nvidia-smi | grep "vllm"
# Should show vllm process with GPU memory allocated
```

### Check startup progress
```bash
# Watch logs in real-time
docker logs -f vllm-merged 2>&1 | grep -E "Loading|compile|CUDA|Engine"

# Expected sequence:
# 1. "Loading model weights took X seconds"
# 2. "torch.compile: ..." (first boot only)
# 3. "Capturing CUDA graph" (first boot only)
# 4. "Engine 000: Avg prompt throughput: X tokens/s"
```

## Common Timing Issues

### Issue: Startup takes >10 minutes
**Possible causes:**
- Model files are on slow storage (HDD instead of NVMe)
- Docker image not cached (first pull)
- torch.compile cache invalidated (model config changed)
- GPU memory fragmentation from previous runs

**Fix:**
```bash
# Clear GPU memory and restart
docker rm -f vllm-merged
nvidia-smi | grep -v "NVIDIA-SMI" | awk '{print $5}' | xargs -I {} kill -9 {} 2>/dev/null
# Wait 10 seconds for GPU memory cleanup
sleep 10
docker run -d ... (relaunch)
```

### Issue: vLLM appears running but doesn't respond to requests
**Symptom:** `docker ps` shows container running, but `curl` times out
**Cause:** Container is still in startup phase (model loading, torch.compile)
**Fix:** Wait 5-6 minutes for full startup. Check logs for progress.

### Issue: vLLM stops responding after hours of inactivity
**Symptom:** Container running, GPU util 0%, no new logs, requests timeout
**Cause:** Known vLLM issue after 4+ hours idle on some configurations
**Fix:** Restart container: `docker restart vllm-merged`
**Prevention:** Set up health check script (see `references/vllm-stuck-after-inactivity-may15-2026.md`)

## Health Check Script

Save as `/usr/local/bin/vllm-health-check.sh`:

```bash
#!/bin/bash
# vLLM health check — restart if stuck

HEALTH_URL="http://localhost:8000/v1/models"
LOG_FILE="/var/log/vllm-health.log"

# Check if vLLM responds
if ! curl -s --max-time 10 "$HEALTH_URL" > /dev/null 2>&1; then
    echo "$(date): vLLM not responding, restarting..." >> "$LOG_FILE"
    docker restart vllm-merged
    echo "$(date): Restarted vLLM" >> "$LOG_FILE"
else
    echo "$(date): vLLM healthy" >> "$LOG_FILE"
fi
```

Add to crontab (check every 5 minutes):
```bash
*/5 * * * * /usr/local/bin/vllm-health-check.sh
```

## Performance After Startup

Once vLLM is ready, performance metrics are available in logs:

```bash
# Check throughput
docker logs vllm-merged 2>&1 | grep "Avg generation throughput" | tail -5

# Check speculative decoding metrics
docker logs vllm-merged 2>&1 | grep "SpecDecoding metrics" | tail -5

# Check KV cache usage
docker logs vllm-merged 2>&1 | grep "GPU KV cache usage" | tail -5
```

## systemd Service for Auto-Start

```ini
[Unit]
Description=vLLM Inference Server
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
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --enable-lora \
  --lora-modules merged-lora=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --max-lora-rank 256 \
  --max-model-len 131072 \
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

Install:
```bash
sudo cp /tmp/vllm.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vllm.service
sudo systemctl start vllm.service
```

## Key Takeaways

1. **First boot takes 5-6 minutes** — don't panic if requests fail immediately
2. **Subsequent boots are faster** (~3-4 min) due to cached compilation
3. **Check logs for "Engine 000" message** — that's the "ready" signal
4. **Health check scripts prevent silent failures** after long idle periods
5. **systemd service ensures auto-start on boot** with proper cleanup
