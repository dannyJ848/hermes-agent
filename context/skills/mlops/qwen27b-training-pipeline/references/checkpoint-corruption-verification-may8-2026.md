# Checkpoint Corruption Verification — May 8, 2026

## Problem
When resuming training after failed higher-rank attempts (512, 768, 1024), how to verify that the checkpoint being loaded is NOT corrupted by those attempts.

## Context
- Rank 256 training completed 1500 steps, saved checkpoint at 16:11
- Then attempted ranks 1024, 768, 512 — all crashed before saving checkpoints
- Resumed rank 256 from checkpoint_step_1500
- User asked: "does that mean there is any corruption from those earlier 1500 training steps?"

## Verification Method

### 1. Timestamp Check
```bash
ls -lt /data/SpecForge/custom_dflash/checkpoints/ | head -10
```
- checkpoint_step_1500: May 8 16:11
- Rank 1024 attempt: started 16:44
- Rank 768 attempt: started 16:57
- Rank 512 attempt: started ~17:15
- Rank 256 resumed: 17:31

**Conclusion:** checkpoint_step_1500 saved at 16:11, BEFORE any higher-rank attempts.

### 2. File Size Check
```bash
ls -la /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_1500/
```
- adapter_model.bin: 5.1GB
- optimizer.pt: 2.6GB

**Size validation:**
- Rank 256 adapter: ~1.275B params × 2 bytes (bf16) = ~2.5GB + overhead = ~5GB ✅
- Rank 512 adapter would be: ~2.5B params × 2 bytes = ~5GB + overhead = ~10GB ❌
- Rank 768 adapter would be: ~3.8B params × 2 bytes = ~7.6GB + overhead = ~15GB ❌

**Conclusion:** 5.1GB file size matches rank 256, not higher ranks.

### 3. Process Check
```bash
ps aux | grep "train_lora" | grep -v grep
```
- Only ONE process running (rank 256 final)
- No orphaned higher-rank processes

## Key Insight
Failed training attempts that crash before the first checkpoint save CANNOT corrupt existing checkpoints. The checkpoint files are only written after successful step completion. OOM kills, serialization errors, and SIGKILLs all occur during forward/backward pass — before any file write.

## Anti-Pattern to Avoid
- Don't assume checkpoint corruption just because training failed at higher ranks
- Don't delete valid checkpoints "just to be safe" without verification
- Don't retrain from step 0 when a clean checkpoint exists

## Verification Checklist
When resuming after failed experiments:
1. Check checkpoint timestamp vs experiment timeline
2. Verify file sizes match expected rank configuration
3. Confirm no duplicate processes are running
4. Check log for "Resumed from checkpoint" message
5. Verify loss values are consistent with previous trajectory
