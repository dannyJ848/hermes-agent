# Process Duplication OOM — May 8, 2026

## Incident
Training crashed at step 700. No explicit errors in logs. DGX became unresponsive under load.

## Diagnosis
- `ps aux` showed 2 training processes (PIDs 7779 and 7808) after DGX cycle
- Both loading weights simultaneously from same checkpoint
- GPU memory would have compounded: ~50GB × 2 = ~100GB+ before SAE/optimizer overhead
- System froze, SSH timed out during banner exchange

## Root Cause
Launch mechanism did not kill existing processes before starting new ones. When:
1. Training was already running (PID 61724 from previous launch)
2. User cycled DGX (power cycle)
3. On reboot, something auto-launched or previous nohup process resumed
4. Manual launch script ran without checking for existing processes
5. Result: 2+ instances competing for GPU memory

## Why Silent (No Logs)
- Linux OOM killer sends SIGKILL (signal 9)
- SIGKILL cannot be caught or logged by the process
- Process dies instantly, log ends mid-line
- No stack trace, no error message
- Only evidence: `dmesg | grep -i 'killed process'` (requires root)

## Memory Math
| Component | 1 Process | 2 Processes |
|-----------|----------|-------------|
| Base model (bf16) | ~50GB | ~100GB |
| LoRA weights | ~0.2GB | ~0.4GB |
| Optimizer states | ~0.8GB | ~1.6GB |
| Activations | ~6GB | ~12GB |
| SAE overhead | ~2GB | ~4GB |
| **Total** | **~59GB** | **~118GB** |
| Headroom on 130GB | 71GB | 12GB |
| Result | Stable | OOM → freeze |

## Fix Applied (v1: pkill)
`/tmp/launch_training.sh` now includes:
```bash
pkill -9 -f "train_lora_sae_teacher" 2>/dev/null || true
sleep 2
python3 -c "import torch; torch.cuda.empty_cache()"
```

This is NOT sufficient. Race condition: if launch script runs twice rapidly (cron + manual), both pass pkill before either starts new process. Result: duplicates anyway.

## Fix v2: Atomic PID File with flock (May 8, 2026)

**Robust fix: advisory file locking + PID tracking**
```bash
#!/bin/bash
set -e

PIDFILE="/tmp/training.pid"
LOCKFILE="/tmp/training.lock"

# Atomic lock: only one launcher proceeds
echo "Acquiring lock..."
(
    flock -n 200 || { echo "Another launcher is running. Exiting."; exit 1; }
    
    # Kill existing training
    if [ -f "$PIDFILE" ]; then
        OLD_PID=$(cat "$PIDFILE" 2>/dev/null)
        if kill -0 "$OLD_PID" 2>/dev/null; then
            echo "Killing existing training PID $OLD_PID"
            kill -9 "$OLD_PID" 2>/dev/null || true
            sleep 3
        fi
    fi
    pkill -9 -f "train_lora_sae_teacher" 2>/dev/null || true
    sleep 2
    
    # Clear GPU
    python3 -c "import torch; torch.cuda.empty_cache()"
    
    # Launch
    cd /data/SpecForge/custom_dflash
    nice -n 10 nohup python3 -u train_lora_sae_teacher_v1.py \
        --resume_from_checkpoint /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_700 \
        >> training.log 2>&1 &
    
    PID=$!
    echo "$PID" > "$PIDFILE"
    echo "Launched PID: $PID"
    sleep 2
    ps -p "$PID" -o pid,stat,%cpu,rss,etime | tail -1
    
) 200>"$LOCKFILE"
```

**Why this works:**
- `flock -n 200` — non-blocking lock. If another process holds it, exits immediately.
- PID file tracks actual training process
- Even if two launchers fire simultaneously, only one acquires lock
- Second launcher sees "Another launcher is running" and exits

**Verification:**
```bash
# Test race: run two simultaneously
ssh djg6228@10.0.0.171 'bash /tmp/launch_training.sh' &
ssh djg6228@10.0.0.171 'bash /tmp/launch_training.sh' &
wait
# Expected: one "Launched PID: XXXX", one "Another launcher is running"
```

## Detection Pattern
```bash
# After any launch or DGX recovery, ALWAYS verify process count
ssh djg6228@10.0.0.171 'ps aux | grep train_lora_sae_teacher | grep -v grep | wc -l'
# Expected: 1
# If >1: pkill -9 -f "train_lora_sae_teacher", wait, relaunch
```

## Prevention Checklist
- [ ] Before launching: check process count
- [ ] Before launching: clear GPU cache
- [ ] After launching: verify single PID
- [ ] After DGX cycle: check for auto-resumed processes
- [ ] In launch script: unconditional kill + sleep + verify

## Related
- `templates/launch_training.sh` — known-good launch script
- `references/oom-stuck-kill-resume-hazard.md` — monitor kill-resume hazard
- `references/ssh-timeout-under-training-load-may8-2026.md` — SSH behavior under load
