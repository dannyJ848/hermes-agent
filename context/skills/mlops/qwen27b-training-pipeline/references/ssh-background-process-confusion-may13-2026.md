# SSH Background Process Confusion — May 13, 2026

## Problem

When monitoring training via SSH, multiple processes and log files create confusion about what is actually running. Users (and agents) may misinterpret:
- A terminated SSH session as a crashed training process
- Pre-tokenization as training
- A stale log file as evidence of a current process

## Scenario

**What happened:**
1. User launched pre-tokenization (PID 572146) via SSH
2. User launched telemetry server (PID 575336) and monitor daemon (PID 579274)
3. Earlier failed axolotl attempt left stale log files in adapter directory
4. User disconnected SSH session
5. Later, user asked "training crashed what happened?"

**Actual state:**
- Pre-tokenization: RUNNING (PID 572146, 50+ min elapsed)
- Training: NEVER STARTED (no train_direct.py process)
- GPU: IDLE (no compute processes)
- Stale logs: From earlier failed axolotl attempt, not current activity

## Diagnostic Checklist

When user reports "training crashed", verify BEFORE diagnosing:

```bash
# 1. What processes are actually running?
ssh djg6228@10.0.0.171 "ps aux | grep python | grep -v grep"
# Expected: pre_tokenize.py (tokenization), telemetry_server.py, monitor2.py
# NOT expected: train_direct.py, axolotl, or any training process

# 2. What GPU processes exist?
ssh djg6228@10.0.0.171 "nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader"
# Expected: EMPTY (pre-tokenization is CPU-only)
# If training were running: would show python process using 50GB+ GPU

# 3. What files exist in output directory?
ssh djg6228@10.0.0.171 "ls -la /data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256/"
# Check timestamps — old files from previous attempts vs new files

# 4. What does the actual training log say?
ssh djg6228@10.0.0.171 "cat /data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256/training.log"
# May show "Starting training at [timestamp]" from OLD attempt
# No "Step 1/XXX" means training never actually started

# 5. Check pre-tokenization progress
ssh djg6228@10.0.0.171 "wc -l /data/SpecForge/custom_dflash/preprocessed/*.jsonl"
# Shows how many examples have been tokenized
```

## Common Misinterpretations

| Observation | Wrong Conclusion | Right Interpretation |
|-------------|------------------|----------------------|
| "training.log exists" | Training is running | Log from OLD attempt, process may be gone |
| "Background process completed" | Training finished/crashed | SSH session terminated, not the remote process |
| "No GPU activity" | Training crashed | Training hasn't started yet — still preprocessing |
| "Process not found" | Training died | Wrong PID checked, or process never existed |
| "Log ends abruptly" | Silent crash | SSH session dropped, process still running remotely |

## Key Rule

**Training hasn't started until you see "Step 1/XXX" or equivalent in the log.**

Pre-training steps that are NOT training:
- Dataset download/transfer
- Dataset consolidation/formatting
- Pre-tokenization to disk
- Model loading to GPU
- LoRA adapter initialization
- Optimizer state creation

These can take hours but are NOT training. Only step iteration with loss computation is training.

## Prevention

**For agents:**
1. Always check `ps aux` for actual training process name (not just "python")
2. Always check GPU for compute processes (not just GPU utilization)
3. Always check log for "Step X/XXX" before declaring training active
4. Distinguish between: preprocessing, loading, and actual step iteration

**For users:**
1. Use separate log files for each stage: `preprocess.log`, `train.log`, `merge.log`
2. Write PID to file when starting: `echo $! > /tmp/train.pid`
3. Use `nvidia-smi dmon` to see GPU activity over time
4. Check process tree: `pstree -p | grep train`

## Related

- `references/axolotl-training-launch-background-may13-2026.md` — Correct background process pattern
- `references/dgx-training-telemetry-monitoring-may13-2026.md` — Telemetry server for clear status
- `references/training-monitoring-ssh-pattern.md` — SSH monitoring best practices
