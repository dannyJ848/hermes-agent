# Process Duplication from Auto-Resume Scripts (May 8, 2026)

## Incident Summary

After DGX power cycle and clean bulletproof training launch, OLD `train_lora_sae_teacher_v1.py` processes appeared minutes later, consuming GPU memory and destabilizing the system.

## Timeline

- **10:33 UTC** — Launched bulletproof training (PID 45823) via `launch_bulletproof.sh`
- **10:36 UTC** — Check shows 1 process, weight loading at ~53%
- **10:40 UTC** — Check shows 2 OLD v1.py processes (PIDs 47542, 47561) running alongside bulletproof
- **10:40 UTC** — Auto-resume scripts `resume_training.sh` and `training_monitor.sh` discovered as root cause
- **10:41 UTC** — Killed all processes, deleted auto-resume scripts, relaunched clean

## Root Cause

`resume_training.sh` and `training_monitor.sh` from a previous session existed in `/data/SpecForge/custom_dflash/`. These scripts:
1. Were configured to run at intervals (cron or loop)
2. Launched `train_lora_sae_teacher_v1.py` (the OLD script, not bulletproof)
3. The bash parent scripts were not visible in initial `ps aux | grep train` checks
4. Their python3 children appeared later as "mystery" duplicates

## Detection Pattern

```bash
# Initial check (missed the problem — only checks for 'train' in command)
ps aux | grep train | grep -v grep | wc -l
# Returns: 1 (bulletproof only — looks clean)

# Correct check (catches python3 children of auto-resume scripts)
ps aux | grep python3 | grep -v grep | grep -v "bash -c"
# Returns: 2 (the duplicate v1.py processes)

# Root cause check (finds the auto-resume parents)
ps aux | grep -E "resume_training|training_monitor" | grep -v grep
# Returns: 2 (bash scripts that spawned the duplicates)
```

## Impact

| Metric | Single Process | With Duplicates |
|--------|---------------|-----------------|
| GPU Memory | ~60GB | ~90GB+ |
| CPU | 100% (1 core) | 196.4% (2 cores at ~98% each) |
| SSH Responsiveness | Normal | Sluggish/Unresponsive |
| System Stability | Stable | Freeze risk |

## Fix Applied

```bash
# Kill ALL training variants
pkill -9 -f "train_lora_sae_teacher"
pkill -9 -f "train_bulletproof"

# Kill auto-resume script parents
pkill -9 -f "resume_training"
pkill -9 -f "training_monitor"

# DELETE the scripts permanently
rm -f /data/SpecForge/custom_dflash/resume_training.sh \
      /data/SpecForge/custom_dflash/training_monitor.sh \
      /data/SpecForge/custom_dflash/monitor_config.json

# Clear GPU
python3 -c "import torch; torch.cuda.empty_cache()"

# Verify clean
ps aux | grep -E "train|python3.*train|resume_training|training_monitor" | grep -v grep | wc -l
# MUST return 0
```

## Prevention

All launch scripts must now include:
1. Kill of ALL training variants (v1, bulletproof, any future names)
2. Kill of auto-resume script parents
3. DELETE (not just kill) auto-resume scripts from disk
4. 3-second sleep (was 2, increased for safety)
5. GPU cache clear
6. Single instance launch with PID verification

## Key Insight

Auto-resume scripts are a HIDDEN duplication vector. They don't show up in standard process checks because:
- The bash parent uses minimal resources
- The python3 children appear minutes after launch
- The children use the OLD script name, not the new one
- Initial checks happen before the auto-resume triggers

**Rule:** Before ANY training launch, check for AND remove auto-resume scripts from disk. Killing processes is not enough — the scripts will respawn them.
