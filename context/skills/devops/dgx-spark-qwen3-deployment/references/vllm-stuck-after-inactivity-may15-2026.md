# vLLM Container Stuck-After-Inactivity on DGX Spark

**Date:** May 15, 2026
**Affected:** vLLM containers running Qwen3.6-27B on DGX Spark (GB10)
**Symptom:** Container appears running (docker ps shows Up) but stops processing requests

## Symptoms

1. Container status shows `Up` but requests timeout
2. GPU utilization drops to 0%
3. No new log output (docker logs shows last entry from hours ago)
4. curl to /v1/models hangs indefinitely
5. Affects containers idle for 4+ hours

## Verification

```bash
# Quick health check
curl -s --max-time 5 http://localhost:8000/v1/models
# If this hangs or times out, vLLM is stuck

# Check GPU utilization
nvidia-smi
# If GPU util is 0% but container is "Up", it's stuck

# Check last log entry
docker logs --tail 5 vllm-merged
# If last entry is >1 hour old, stuck confirmed
```

## Fix

```bash
# Immediate fix: restart container
docker restart vllm-merged

# Wait for ready
for i in {1..60}; do
  if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    echo "Ready"
    break
  fi
  sleep 10
done
```

## Prevention

Add health check and auto-restart to systemd service:

```ini
# /etc/systemd/system/vllm-dflash.service
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
  --health-cmd="curl -f http://localhost:8000/v1/models || exit 1" \
  --health-interval=60s \
  --health-timeout=10s \
  --health-retries=3 \
  --health-start-period=300s \
  vllm/vllm-openai:latest \
  [vLLM args...]
ExecStop=/usr/bin/docker stop -t 30 vllm-merged
ExecStopPost=/usr/bin/docker rm -f vllm-merged

[Install]
WantedBy=multi-user.target
```

**Note:** Docker health checks require the container to have `curl` installed. The `vllm/vllm-openai:latest` image includes curl. If using a custom image, verify curl is available.

## Monitoring Script

```bash
#!/bin/bash
# /usr/local/bin/vllm-health-check.sh
# Run via cron every 5 minutes

CONTAINER="vllm-merged"
TIMEOUT=10

if ! curl -s --max-time $TIMEOUT http://localhost:8000/v1/models > /dev/null 2>&1; then
  echo "$(date): vLLM not responding, restarting..." >> /var/log/vllm-health.log
  docker restart $CONTAINER
fi
```

## Root Cause (Hypothesis)

The stuck state appears to be a kernel-level stall or deadlock in the CUDA driver or vLLM's scheduler. Possible causes:
- CUDA context timeout after extended idle period
- Memory leak in vLLM's scheduler or KV cache manager
- Docker container losing GPU context

**Not yet root-caused.** The restart fix is reliable but the underlying cause needs investigation.

## Related

- vLLM issue: May be related to https://github.com/vllm-project/vllm/issues/ (search for "hang" + "idle")
- DGX Spark specific: May be related to GB10's unified memory architecture and power management
