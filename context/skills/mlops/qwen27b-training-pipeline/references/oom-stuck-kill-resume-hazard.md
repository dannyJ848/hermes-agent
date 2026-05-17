# OOM/Stuck at Step 700 — Kill-Resume Hazard Pattern

**Date:** May 8, 2026  
**System:** DGX Spark (130GB GPU), Qwen 27B LoRA training, rank-256  
**Trigger:** Training stuck at step 700 for 31+ min, monitor auto-killed, system became unresponsive

## Timeline

| Time | Event |
|------|-------|
| 23:18 | Checkpoint step_700 written (5.1GB adapter + 2.6GB optimizer) |
| 23:40 | Monitor: OK, step 700, GPU 92%, 95.2GB |
| 23:45 | Monitor: OK, step 700, GPU 91%, 95.7GB |
| 23:50 | Monitor: STUCK_NO_CKPT — kill_resume triggered (idle 31min) |
| 23:55 | SSH connection failed (EXIT=255) |
| 00:00 | User power-cycled DGX |
| 00:03 | DGX back online, resumed from checkpoint_step_700 |

## Root Cause

Training at GPU memory edge (92-95GB / 130GB) with no checkpoint for 31+ minutes. The system had no headroom for:
1. Checkpoint I/O (spikes memory during save)
2. System processes (SSH daemon, cron, monitor)
3. Kill-resume script execution (needs GPU access to empty_cache)

When the monitor's `kill_resume` triggered:
- `pkill -9` sent SIGKILL to training process
- GPU memory freed abruptly
- But the system was already in a degraded state (memory pressure, I/O backlog)
- SSH daemon became unresponsive — not just slow, completely dead

## Why This Happens at Memory Edge

At 92%+ GPU utilization:
- **Checkpoint saves** allocate new tensors for state serialization → temporary spike to 98-100%
- **System swap** under memory pressure → disk thrashing
- **Network I/O** (SSH, monitor log writes) competes with GPU memory bus
- **Grace CPU** (20 cores) saturated handling GPU coordination + system tasks

## Prevention Pattern

### 1. More Frequent Checkpoints at High Memory
```python
# When GPU > 90%, checkpoint every 50 steps instead of 100
if gpu_memory_percent > 90:
    checkpoint_interval = 50
else:
    checkpoint_interval = 100
```

### 2. Proactive GPU Cache Management Before Saves
```python
# Before checkpoint save — clear cache and synchronize
if step % checkpoint_interval == 0:
    torch.cuda.synchronize()
    torch.cuda.empty_cache()
    # NOW save — with cleared cache
    save_checkpoint(...)
```

### 3. Treat Checkpoint Saves as Hazards
```python
# Monitor should watch for BOTH:
# - No checkpoint for N minutes (stuck detection)
# - GPU memory > 95% for M minutes (pre-OOM detection)
# Pre-OOM detection should trigger GRACEFUL stop, not SIGKILL

if gpu_memory > 95 and time_since_last_checkpoint > 10:
    # Graceful stop — allows current step to finish, then checkpoint
    send_signal(SIGTERM)  # not SIGKILL
    wait 30 seconds for checkpoint
    if still no checkpoint: then SIGKILL
```

### 4. Monitor Should Empty Cache Before Kill
```bash
# In kill_resume script, BEFORE pkill:
python3 -c "import torch; torch.cuda.empty_cache(); torch.cuda.synchronize()"
sleep 2
# THEN kill
pkill -9 -f "train_lora_sae_teacher"
```

### 5. SSH Daemon Priority
```bash
# On DGX, ensure SSH daemon has CPU priority
sudo nice -n -10 systemctl restart sshd
# Or use systemd resource limits to reserve CPU for sshd
```

## Recovery Pattern

When DGX is unresponsive after kill:
1. **Wait 2-5 min** — may be temporary I/O backlog clearing
2. **Check ping** — `ping 10.0.0.171` to verify network layer alive
3. **If ping works but SSH dead** — system processes degraded, needs power cycle
4. **If ping dead** — full system hang, definitely needs power cycle
5. **After power cycle** — verify checkpoint integrity before resume

## Checkpoint Validation Post-Crash

```bash
# After any crash/resume, validate checkpoint before using
python3 -c "
import torch
ckpt = torch.load('/data/SpecForge/custom_dflash/checkpoints/checkpoint_step_700/adapter_model.bin', map_location='cpu')
print('Keys:', list(ckpt.keys())[:5])
for k in list(ckpt.keys())[:3]:
    print(f'{k}: shape={ckpt[k].shape}, dtype={ckpt[k].dtype}')
print('Checkpoint valid')
"
```

## Key Lesson

**At GPU memory edge, the monitor's kill-resume script itself becomes a hazard.** The very tool designed to save the training run can destabilize the system. Mitigation: proactive cache clearing, graceful stops, frequent checkpoints, and treating checkpoint I/O as a memory spike event.
