# Training Completion Verification — Don't Trust "Merging LoRA weights..."

**Date:** May 10, 2026
**System:** DGX Spark (NVIDIA GB10)
**Training:** Qwen 27B LoRA + SAE + Teacher Distillation

## The Pitfall

The training log says:
```
2026-05-10 17:10:40,002 [INFO] Saved checkpoint: /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_10000
2026-05-10 17:10:44,599 [INFO] Merging LoRA weights...
2026-05-10 17:10:45,003 [INFO] aarch64-linux-gnu-gcc ...
```

**This does NOT mean the merge succeeded.** The process logged "Merging LoRA weights..." then started compiling C extensions (gcc output). The actual model weight files (.safetensors, .bin, .pt) were **never written** to `final_model_merged/`.

## Verification Checklist (run in order)

### 1. Check process is actually gone
```bash
ssh djg6228@spark-85e8.local "ps aux | grep train | grep -v grep"
```
- Empty output = process exited (good or bad)
- If process still running, wait and re-check

### 2. Check final_model_merged/ has WEIGHT files
```bash
ssh djg6228@spark-85e8.local "find /data/SpecForge/custom_dflash/checkpoints/final_model_merged/ -name '*.safetensors' -o -name '*.bin' -o -name '*.pt' | wc -l"
```
- **MUST return > 0** — config.json alone is NOT a complete model
- If 0 files: merge failed or was interrupted

### 3. Check total file count in merged directory
```bash
ssh djg6228@spark-85e8.local "ls -lh /data/SpecForge/custom_dflash/checkpoints/final_model_merged/"
```
- A complete Qwen 27B model has ~15-30 .safetensors files (sharded)
- Plus config.json, tokenizer files, generation_config.json
- If only 2 files (config.json + generation_config.json): **INCOMPLETE**

### 4. Check for explicit completion message in log
```bash
ssh djg6228@spark-85e8.local "grep -iE 'merge complete|done|saved final|export complete' /mnt/bigssd/train_v2_max1000.log"
```
- Empty result = no confirmation logged
- Look for "Merge complete" or "Model saved to final_model_merged"

### 5. Verify checkpoint_step_10000 exists (fallback)
```bash
ssh djg6228@spark-85e8.local "ls -lh /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_10000/"
```
- If checkpoint exists but merged model doesn't: can re-run merge manually
- If neither exists: training may have failed before saving

## What "Merging LoRA weights..." Actually Means

The log message "Merging LoRA weights..." is emitted **when the merge function is called**, not when it completes. The subsequent gcc compilation output is from the `peft` library compiling CUDA extensions for the merge operation. If the process crashes during compilation or runs out of memory during the actual weight merge, **no error is logged** — the process just dies.

## Correct Status Reporting

**WRONG:** "Training complete, LoRA merged, ready for evaluation"

**RIGHT:** "Training reached step 10000/10000. Checkpoint saved. Merge process started but **weight files not verified**. Checking final_model_merged/ for .safetensors files... [then report actual finding]"

## Recovery If Merge Failed

If `final_model_merged/` has no weight files:

```python
# Re-run merge manually on DGX
from peft import PeftModel
from transformers import AutoModelForCausalLM

base = AutoModelForCausalLM.from_pretrained(
    "/data/SpecForge/custom_dflash/checkpoints/checkpoint_step_10000",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
model = PeftModel.from_pretrained(base, "/path/to/lora/weights")
merged = model.merge_and_unload()
merged.save_pretrained("/data/SpecForge/custom_dflash/checkpoints/final_model_merged/")
```

Or use the training script's merge function if it has one.

## Key Lesson

**Log messages are not ground truth. File existence is.**
- "Merging..." ≠ "Merged"
- "Saved checkpoint" = checkpoint exists (verify with ls)
- "Ready for evaluation" = weight files exist + config valid + tokenizer present

Always verify with `find *.safetensors` before declaring training complete.
