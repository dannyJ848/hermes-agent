# SSH Timeout Under Training Load — May 8, 2026 Incident

## Symptom

SSH to DGX Spark (10.0.0.171) times out during `banner exchange` while training script loads model weights. Connection recovers after weight loading completes.

## Timeline

| Time | Event |
|------|-------|
| 00:16 | Training launched from checkpoint_step_700, PID 54254 |
| 00:20 | Process PID 59310, 109% CPU, 30.2GB RAM — weight loading ~50% |
| 00:25 | Process PID 61724, 113% CPU, 21.6GB RAM — weight loading ~58% |
| 00:30 | SSH check: `Connection timed out during banner exchange` |
| 00:31 | SSH recovered — new PID 61724 confirmed alive |

## Root Cause

`torch.load()`/`safetensors` weight deserialization is CPU-intensive and can starve SSH daemon of scheduling time on ARM cores with unified memory under pressure.

## Key Observations

- **Process survived** — PID changed (54254 → 59310 → 61724) suggesting process restart or PID reuse, but training continued
- **GPU barely active during load** — nvidia-smi shows 1-4% util, 38-42°C (normal for loading phase)
- **RAM grows during load** — 13.5GB → 30.2GB → 21.6GB (fluctuates as layers load)
- **SSH recovers automatically** — no manual intervention needed, just wait

## Recovery Pattern

1. **Wait it out** — SSH recovers once weight loading completes (~5-10 min for 27B)
2. **Use short timeouts** — `ssh -o ConnectTimeout=5` fails fast instead of hanging
3. **Check process via alternative methods** — if SSH down, check DGX local monitor logs on MacBook

## Prevention

- **Lower process priority**: `nice -n 10 python3 train.py` — gives SSH headroom
- **CPU affinity**: `taskset -c 0-15 python3 train.py` — reserve cores for system
- **Avoid SSH polling during load** — check status only after expected load duration

## Related

- `dgx-spark-qwen3-deployment/references/ssh-timeout-under-training-load.md` — general pattern
- `training_monitor.sh` — remote monitor that doesn't need SSH
