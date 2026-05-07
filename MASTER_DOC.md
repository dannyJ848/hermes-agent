# Qwen 27B Training — Master Document
**Last Updated:** May 6, 2026 21:15 UTC
**Status:** RUNNING — PID 881997
**Branch:** qwen27b-training-artifacts-may3-2026
**Commit:** a21912746

## Current Training State
| Attribute | Value |
|-----------|-------|
| Step | 0/4000 (restarted from scratch) |
| Loss | N/A (model loading in progress) |
| GPU | Loading (will be ~85GB when running) |
| DGX | 10.0.0.171 (djg6228/6228) |
| PID | 881997 |
| LoRA | r=1024, alpha=2048 |
| Trainable | 5.1B params (15.9% of 32B) |

## Critical Fixes Applied (May 6, 2026)

### Fix #1: Checkpoint Save OOM (CRASHED at step 999)
- **Root cause:** `model.to('cpu')` moved 85GB to system RAM → OOM killer killed PID 590094
- **Fix:** Save only LoRA adapter params (param.detach().cpu()), no full model move
- **Impact:** ~5GB vs 85GB — safe on 128GB RAM

### Fix #2: Resume Bug (PeftModel.from_pretrained)
- **Bug:** `model = model.from_pretrained(ckpt_path)` fails with `TypeError: missing required positional argument: 'model_id'`
- **Fix:** Use `hasattr(model, 'load_adapter')` check + `PeftModel.from_pretrained(model, ckpt_path)`
- **Code:**
  ```python
  if hasattr(model, 'load_adapter'):
      model.load_adapter(ckpt_path, adapter_name='default')
  else:
      model = PeftModel.from_pretrained(model, ckpt_path)
  ```

### Fix #3: Empty Checkpoint Dir
- **Action:** Deleted `/data/SpecForge/custom_dflash/checkpoints/checkpoint_step_1000` (empty, failed save)
- **Result:** Training starts from step 0 with clean state

## File Locations
- Training script: `/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py`
- Log: `/mnt/bigssd/train_lora_sae_teacher_v1_restart.log`
- Checkpoints: `/data/SpecForge/custom_dflash/checkpoints/`
- Cache: `/mnt/bigssd/teacher_cache/` (82K+ PKL files)

## Quick Status Commands
```bash
# Check process
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=15 djg6228@10.0.0.171 "ps -p 881997 -o pid,comm,etime,pcpu,pmem 2>/dev/null || echo 'PROCESS_DEAD'"

# Check log tail
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=15 djg6228@10.0.0.171 "tail -5 /mnt/bigssd/train_lora_sae_teacher_v1_restart.log"
```

## Known Issues
- SSH to DGX may timeout during heavy model loading — this is expected
- Model loading takes ~5-6 minutes (851 weight shards for 27B model)
- First checkpoint at step 500 will test the OOM fix

## Config
- max_steps: 4000
- save_every: 500
- batch_size: 1
- grad_accum: 4
- warmup_steps: 400
- LR: 0.0002
