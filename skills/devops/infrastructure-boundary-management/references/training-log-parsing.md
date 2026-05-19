# Training Log Parsing — Qwen 27B LoRA+SAE+Teacher Distillation

## Log Format

```
2026-05-09 11:05:59,259 [INFO] Step 4610/10000 | Loss: 1.4138 (CE:1.236 D:1.208 SAE:0.558) | W:(0.77,0.34,0.10) | LR: 1.19e-04 | GPU: 62.6GB
```

**Fields:**
- `Step N/M` — current step / total steps
- `Loss: X` — total multi-objective loss
- `CE:X` — cross-entropy component
- `D:X` — distillation component  
- `SAE:X` — sparse autoencoder component
- `W:(a,b,c)` — loss weights
- `LR: X` — current learning rate
- `GPU: XGB` — GPU memory used

**Intermediate steps** (between logged steps) show:
```
2026-05-09 11:03:00,006 [INFO] [DEBUG] Skipping log for step 4601
```

This is normal — logging happens every N steps to reduce I/O.

## Parsing One-Liner

```bash
ssh spark-85e8.local 'grep "Step [0-9]*/10000" /mnt/bigssd/train_r256_final.log | tail -1'
```

## ETA Calculation

```bash
# Get last logged step and timestamp
ssh spark-85e8.local 'grep "Step [0-9]*/10000" /mnt/bigssd/train_r256_final.log | tail -5'
# Count steps between two timestamps, divide by time delta
# Typical: ~20s per step for rank-256 LoRA on DGX Spark
# Remaining steps * 20s = ETA in seconds
```

## Process Check

```bash
# Verify PID is still running
ssh spark-85e8.local 'ps -p 443609 -o pid,etime,%cpu,%mem,cmd'
# If etime is frozen (not increasing), process may be stuck
```

## OOM Warning Signs

Watch for these in logs:
- `CUDA out of memory` — obvious
- `Cache cleared before backward` — normal OOM prevention, but frequent = near limit
- `Gradients zeroed` without `Optimizer step complete` — possible OOM during step
- GPU memory climbing over time (not stable) — memory leak

## What NOT to Worry About

- `Skipping log for step N` — normal, I/O throttling
- `Cache cleared before backward` — normal OOM prevention
- `Moved to device` / `Moving to device` — normal CPU-GPU transfer
- Loss fluctuating ±0.1 between steps — normal for multi-objective

## Stale Log Detection

When the log file hasn't been updated in hours/days but the process still appears in `ps aux`:

**Symptoms:**
- `grep "Step" log | tail -1` returns same line across multiple checks
- `ls -l log` shows old modification time
- Process shows in `ps` but with 0% CPU

**Investigation:**
```bash
# Check if process is actually alive
ssh spark-85e8.local 'ps -o pid,stat,etime,pcpu -p 443609'
# stat=R (running) or S (sleeping) = OK
# stat=Z (zombie) or D (uninterruptible) = BAD

# Check for alternative log destinations
ssh spark-85e8.local 'ls -lt /mnt/bigssd/*.log /tmp/*.log 2>/dev/null | head -10'
ssh spark-85e8.local 'ls -la /proc/443609/fd | grep log'
```

**Decision:**
- Process alive + CPU > 0% + log not updating → Logging redirected, find new log
- Process alive + CPU = 0% → Hung, needs investigation
- Process not in ps → Finished or crashed, check for completion markers

**Loop detection warning:**
Repeatedly running the same `grep` command to poll for updates can trigger Hermes' loop detection. If the log hasn't changed after 3-4 checks, stop polling and investigate the root cause (different log file, hung process, or completion).
