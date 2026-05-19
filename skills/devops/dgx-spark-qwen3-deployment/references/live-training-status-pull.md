# Live Training Status Pull — DGX Spark Qwen 27B

## Session: May 10, 2026 — Qwen 27B Expert Logician (COMPLETE)

## Current Status (May 10, 2026 17:10 — TRAINING COMPLETE)

```
Step:        10000 / 10000 (100%)
Final checkpoint: May 10 17:10:40
Final loss:  0.8677 (CE:0.552 | D:1.029 | SAE:0.514)
GPU:         NVIDIA GB10, released
PID:         443609 (EXITED after completion)
Process:     COMPLETED — LoRA merge in progress
Checkpoints: /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_10000/
```

## Completion Timeline

- **17:07:34** — Step 9990/10000, loss 0.8677
- **17:10:34** — Step 9999 (gradients zeroed, log skipped)
- **17:10:40** — Checkpoint saved at step 10000
- **17:10:44** — LoRA merge started (gcc compilation visible)
- **Process exited** — Normal completion, not crash

## Historical Sessions

### May 10, 2026 — Final Hours
```
Step 9720/10000 (97.2%) @ 15:37 UTC, loss 0.8719
Step 9730/10000 (97.3%) @ 15:40 UTC, loss 0.8559
Step 9970/10000 (99.7%) @ 17:00 UTC, loss 0.9151
Step 9980/10000 (99.8%) @ 17:04 UTC, loss 0.9273
Step 9990/10000 (99.9%) @ 17:07 UTC, loss 0.8677
Step 10000/10000 (100%) @ 17:10 UTC — COMPLETE
```

### May 8, 2026 — Early Training
```
Step:        1770 / 10000 (17.7%)
Loss:        1.9754 (down from ~3.0 at step 1560)
  - CE:      1.746
  - Distill: 1.354
  - SAE:     0.613
Weights:     (0.91, 0.25, 0.07)
LR:          1.90e-04
GPU:         62.6GB / 130GB (48% used)
GPU Util:    92%
Temp:        64°C
PID:         443609 (running 1h41m, 103% CPU)
```

## One-Command Status Check

```bash
# Quick GPU + process check
ssh -o ConnectTimeout=5 djg6228@10.0.0.171 \
    "echo '=== GPU ===' && nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu \
     --format=csv,noheader && echo '=== PROCESS ===' && \
     ps -f -p 443609 2>/dev/null && echo '=== CHECKPOINTS ===' && \
     ls -lt /data/SpecForge/custom_dflash/checkpoints/ | head -5"
```

## Historical Sessions

### May 8, 2026 — Early Training
```
Step:        1770 / 10000 (17.7%)
Loss:        1.9754 (down from ~3.0 at step 1560)
  - CE:      1.746
  - Distill: 1.354
  - SAE:     0.613
Weights:     (0.91, 0.25, 0.07)
LR:          1.90e-04
GPU:         62.6GB / 130GB (48% used)
GPU Util:    92%
Temp:        64°C
PID:         443609 (running 1h41m, 103% CPU)
```

## Concise Status Format (User Preference)

User expects short, direct output. No preamble. No markdown tables. Example:

```
Step:        1770 / 10000 (17.7%)
Loss:        1.9754 (down from ~3.0 at step 1560)
  - CE:      1.746
  - Distill: 1.354
  - SAE:     0.613
Weights:     (0.91, 0.25, 0.07)
LR:          1.90e-04
GPU:         62.6GB / 130GB (48% used)
GPU Util:    92%
Temp:        64°C
PID:         443609 (running 1h41m, 103% CPU)
```

## Log Format Pattern

```
Step N/MAX | Loss: X.XXXX (CE:X.XXX D:X.XXX SAE:X.XXX) | W:(w_ce,w_d,w_sae) | LR: X.XXe-XX | GPU: XX.XGB
```

Example from live log:
```
2026-05-08 19:12:59,374 [INFO] Step 1770/10000 | Loss: 1.9754 (CE:1.746 D:1.354 SAE:0.613) | W:(0.91,0.25,0.07) | LR: 1.90e-04 | GPU: 62.6GB
```

