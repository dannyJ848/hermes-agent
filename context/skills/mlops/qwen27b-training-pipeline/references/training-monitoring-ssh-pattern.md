# Training Monitoring — SSH + Log Tail Pattern

## Problem

When training runs on a remote DGX, you need to check status without SSHing into an interactive session. The training log is written to disk but you need to:
1. Check if the process is still alive
2. See the latest progress (tokenization %, loss, step count)
3. Estimate time remaining
4. Detect stalls or errors

## Pattern

### 1. Check Process Alive
```bash
ssh djg6228@10.0.0.171 "ps aux | grep -E 'axolotl|python.*train' | grep -v grep | head -5"
```
Expected output: Multiple python processes (accelerate launch + axolotl workers)

### 2. Check Latest Progress
```bash
ssh djg6228@10.0.0.171 "tail -50 /path/to/training.log | grep -E 'loss|epoch|step|Tokeniz' | tail -20"
```

For axolotl specifically:
```bash
ssh djg6228@10.0.0.171 "tail -30 /data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256/logs/training_live.log | grep 'Tokenizing' | tail -5"
```

### 3. Parse Tokenization Progress

Axolotl tokenization output format:
```
Tokenizing Prompts (num_proc=20):  99%|█████████▉| 2131393/2158309 [2:12:45<46:58, 9.55 ex/s]
```

Key numbers:
- `2131393/2158309` = current/total examples
- `2:12:45` = elapsed time
- `<46:58` = estimated remaining
- `9.55 ex/s` = current speed

**Important**: Speed drops dramatically in final % (from ~3000/s to ~9/s). This is normal — the remaining samples are the longest/most complex ones. Don't panic.

### 4. Detect Training vs Tokenization

Training hasn't started until you see:
```
loss=1.2345, step=42/10000
```

If you only see `Tokenizing Prompts`, it's still preprocessing. Actual training comes after.

### 5. Full Status Command
```bash
ssh djg6228@10.0.0.171 "echo '=== PROCESS ==='; ps aux | grep -E 'axolotl|python.*train' | grep -v grep | wc -l; echo '=== LATEST ==='; tail -5 /data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256/logs/training_live.log | grep -E 'Tokeniz|loss|step' | tail -3"
```

## Expected Timeline

For 2.15M examples with axolotl:
- Tokenization: 2-3 hours (first 90% in ~1 hour, last 10% in 1-2 hours)
- Actual training: 2-3 days for 2 epochs
- Total: ~3 days

## Warning Signs

| Symptom | Meaning | Action |
|---------|---------|--------|
| Speed drops to <10 ex/s at 99% | Normal final stragglers | Wait |
| Speed drops to <10 ex/s at 50% | Memory pressure or bug | Check `nvidia-smi`, check for errors |
| No output for >30 min | Process may be dead | Check `ps aux` |
| `Killed` in log | OOM killer | Reduce batch size or rank |
| `CUDA out of memory` | GPU OOM | Reduce batch size, enable gradient checkpointing |
| Stuck at same % for >1 hour | Deadlock in multiprocessing | Kill and restart |

## Automation

Set up a cron or background check every hour:
```bash
#!/bin/bash
# training_monitor.sh
LOG="/data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256/logs/training_live.log"
ssh djg6228@10.0.0.171 "tail -1 $LOG" | grep -q "Tokenizing" && echo "Still tokenizing" || echo "Training started"
```

## From This Session (May 13, 2026)

- Training launched at 12:03 UTC
- Tokenization at 99% after 2h27m
- Process alive: PID 438115 (accelerate launch) + 4 workers
- Last seen: 2.14M/2.16M examples tokenized
- Expected: training loops start within 10-20 minutes after tokenization completes
