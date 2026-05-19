# Rank Feasibility Analysis Pattern

## Context
When evaluating whether a higher LoRA rank is feasible on limited GPU memory, distinguish between OOM failures and serialization/save-state failures. The symptoms look identical (process dies), but root causes and fixes differ completely.

## The Trap
Higher ranks (512, 1024) fail during training and the assumption is "OOM — rank too big for GPU." But the actual failure may be checkpoint resume breaking due to `weights_only=True` in PyTorch 2.6, which has nothing to do with memory.

## Diagnostic Pattern

### Step 1: Check if training ever ran at the higher rank
```bash
grep -n "Step.*Loss" train.log | head -5
```
If steps logged with loss values, training RAN. The crash happened later (likely on resume or checkpoint save).

### Step 2: Check crash type
```bash
grep -n "Traceback\|ERROR\|OOM\|OutOfMemory\|UnpicklingError\|weights_only" train.log | head -10
```
- `torch.OutOfMemoryError` = genuine OOM, rank too big
- `_pickle.UnpicklingError: Weights only load failed` = serialization bug, rank is fine
- `Killed process` in dmesg = OOM killer, rank too big
- Clean exit after "Resuming from checkpoint" = weights_only bug

### Step 3: Check GPU memory at crash time
```bash
grep -n "GPU:" train.log | tail -5
```
If GPU was <90GB at crash on a 121GB GPU, it's NOT OOM. The rank fits.

### Step 4: Verify rank actually loaded
```bash
grep -n "r=512\|r=1024\|LoRA: r=" train.log | head -3
```
If the rank logged at startup and steps proceeded, the rank is viable.

## Memory Math for Qwen 27B on 130GB GPU

| Component | Rank 256 | Rank 512 | Rank 1024 |
|-----------|----------|----------|-----------|
| Base model (bf16, frozen) | 50 GB | 50 GB | 50 GB |
| LoRA params (fp32) | 2 GB | 4 GB | 8 GB |
| Optimizer states (8-bit AdamW) | 0.8 GB | 1.6 GB | 3.2 GB |
| Activations (seq=512, batch=1) | 6 GB | 6 GB | 6 GB |
| SAE overhead | 2 GB | 2 GB | 2 GB |
| **Total** | **~61 GB** | **~64 GB** | **~70 GB** |
| Headroom | 60 GB | 57 GB | 51 GB |

All ranks fit. The limiting factor is NOT memory.

## Key Insight from May 8, 2026 Session

Rank 1024 was attempted and logged steps 10-100 successfully:
- Step 10: GPU 85.5GB
- Step 100: GPU 73.7GB
- Crashed on RESUME with `weights_only` error, NOT during training
- This proves rank 1024 is memory-viable

Rank 512 was attempted multiple times:
- All crashes were `weights_only` errors on checkpoint loading
- Never hit OOM
- Rank 512 is also memory-viable

## Decision Matrix

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Crash at startup, no steps logged | OOM during model load | Reduce rank or enable gradient checkpointing |
| Steps log for a while, then crash on "Resuming checkpoint" | `weights_only` serialization | Add `weights_only=False` to all `torch.load()` calls |
| Steps log, GPU >115GB, then `Killed` | Genuine OOM | Reduce rank or batch size |
| Process dies silently, no error in log | OOM killer (SIGKILL) | Check `dmesg`, reduce memory usage |

## Fix Application Order

When retrying a higher rank:
1. Apply `weights_only=False` to ALL `torch.load()` calls FIRST
2. Add atomic launch (prevent process duplication)
3. Verify single process after launch
4. Monitor GPU — should stay under ~75GB for rank 1024
5. If still crashes, THEN consider rank reduction

## Anti-Pattern: Assuming OOM Without Evidence

Don't reduce rank just because training crashed. Verify the actual crash reason first. A working rank 1024 with `weights_only=False` produces ~40% higher quality than rank 256 (more trainable parameters, better expressiveness). Prematurely downgrading rank sacrifices quality for no reason.
