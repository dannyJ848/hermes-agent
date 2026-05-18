# Training Step Duration Calculation

Session: May 6, 2026 — corrected Qwen 27B training ETA from 5min/step to 30.2s/step.

## The trap

Log output: `Step 990/10000 | Loss: 2.0242` — appears every ~5 minutes.

Wrong assumption: "5 minutes per step" → ETA = 4000 steps × 5min = 13.3 days.

Correct understanding: **Log interval is 10 steps**, not 1 step. The log prints every 10 gradient accumulation steps.

## Calculation

```
Log interval: 10 steps
Time between logs: ~302 seconds (5min 2sec)
Actual step duration: 302s / 10 = 30.2s per step

ETA to step 4000 from step 1000:
  3000 steps × 30.2s = 90,600s = 25.2 hours
```

## How to verify

1. Check log format: does it say "Step X" or "Step X/10000"?
2. Check config for `log_every` or `logging_steps` parameter
3. Look for "Skipping log for step N" messages — indicates log throttling
4. Count lines between identical step numbers in log file

## Key config parameters

```python
# Typical training config
save_every = 500        # Save checkpoint every 500 steps
log_every = 10          # Log every 10 steps (not every step!)
max_steps = 4000        # Total training steps
warmup_steps = 400      # LR warmup period
```

## Pitfall: stale config values

The `max_steps` value may be read dynamically from config file during training loop. If you change the config file mid-training, the loop picks up the new value on next iteration. Verify by checking the actual live config read in the training loop, not just the initial config object.

```python
# In training loop — config re-read each iteration
if global_step >= config.max_steps:  # Reads LIVE value
    break
```

## User correction

User caught the 5min/step error and corrected aggressively. Always verify step duration by checking log interval before stating ETAs.