## Key Metrics to Extract

| Field | Source | Example |
|-------|--------|---------|
| Step | Log line | `Step 1770/10000` |
| Loss | Log line | `Loss: 1.9754` |
| CE | Log line | `CE:1.746` |
| Distill | Log line | `D:1.354` |
| SAE | Log line | `SAE:0.613` |
| Weights | Log line | `W:(0.91,0.25,0.07)` |
| LR | Log line | `LR: 1.90e-04` |
| GPU | Log line | `GPU: 62.6GB` |
| GPU Util | nvidia-smi | `92` |
| Temp | nvidia-smi | `64` |
| PID | ps command | `443609` |
| Runtime | ps etime | `01:41:22` |

## File Locations (Current Run — May 10, 2026)

- Training script: `/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py`
- Log files: `/data/SpecForge/custom_dflash/training.log` (older), `/data/SpecForge/custom_dflash/training_v1.log` (May 8)
- Checkpoints: `/data/SpecForge/custom_dflash/checkpoints/checkpoint_step_NNN/`
  - Each checkpoint: `adapter_model.bin` (~4.8GB) + `optimizer.pt` (~2.5GB)
  - Final model: `/data/SpecForge/custom_dflash/checkpoints/final_model/` (May 8)
- Master doc: `/data/SpecForge/custom_dflash/MASTER_DOC.md`
- instant_context.py: `/data/SpecForge/custom_dflash/instant_context.py`
- Monitor log: `/data/SpecForge/custom_dflash/monitor.log`
- Training status JSON: `/data/training-status.json` (may be stale — check process directly)

## SSH Connection Details

```
Host: 10.0.0.171 (also spark-85e8.local)
User: djg6228
Auth: SSH key (id_ed25519.pub in authorized_keys)
Passwordless sudo: configured
```

## Training Completion Detection

When training finishes successfully:

```
[Step 10000/10000] Loss: N
Saved checkpoint: /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_10000
Merging LoRA weights...
```

**Verification:**
```bash
# Process gone + final checkpoint exists = SUCCESS
ls -la /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_10000/
# → adapter_model.bin, optimizer.pt, etc.

# Process no longer in ps
ps aux | grep train | grep -v grep
# → empty (normal, not a crash)
```

**Post-completion status report:**
```
training COMPLETE. step 10000/10000. final loss: 0.8677. checkpoint saved. lora merge in progress.
```

## Post-Training Pipeline

When training completes:
1. `bash merge_model.sh`
2. `python3 evaluate_model.py`
3. `bash deploy_hermes_qwen.sh`

## CRITICAL: Silent Merge Failure Detection

The original training script's `merge_and_unload()` call **silently failed** — process exited without writing weight files. Only config.json and generation_config.json were present in final_model_merged/. The training log showed gcc compilation lines but no "Merge complete" confirmation.

### Detection Pattern
```bash
# After training "completes", ALWAYS verify weight files exist:
ls -lh /data/SpecForge/custom_dflash/checkpoints/final_model_merged/*.safetensors 2>/dev/null || echo "MERGE FAILED — no weight files"

# Expected: model-00001-of-00015.safetensors, etc. (52GB total)
# Failure: only config.json + generation_config.json (~3KB total)
```

### Recovery: Manual LoRA Merge

When the automatic merge fails, reconstruct and run manually:

```bash
# 1. Identify base model path
cat /data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py | grep from_pretrained
# Usually: /data/models/Qwen3.6-27B-Uncensored (or similar)

# 2. Write merge script
cat > /tmp/merge_lora.py << 'PYEOF'
import os
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM

base_model_path = '/data/models/Qwen3.6-27B-Uncensored'  # VERIFY THIS
adapter_path = '/data/SpecForge/custom_dflash/checkpoints/checkpoint_step_10000'
merged_output = '/data/SpecForge/custom_dflash/checkpoints/final_model_merged'

print(f'Loading base model from: {base_model_path}')
model = AutoModelForCausalLM.from_pretrained(
    base_model_path,
    torch_dtype=torch.bfloat16,
    device_map='auto',
    trust_remote_code=True
)
print('Base model loaded')

print('Loading LoRA adapter...')
model = PeftModel.from_pretrained(model, adapter_path)

print('Merging LoRA weights...')
merged_model = model.merge_and_unload()

print(f'Saving merged model to {merged_output}...')
os.makedirs(merged_output, exist_ok=True)
merged_model.save_pretrained(merged_output)

print('Merge complete!')
print(f'Files: {os.listdir(merged_output)}')
PYEOF

# 3. Run in background (SSH session may timeout)
nohup python3 /tmp/merge_lora.py > /tmp/merge_lora.log 2>&1 &
echo $!  # Save PID for monitoring

# 4. Monitor progress
tail -f /tmp/merge_lora.log
# Expected: "Loading weights: X%" progress, then "Merge complete!"
```

