# DGX Training Double-Launch Incident — May 8, 2026

## Incident Summary

Training crashed at step 700 (OOM/stuck). DGX cycled. Auto-resume script triggered on boot, but launched **2 duplicate training processes** competing for the same GPU. Both processes at 101% CPU, 12–13GB RAM each. DGX became unresponsive again. Required second physical cycle and manual single-process launch.

## Timeline

- `23:40` — step 700, GPU 92%, 95.2GB (normal)
- `23:45` — step 700, GPU 91%, 95.7GB (normal)
- `23:50` — **STUCK_NO_CKPT: kill_resume triggered** (step 700, idle 31min). Monitor tried to kill and resume.
- `23:55` — SSH connection failed (EXIT=255). DGX became unresponsive.
- `00:00+` — DGX fully dead, SSH timing out consistently
- **Cycle 1** — DGX rebooted, auto-resume script launched 2 processes (PIDs 45545, 45656)
- **Cycle 2** — DGX rebooted again, 0 python3 processes, clean state

## Root Cause

The auto-resume script (`/data/SpecForge/custom_dflash/resume_training.sh`) restarts training in background. When the system boots after a crash, something (systemd/cron/monitor) may also trigger the same script. Result: two independent launches of the same training command.

## Detection

```bash
# After any resume or reboot, ALWAYS check process count:
ps aux | grep train_lora_sae_teacher | grep -v grep | wc -l
# If > 1: kill all and relaunch manually

# Also check individual PIDs:
ps aux | grep train_lora_sae_teacher | grep -v grep
# Should show exactly 1 process
```

## Fix: Manual Single-Process Launch

```bash
# 1. Kill everything (surgical approach)
ssh djg6228@10.0.0.171 'pkill -9 -f "train_lora_sae_teacher"; sleep 2'

# 2. Verify clean
ssh djg6228@10.0.0.171 'ps aux | grep train_ | grep -v grep | wc -l'
# Expected: 0

# 3. Clear GPU
ssh djg6228@10.0.0.171 'python3 -c "import torch; torch.cuda.empty_cache()"'

# 4. Launch via script (not inline nohup — terminal tool blocks on &)
# Write launch script locally, scp to DGX, then execute:
cat > /tmp/launch_training.sh << 'EOF'
#!/bin/bash
set -e
cd /data/SpecForge/custom_dflash
pkill -9 -f "train_lora_sae_teacher" 2>/dev/null || true
sleep 2
python3 -c "import torch; torch.cuda.empty_cache()"
nohup python3 -u train_lora_sae_teacher_v1.py \
    --resume_from_checkpoint /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_700 \
    >> training.log 2>&1 &
PID=$!
echo "Launched PID: $PID"
echo $PID > /tmp/training.pid
sleep 2
ps -p $PID -o pid,stat,%cpu,rss,etime | tail -1
EOF

scp /tmp/launch_training.sh djg6228@10.0.0.171:/tmp/launch_training.sh
ssh djg6228@10.0.0.171 'bash /tmp/launch_training.sh'

# 5. Verify single process after 10s
sleep 10
ssh djg6228@10.0.0.171 'ps aux | grep train_lora_sae_teacher | grep -v grep | wc -l'
# Expected: 1
```

## Key Lesson

**Never trust auto-resume scripts after a system crash.** They may have been triggered by multiple mechanisms (systemd, cron, monitor, manual). Always verify process count before leaving the system.

## Prevention

Add to launch script:
```bash
# Prevent double-launch: check if already running
if [ -f /tmp/training.pid ]; then
    OLD_PID=$(cat /tmp/training.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "Training already running (PID $OLD_PID). Aborting."
        exit 1
    fi
fi
```

## Terminal Tool Limitation

The `terminal` tool blocks on shell background operators (`&`, `nohup ... &`). Cannot use inline backgrounding. Must write a script file, `scp` it, then execute via `ssh`.

Workaround pattern:
1. `write_file` locally → `/tmp/script.sh`
2. `terminal` with `scp` to transfer
3. `terminal` with `ssh` to execute (foreground, but script backgrounds internally)
4. `terminal` with `ssh` to poll status
