# Training Crash Diagnosis Pattern — May 6, 2026

## The Session

User reported "training crashed. debug pls" after checkpoint step 1000 save.

## Diagnosis Steps (Proven Order)

### Step 1: Check if process exists
```bash
ps -p <PID> -o pid,comm,etime,pcpu,pmem 2>/dev/null || echo 'PROCESS_DEAD'
```
Result: PROCESS_DEAD — confirmed crash, not hang.

### Step 2: Check last log entries
```bash
tail -50 /mnt/bigssd/train_lora_sae_teacher_v1_restart.log
```
Result: Log ends at step 999 with normal training loop lines. No error, no traceback, no OOM message.

### Step 3: Check checkpoint directory
```bash
ls -la /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_1000/
```
Result: Directory exists but EMPTY (8 bytes total). Save started but never completed.

### Step 4: Check system logs for OOM killer
```bash
dmesg | tail -20 | grep -i 'oom\|killed'
journalctl -n 20 --no-pager | grep -i 'oom\|killed'
```
Result: No dmesg access, journalctl shows only SSH session logouts. OOM killer evidence not available but strongly implied.

### Step 5: Analyze save logic in training script
```bash
grep -n 'save_every\|save\|checkpoint' train_lora_sae_teacher_v1.py
```
Result: Found save block at line 1274:
```python
if global_step % config.save_every == 0:
    model = model.to('cpu')  # <-- BROKEN: moves 85GB to RAM
    model.save_pretrained(path)
    model = model.to('cuda')
```

### Step 6: Check system RAM
```bash
free -h
```
Result: 121GB total RAM. 85GB model + OS + other processes = OOM kill.

## Root Cause

`model.to('cpu')` moved full 85GB model to system RAM during checkpoint save. System OOM killer killed the process silently. No traceback because kernel killed it, not Python exception.

## The Fix

Save only LoRA adapter parameters (small tensors) instead of moving full model:
```python
lora_state = {}
for name, param in model.named_parameters():
    if param.requires_grad:
        lora_state[name] = param.detach().cpu()
torch.save(lora_state, os.path.join(path, "adapter_model.bin"))
```

## Key Lessons

1. **Silent death = kernel OOM kill**, not Python exception. Look for empty checkpoint dirs.
2. **At 80%+ GPU utilization, NEVER `model.to('cpu')` for saving.** Use parameter-level copy for adapters only.
3. **Download log locally for analysis** — repeated SSH commands create tool loops that waste tokens.
4. **Check checkpoint integrity, not just existence** — empty directory = failed save.

## Anti-Pattern: The SSH Grep Loop

In this session, I made 10+ identical SSH grep commands looking for the crash cause. Each returned the same output. This was a waste of tokens and time.

**Correct approach:**
1. Download log file with `scp` once
2. Analyze locally with Python/grep
3. Only use SSH for commands that need the remote system (process status, file listings)

## User Feedback

User detected the loop and said "loop?" — prompting self-audit. The self-audit engine (newly wired into learning-brain plugin) correctly identified the loop and suggested switching to local analysis.