### Background Process Monitoring on Remote SSH

**CRITICAL PITFALL:** `terminal(background=true)` does NOT work over SSH. The backgrounding happens on the MacBook, not the DGX. Use `nohup` + `&` on the remote host directly, then poll via separate SSH commands.

```bash
# Start (returns immediately)
ssh djg6228@spark-85e8.local "nohup python3 /tmp/merge_lora.py > /tmp/merge_lora.log 2>&1 & echo \$!"
# → returns PID like 2878766

# Poll status (run every 30-60 seconds)
ssh djg6228@spark-85e8.local "ps aux | grep merge_lora | grep -v grep"
ssh djg6228@spark-85e8.local "tail -5 /tmp/merge_lora.log"

# Check completion
ssh djg6228@spark-85e8.local "ls -lh /data/SpecForge/custom_dflash/checkpoints/final_model_merged/*.safetensors | wc -l"
# → 15 files = success
```

### Stale Log Detection (Critical)

When `ps aux` shows a running training process but the log hasn't updated:

```bash
# 1. Check ALL log files by recency (the active log may have a different name)
ls -lt /mnt/bigssd/*.log | head -10
# → train_v2_max1000.log     (May 10 15:39 — ACTIVE)
# → train_r256_final.log     (May 10 15:39 — same process, duplicate output)
# → train_lora_sae_teacher_v1.log (May 6 23:58 — STALE, abandoned)

# 2. Check which log the process is actually writing to
ls -la /proc/$(pgrep -f train_lora_sae_teacher) /fd | grep log
```

**The old run (step 210/4000) was superseded by v2 (step 9720/10000).** Always report the MOST RECENT log, not the one with the oldest timestamp.

### ETA Calculation from Live Steps

**User demands exact ETA, not rough estimates.** Calculate from actual log timestamps:

```bash
# Extract two data points with timestamps
grep -E 'Step [0-9]+/[0-9]+' /mnt/bigssd/train_v2_max1000.log | tail -20 | head -1
# → Step 9540/10000 @ 2026-05-10 14:36:56
grep -E 'Step [0-9]+/[0-9]+' /mnt/bigssd/train_v2_max1000.log | tail -1
# → Step 9730/10000 @ 2026-05-10 15:40:36
```

**Calculation:**
- Elapsed: 63.7 minutes for 190 steps
- Seconds per step: 3820s / 190 = **20.1 sec/step**
- Remaining: 10000 - 9730 = 270 steps
- ETA: 270 × 20.1 = **5428 seconds = 90.5 minutes**

**Report format:** `Step 9730/10000 (97.3%). ETA: 90.5 minutes (~17:11 UTC). Rate: 20.1 sec/step.`

Example from May 10, 2026:
- Steps 9540→9730 (190 steps) took 3820 seconds
- Seconds per step: 20.1
- Remaining 270 steps: ~90 minutes ETA

## User Communication Style

- "gimme another status pls" → Short, direct status checks
- "that's too low, bump it to 10k" → Direct commands, no preamble
- "it ready" → DGX cycled and ready for commands
- Values completeness over speed
- Expects proactive OOM prevention
- HATES redundant tool call loops
- "debug it" → investigate and fix immediately, no preamble

## Related

- `references/lora-sae-teacher-distillation-training.md` — Full training config
- `references/ssh-config-discovery.md` — SSH connection details
- `references/ssh-timeout-under-training-load.md` — SSH unresponsiveness during training
