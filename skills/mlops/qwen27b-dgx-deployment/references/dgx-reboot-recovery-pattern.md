# DGX Spark Reboot and Service Recovery Pattern

## Problem

DGX Spark becomes unreachable via SSH (times out during banner exchange). This can happen due to:
- Extended training load causing thermal throttling
- vLLM container stuck after inactivity
- System resource exhaustion
- Network stack issues

## Recovery Steps

### 1. Physical Reboot

When SSH is completely unresponsive:
1. **Power cycle the DGX** — disconnect USB-C power, wait 10 seconds, reconnect
2. **Wait for boot** — ~2-3 minutes for Ubuntu to come up
3. **Verify SSH access** — `ssh djg6228@spark-85e8.local` or `ssh djg6228@10.0.0.171`

### 2. Service Status Check

After reboot, verify all services:

```bash
# Check vLLM container
sudo systemctl status vllm-dflash.service
docker ps | grep vllm-merged

# Check Hermes gateway
sudo systemctl status hermes-dgx-gateway.service

# Check Qdrant (vector DB)
docker ps | grep qdrant || docker start qdrant

# Check distillation daemon
ps aux | grep dgx_distillation_daemon
```

### 3. vLLM Recovery

If vLLM container is stuck (running but not processing):

```bash
# Quick restart
docker restart vllm-merged

# Or full cycle
docker stop -t 30 vllm-merged
docker rm vllm-merged
sudo systemctl restart vllm-dflash.service
```

**Startup timeline after reboot:**
1. Container start: instant
2. Model shard loading: ~3 min (15 shards × ~12s each)
3. torch.compile: ~66s (cached on subsequent boots)
4. CUDA graph capture: ~74s (~128 graphs)
5. **Total to ready: ~5-7 minutes**

### 4. Hermes Gateway Recovery

If gateway needs restart:

```bash
sudo systemctl restart hermes-dgx-gateway.service
sleep 3
systemctl is-active hermes-dgx-gateway.service
```

**Note:** Gateway logs go to systemd journal. Check with:
```bash
journalctl -u hermes-dgx-gateway.service --no-pager -n 50
```

### 5. Cognitive Orchestrator Verification

After any restart, verify all 20 subsystems:

```bash
export HERMES_CONFIG=/data/SpecForge/hermes-agent/config.yaml
cd /data/SpecForge/hermes-agent
source venv/bin/activate

python3 << "PYEOF"
import sys
sys.path.insert(0, ".")
from run_agent import AIAgent
agent = AIAgent()
PYEOF
```

Expected output:
```
🧠 Cognitive orchestrator ready: 19/20 subsystems active
   ✓ tiered_memory
   ✓ error_learning
   ✓ skill_tracker
   ✓ brain
   ✗ cortex_flywheel          (DB schema: cortex_nodes table missing)
   ✓ distillation_bridge
   ✓ self_audit
   ✓ training_gym
   ✓ memory_bridge
   ✓ subconscious
   ✓ autobrowse_tracer
   ✓ context_sculptor
   ✓ tool_oracle
   ✓ trust_scorer
   ✓ unified_intelligence
   ✓ failure_prevention
   ✓ experimentation
   ✓ domain_transfer
   ✓ attention_prioritizer
   ✓ evaluation_gate
```

### 6. Health Check Automation

Install the health check script to auto-detect stuck containers:

```bash
# Copy from skill
sudo cp ~/.hermes/skills/mlops/qwen27b-dgx-deployment/scripts/vllm-health-check.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/vllm-health-check.sh

# Add to crontab (every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/vllm-health-check.sh") | crontab -
```

## Known Issues

### vLLM Container Stuck After Inactivity

**Symptoms:**
- Container shows as `Up` in `docker ps`
- curl to localhost:8000 times out
- GPU utilization at 0%
- No new log entries for 30+ minutes

**Fix:** `docker restart vllm-merged` (takes ~5-7 min to recover)

**Prevention:** Health check script auto-restarts stuck containers

### SSH Banner Exchange Timeout

**Symptoms:**
- `ssh` hangs at "Connection established" before password prompt
- No response to keyboard input
- Must Ctrl-C to abort

**Fix:** Power cycle DGX (disconnect/reconnect USB-C)

**Prevention:** Monitor system load, avoid running training + inference simultaneously

### Qdrant Not Auto-Starting

**Symptoms:**
- `docker ps` doesn't show qdrant container
- Hermes knowledge search fails

**Fix:** `docker start qdrant`

**Prevention:** Add Qdrant to systemd or docker-compose auto-start

## Verification Commands

```bash
# Full system health check
ssh djg6228@spark-85e8.local '
  echo "=== vLLM ===" && docker ps | grep vllm && curl -s http://localhost:8000/v1/models | head -1
  echo "=== Gateway ===" && systemctl is-active hermes-dgx-gateway.service
  echo "=== Qdrant ===" && docker ps | grep qdrant || echo "Qdrant not running"
  echo "=== GPU ===" && nvidia-smi --query-gpu=name,utilization.gpu,temperature.gpu --format=csv,noheader
  echo "=== Disk ===" && df -h /data | tail -1
'
```
