# SSH Timeout Under Training Load — DGX Spark

## Symptom

SSH connections to DGX Spark (10.0.0.171) timeout during `banner exchange` or hang on simple commands while training script is loading model weights. Connection recovers after training process completes weight loading or is killed.

## Root Cause

Training process (Qwen 27B LoRA + SAE + teacher distillation) monopolizes CPU during weight deserialization. `torch.load()`/`safetensors` loading is CPU-intensive and can starve the SSH daemon of scheduling time, especially on ARM cores with 128GB unified memory under pressure.

## Timeline from Session (May 8, 2026)

| Time | Event |
|------|-------|
| 00:16 | Launched training from checkpoint_step_700 |
| 00:20 | Process PID 59310, 109% CPU, 30.2GB RAM — weight loading ~50% |
| 00:25 | Process PID 61724, 113% CPU, 21.6GB RAM — weight loading ~58% |
| 00:30 | SSH check: `Connection timed out during banner exchange` |
| — | Training still running (confirmed by later recovery) |

## Recovery Pattern

1. **Wait it out** — SSH recovers automatically once weight loading completes (~5-10 min for 27B model)
2. **Cycle DGX** — if SSH remains down >5 min, power cycle via physical button or IPMI
3. **Use local monitor script** — cron-based monitor on MacBook logs status without needing live SSH

## Prevention / Mitigation

- **Lower process priority**: `nice -n 10 python3 train.py` — gives SSH daemon headroom
- **CPU affinity**: `taskset -c 0-15 python3 train.py` — reserve cores 16-19 for system/SSH
- **Avoid polling during load phase** — check status only after expected load duration
- **Use `ServerAliveInterval` + `ConnectTimeout`** — fail fast rather than hang:
  ```bash
  ssh -o ConnectTimeout=5 -o ServerAliveInterval=3 -o ServerAliveCountMax=1 user@spark
  ```

## Detection Script

```bash
# /tmp/spark_ssh_probe.sh
# Returns: alive | loading | down
ssh -o ConnectTimeout=5 -o ServerAliveInterval=3 -o ServerAliveCountMax=1 \
    djg6228@10.0.0.171 'echo alive' 2>/dev/null || {
    # Check if host pings but SSH rejects
    ping -c 1 -W 2 10.0.0.171 >/dev/null 2>&1 && echo "loading" || echo "down"
}
```

## Related

- `training_monitor.sh` (remote) — checks process health without SSH dependency
- `dgx_local_monitor.sh` (MacBook) — cron-based SSH polling with deduped alerts
