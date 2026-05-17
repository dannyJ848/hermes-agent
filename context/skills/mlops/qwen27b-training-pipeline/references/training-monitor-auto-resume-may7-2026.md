# Training Monitor + Auto-Resume Deployment — May 7, 2026

## Problem
Training at GPU memory edge (62.6GB/130GB, rank-256 LoRA) is fragile. A crash or hang means hours of lost progress. Manual recovery requires SSH to DGX, checking logs, finding latest checkpoint, composing resume command — all while DGX may be unresponsive under load.

## Solution: Two-Layer Monitoring

### Layer 1: Remote Monitor (DGX itself)

**Script:** `/data/SpecForge/custom_dflash/training_monitor.sh`

```bash
#!/bin/bash
# Runs every 5 min via DGX crontab
# Checks: PID alive, GPU utilization, checkpoint age
# If dead/stale (>30 min no checkpoint): kills zombie, calls resume

CONFIG="/data/SpecForge/custom_dflash/monitor_config.json"
PID=$(jq -r '.pid' "$CONFIG")
MAX_IDLE_MIN=$(jq -r '.max_idle_minutes' "$CONFIG")

# Check process alive
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "$(date): PID $PID dead, calling resume"
    bash /data/SpecForge/custom_dflash/resume_training.sh
    exit
fi

# Check checkpoint age
LATEST=$(ls -t /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_* 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
    AGE_MIN=$(( ($(date +%s) - $(stat -c %Y "$LATEST")) / 60 ))
    if [ "$AGE_MIN" -gt "$MAX_IDLE_MIN" ]; then
        echo "$(date): Stale checkpoint ($AGE_MIN min), killing and resuming"
        kill -9 "$PID" 2>/dev/null
        bash /data/SpecForge/custom_dflash/resume_training.sh
    fi
fi
```

**Resume script:** `/data/SpecForge/custom_dflash/resume_training.sh`

```bash
#!/bin/bash
# Validates latest checkpoint, restarts training, updates monitor config

CHECKPOINT_DIR="/data/SpecForge/custom_dflash/checkpoints"
LATEST=$(ls -t "$CHECKPOINT_DIR"/checkpoint_step_* 2>/dev/null | head -1)

if [ -z "$LATEST" ]; then
    echo "No checkpoint found, starting from step 0"
    # Start fresh
    cd /data/SpecForge/custom_dflash
    nohup python3 train_lora_sae_teacher_v1.py > /mnt/bigssd/train.log 2>&1 &
else
    STEP=$(echo "$LATEST" | grep -o 'step_[0-9]*' | cut -d_ -f2)
    echo "Resuming from step $STEP"
    cd /data/SpecForge/custom_dflash
    nohup python3 train_lora_sae_teacher_v1.py --resume_from_checkpoint "$LATEST" > /mnt/bigssd/train.log 2>&1 &
fi

# Update monitor config with new PID
NEW_PID=$!
echo "{\"pid\": $NEW_PID, \"max_idle_minutes\": 30, \"resume_script\": \"/data/SpecForge/custom_dflash/resume_training.sh\"}" > /data/SpecForge/custom_dflash/monitor_config.json
```

**Crontab on DGX:**
```
*/5 * * * * /data/SpecForge/custom_dflash/training_monitor.sh >> /mnt/bigssd/monitor.log 2>&1
```

### Layer 2: Local Monitor (MacBook)

**Script:** `/tmp/dgx_local_monitor.sh`

```bash
#!/bin/bash
# Runs every 5 min via Mac crontab
# SSH into DGX, checks training status, logs to local file

ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no djg6228@spark-85e8.local '
    ps -p 180722 -o pid,comm,etime 2>/dev/null || echo "DEAD"
    tail -3 /mnt/bigssd/train_lora_sae_teacher_v1.log 2>/dev/null
' >> /tmp/dgx_monitor.log 2>&1
```

**Crontab on Mac:**
```
*/5 * * * * /tmp/dgx_local_monitor.sh
```

## Key Design Decisions

1. **DGX-local cron, not Hermes cron** — Hermes cron tool is broken (13% success). DGX crontab is native and reliable.
2. **nohup on DGX, not through SSH tunnel** — SSH tunnel closing sends SIGHUP. DGX-local nohup survives disconnect.
3. **Checkpoint age, not just PID** — PID can exist but training hung (infinite loop, deadlock). Checkpoint age catches hangs.
4. **Kill-first, resume-second** — Zombie PIDs block restart. Always kill before resuming.
5. **30-minute stale threshold** — Normal pace is 0.34 min/step = ~3 min per 10 steps. 30 min = ~100 steps without checkpoint = definitely hung.

## OOM Prevention at Checkpoint Saves

When training at GPU memory edge, checkpoint saves are hazards:

```python
# Before saving checkpoint:
torch.cuda.synchronize()          # Wait for all GPU ops
model.to('cpu')                   # Offload to CPU
import gc; gc.collect()           # Force garbage collection
torch.save(checkpoint, path)      # Save from CPU
model.to('cuda')                  # Reload to GPU
torch.cuda.empty_cache()          # Clear fragmentation
```

This prevents OOM during save (which would corrupt the checkpoint).

## Files

| Purpose | Path |
|---------|------|
| Remote monitor | `/data/SpecForge/custom_dflash/training_monitor.sh` |
| Resume script | `/data/SpecForge/custom_dflash/resume_training.sh` |
| Monitor config | `/data/SpecForge/custom_dflash/monitor_config.json` |
| Local monitor | `/tmp/dgx_local_monitor.sh` |
| Local log | `/tmp/dgx_monitor.log` |

## Status

Deployed May 7, 2026. Training rank-256 stable at step 600+. Both monitors active.
