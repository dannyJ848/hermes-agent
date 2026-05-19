# Training Status Check — DGX Spark

## Quick Status (punchy format, user's preferred style)

```
step 4615/10000, loss 1.4138, 30h left. pid 443609, 17h elapsed. gpu 62.6GB.
```

## Full Workflow

### 1. Discover SSH target (PITFALL: don't guess hostname)

```bash
# Check ~/.ssh/config for Includes
cat ~/.ssh/config
# May include: /Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/ssh_config

# Actual host: spark-85e8.local
# Actual user: djg6228
# Key: /Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key
```

### 2. Verify process running

```bash
ssh spark-85e8.local 'ps aux | grep -E "(train|python)" | grep -v grep'
```

### 3. Find log file (dynamic path — check /proc/PID/fd/)

```bash
ssh spark-85e8.local 'ls -la /proc/443609/fd | grep log'
# Typical output: /mnt/bigssd/train_r256_final.log
```

### 4. Parse latest step

```bash
ssh spark-85e8.local 'grep "Step [0-9]*/10000" /mnt/bigssd/train_r256_final.log | tail -1'
```

### 5. Calculate ETA

- Steps remaining: 10000 - current_step
- Seconds per step: ~20s (from log timestamps)
- ETA hours: (remaining * 20) / 3600

## Log Format Reference

```
Step 4610/10000 | Loss: 1.4138 (CE:1.236 D:1.208 SAE:0.558) | W:(0.77,0.34,0.10) | LR: 1.19e-04 | GPU: 62.6GB
```

Components:
- `CE`: Cross-entropy loss
- `D`: Distillation loss
- `SAE`: Sparse autoencoder loss
- `W`: Loss weights (CE, distillation, SAE)
- `LR`: Learning rate
- `GPU`: VRAM usage in GB

## Exact ETA Calculation (User Demands Precision)

**Pitfall:** Giving rough estimates like "~18 hours" triggers user correction. Calculate exactly from actual log timestamps.

```bash
# 1. Get two data points with timestamps
ssh spark-85e8.local 'grep -E "Step [0-9]+/[0-9]+" /mnt/bigssd/train_v2_max1000.log | tail -20 | head -1'
# → Step 9540/10000 @ 2026-05-10 14:36:56

ssh spark-85e8.local 'grep -E "Step [0-9]+/[0-9]+" /mnt/bigssd/train_v2_max1000.log | tail -1'
# → Step 9730/10000 @ 2026-05-10 15:40:36
```

**Calculation:**
- Elapsed: 63.7 minutes for 190 steps
- Seconds per step: 3820s / 190 = **20.1 sec/step**
- Remaining: 10000 - 9730 = 270 steps
- ETA: 270 × 20.1 = **5428 seconds = 90.5 minutes = 1.51 hours**

**Formula:**
```python
from datetime import datetime
start = datetime.strptime("2026-05-10 14:36:56", "%Y-%m-%d %H:%M:%S")
end = datetime.strptime("2026-05-10 15:40:36", "%Y-%m-%d %H:%M:%S")
elapsed_seconds = (end - start).total_seconds()
steps_done = 9730 - 9540  # 190
seconds_per_step = elapsed_seconds / steps_done
remaining_steps = 10000 - 9730  # 270
eta_seconds = remaining_steps * seconds_per_step
# eta_seconds = 5428 ≈ 90.5 minutes
```

**Report format:**
```
Step 9730/10000 (97.3%). ETA: 90.5 minutes (~17:11 UTC).
Rate: 20.1 sec/step. Loss: 0.8559.
```

## Stale Log with Active Process (Critical Pattern)

**Scenario:** Process shows in `ps aux` (PID 443609, 105% CPU, 95GB GPU) but log hasn't updated in days.

**Root cause:** Training script was restarted with a NEW log file. The old log is abandoned but the process name looks the same.

**Detection:**
```bash
# 1. List ALL log files by recency
ssh spark-85e8.local 'ls -lt /mnt/bigssd/*.log | head -10'
# → train_v2_max1000.log     (May 10 15:39 — ACTIVE)
# → train_r256_final.log     (May 10 15:39 — SAME PROCESS, duplicate)
# → train_lora_sae_teacher_v1.log (May 6 23:58 — STALE, abandoned)

# 2. Check which log the process is actually writing to
ssh spark-85e8.local 'ls -la /proc/443609/fd | grep log'
```

**Resolution:**
- Always check `ls -lt /mnt/bigssd/*.log` for the MOST RECENT log
- The old run (step 210/4000) was superseded by v2 (step 9720/10000)
- Report the ACTIVE log, not the stale one

## Common Pitfalls

| Wrong | Right |
|-------|-------|
| `ssh dgx` | `ssh spark-85e8.local` |
| `ssh 192.168.1.100` | Check `~/.ssh/config` Includes first |
| `ssh 10.0.0.171` (from Hermes config) | Use `spark-85e8.local` from NVIDIA Sync |
| `ssh root@spark-85e8.local` | Use `djg6228@spark-85e8.local` |
| Assume log at `~/qwen-training/checkpoints/` | Check `/proc/PID/fd/` for actual paths |
| Permission denied with default user | Check NVIDIA Sync config for correct user |
| Report old step numbers from memory | Always grep latest from live log |
| Keep polling same command when log is stale | Check if process is actually running + alive |
| Give rough ETA ("~18 hours") | Calculate exact from log timestamps |
| Assume single log file | Check `ls -lt` for most recent log |
| Report stale log (step 210) | Find active log (step 9720) |

## Stale Log Detection

When the log hasn't updated in hours/days but the process still shows in `ps aux`:

```bash
# 1. Check if process is actually alive (not zombie)
ssh spark-85e8.local 'ps -o pid,stat,etime,cmd -p 443609'
# Look for stat=R (running) or S (sleeping). Z=zombie, D=uninterruptible sleep (bad)

# 2. Check if process is consuming CPU
ssh spark-85e8.local 'top -bn1 -p 443609 | tail -2'
# If CPU% is 0 for extended period, process is hung

# 3. Check for alternative log files
ssh spark-85e8.local 'ls -lt /mnt/bigssd/*.log /tmp/*.log 2>/dev/null | head -10'

# 4. Check /proc/PID/fd for actual log destination
ssh spark-85e8.local 'ls -la /proc/443609/fd | grep log'
```

**Decision tree:**
- Process running + CPU > 0% + log updating → Normal, just slow
- Process running + CPU > 0% + log NOT updating → Logging redirected elsewhere, find new log
- Process running + CPU = 0% + log NOT updating → Process hung, needs restart
- Process NOT in ps → Training finished or crashed, check for completion markers

**Loop detection warning:**
Repeatedly running the same `grep` command to check for updates can trigger Hermes' loop detection. If the log hasn't changed after 3-4 checks, stop polling and investigate why (stuck process, different log file, or completion).
