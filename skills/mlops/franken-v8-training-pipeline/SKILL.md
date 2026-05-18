---
name: franken-v8-training-pipeline
version: 1.0
description: "Franken V8 3-batch progressive training pipeline on DGX Spark. Extract logits from hidden states → train 25-graft model → delete logits → next batch. Final: train Qwen3.6-27B on FrankenV8 draft."
trigger: "When working with Franken V8 model training, DGX Spark GPU, or the 3-batch progressive pipeline"
---

# Franken V8 Training Pipeline

## Model Specs
- **Params**: 8.1B
- **Vocab size**: 248320
- **Grafts**: 25 (all must be defined in training script)
- **Base model**: Qwen3.6-27B-Uncensored (55G at `/data/models/Qwen3.6-27B-Uncensored`)

## Hardware
- **Machine**: DGX Spark (spark-85e8.local)
- **GPU**: NVIDIA GB10, 121GB RAM
- **CUDA**: 13.0
- **PyTorch**: 2.11.0+cu130
- **SSH**: `ssh djg6228@spark-85e8.local`

## 3-Batch Progressive Pipeline (9999 steps total)

| Batch | Steps | Data Source | Status |
|-------|-------|-------------|--------|
| **Batch 2** | 0 - 3332 | `batch_2_logits/` (3332 samples, 1.5T) | ✅ COMPLETE — final_model.pt saved |
| **Batch 1** | 3333 - 6665 | Extract from `hidden_states_full/` (3333 samples) | ✅ COMPLETE — final_model.pt saved |
| **Batch 3** | 6666 - 9999 | Extract from `hidden_states_full/` (3334 samples) | 🔄 EXTRACTING logits now |

### Pipeline Flow
```
Batch 2: train on batch_2_logits/ → final_model.pt (29.4GB, weights only)
         ↓
    DELETE batch_2_logits/ (free 1.5T)
         ↓
Batch 1: EXTRACT logits from hidden_states_full/ (samples 0-3332)
         → train (resume from Batch 2 final_model.pt, steps 3333-6665)
         → final_model.pt at /data/models/FrankenV8-Batch1/
         ↓
    DELETE batch_1_logits/ (free ~1.5T)
         ↓
Batch 3: EXTRACT logits from hidden_states_full/ (samples 6666-9999)
         → train (resume from Batch 1 final_model.pt, steps 6666-9999)
         → final checkpoint
         ↓
    DELETE batch_3_logits/ (free ~1.5T)
         ↓
FINAL STATE: trained FrankenV8 + hidden_states_full/ + Qwen3.6-27B-Uncensored
THEN: Train Qwen3.6-27B on FrankenV8 draft model
```

## Logit Extraction Script

The extraction script must handle the hidden state format correctly:

```python
# Hidden state files have shape: [5, seq_len, 5120] — 5 layers of hidden states
# For logits: use LAST layer (index -1)
# For training: save ALL layers (aux modules need intermediate layers)

def extract_logits(hidden_states_dir, output_dir, model_path):
    model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.bfloat16, device_map="auto")
    model.eval()
    
    for hs_file in sorted(Path(hidden_states_dir).glob("sample_*.pt")):
        hs_data = torch.load(str(hs_file), map_location="cpu", weights_only=True)
        hidden_states = hs_data["hidden_states"]  # [5, seq_len, 5120]
        input_ids = hs_data["input_ids"]
        seq_len = hs_data.get("seq_len", input_ids.shape[0])
        
        # Last layer for logits via LM head
        final_hidden = hidden_states[-1].to(model.device).to(torch.bfloat16)
        with torch.no_grad():
            logits = model.lm_head(final_hidden)  # [seq_len, vocab_size]
        
        # Save in batch_N_logits format
        torch.save({
            "input_ids": input_ids,
            "hidden_states": hidden_states,  # All 5 layers for aux training
            "target_logits": logits.cpu(),
            "seq_len": seq_len,
        }, output_dir / hs_file.name)
```

**Critical**: The `hidden_states` in `hidden_states_full/` are [5, seq_len, 5120] — NOT [seq_len, 5120]. The extraction script must use `hidden_states[-1]` for logits but save ALL layers for training.

## Key Directories (Spark)

| Path | Purpose | Size |
|------|---------|------|
| `/data/SpecForge/custom_dflash/hidden_states_full/` | All 9999 hidden states (keep) | 424G |
| `/data/SpecForge/custom_dflash/batch_3_logits/` | Batch 3 logits (extracting now) | ~1.5T |
| `/data/models/FrankenV8-Batch1/` | Batch 1 training output | 110G |
| `/data/models/FrankenV8-Batch2/` | Batch 2 training output | 83G |
| `/data/models/Qwen3.6-27B-Uncensored/` | Base model | 55G |

**Deleted to free space**: batch_1_logits (1.5T), batch_2_logits (1.5T)

## Training Script
- **Current**: `/data/SpecForge/custom_dflash/train_franken_v8_PROGRESSIVE_FA4.py`
- **Progressive waves**: Core → Speculation Light → Speculation Heavy → Advanced Attention → repeat
- **FA fallback**: FA3 (`flash_attn.flash_attn_interface.flash_attn_func`) — FA4 backward broken on SM120

## FA4 SM120 Bug (Documented)
- FA4 v4.0.0b11 CuTeDSL causal kernel produces NaN with Xavier-init + RMSNorm
- Forward works with `use_tma_O=False` patch
- Backward fails: `DSLRuntimeError: None to Float conversion is not supported`
- **Workaround**: Use FA3 for training, FA4 for inference only

## Checkpoints & Disk Optimization
- **Lightweight checkpoints**: Save model weights ONLY (29GB) instead of full checkpoint with optimizer states (60GB+). Patch the training script:
  ```python
  # BEFORE (60GB per checkpoint — too large for 3.7T disk)
  torch.save({'step': step, 'epoch': epoch, 'model_state_dict': model.state_dict(),
              'optimizer_state_dict': optimizer.state_dict(),
              'scheduler_state_dict': scheduler.state_dict()}, checkpoint_path)
  
  # AFTER (29GB per checkpoint — fits on constrained disk)
  torch.save({'step': global_step, 'epoch': epoch, 'model_state_dict': model.state_dict()}, checkpoint_path)
  ```
- Save every 1000 steps (not 500) to reduce checkpoint count
- Keep only last 1 + final (delete older immediately)
- Weights-only saves to avoid 28GB bloat

## Disk Math for 3.7T Pipeline

**Can the full 3-batch pipeline fit on 3.7T? YES, with careful sequencing:**

| Phase | Data On Disk | Size | Cumulative Used | Free |
|-------|-------------|------|-----------------|------|
| Initial | hidden_states_full + models + other | ~1.5T | ~1.5T | ~2.2T |
| Batch 2 train | + batch_2_logits (1.5T) + checkpoints (80G) | +1.58T | ~3.08T | ~620G |
| After Batch 2 | - batch_2_logits (-1.5T) + final_model.pt | -1.42T | ~1.66T | ~2.04T |
| Batch 1 extract | + batch_1_logits (1.5T) | +1.5T | ~3.16T | ~540G |
| Batch 1 train | + checkpoints (80G) | +80G | ~3.24T | ~460G |
| After Batch 1 | - batch_1_logits (-1.5T) | -1.5T | ~1.74T | ~1.96T |
| Batch 3 extract | + batch_3_logits (1.5T) | +1.5T | ~3.24T | ~460G |
| Batch 3 train | + checkpoints (80G) | +80G | ~3.32T | ~380G |
| **Final** | - batch_3_logits + final model only | ~1.8T | **~1.8T** | **~1.9T** |

**Key insight**: Never hold more than ONE batch of logits + ONE set of checkpoints at a time. The pipeline is sequential: extract → train → delete → next batch.

**Critical**: Delete old models (FrankenV8-Batch1-Final, etc.) before starting new training — they consume 90G each.

## Batch Execution Order (Revised)

The original plan was Batch 1 → Batch 2 → Batch 3. In practice, we ran:
1. **Batch 2 first** (smallest, 3332 samples) — to validate the pipeline
2. **Batch 1** (3333 samples, steps 3333-6665, resume from Batch 2 final)
3. **Batch 3** (3334 samples, steps 6666-9999, resume from Batch 1 final)

This ordering doesn't matter for the final model — all batches get equal training.

## Storage Management
- Internal disk: 3.7T total, ~500G free during training
- Batch logits: ~1.5T each, deleted immediately after training
- External 8TB SSD: arriving Friday Apr 30, mount Saturday

## Status Check Command
```bash
ssh djg6228@spark-85e8.local "tail -5 /data/models/FrankenV8-Batch2/training_resume2.log; nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader"
```

## Current Pipeline Status (Apr 30, 2026)
- **Batch 2**: ✅ COMPLETE — `final_model.pt` at `/data/models/FrankenV8-Batch2/` (29.4GB)
- **batch_2_logits**: ✅ DELETED (freed 1.5T)
- **Batch 1**: ✅ COMPLETE — `final_model.pt` at `/data/models/FrankenV8-Batch1/` (29.4GB, checkpoints at 4000/5000/6000)
- **batch_1_logits**: ✅ DELETED (freed 1.5T, deleted before Batch 3 extraction)
- **Batch 3**: 🔄 EXTRACTING logits from hidden_states_full/ (samples 6666-9999, 3334 files)
- **Disk**: 45% full after batch_1_logits deletion (was 88%)
- **Qwen-Scope**: 33/64 SAE files on Mac (~/Downloads/Qwen-Scope-3.5-27B/, 104G), 31 remaining wait for 8TB SSD Friday
- **8TB SSD**: Arriving Friday, mount Saturday, use for Qwen-Scope + overflow
- **Next**: Batch 3 training (resume from Batch 1 final_model.pt, steps 6666-9999) → delete batch_3_logits → final FrankenV8
- **Then**: Qwen-Scope transfer → integration into Qwen3.6-27B → train Qwen3.6-27B on FrankenV8 draft

## Qwen-Scope Integration (Post-Batch 3)

Qwen-Scope provides Sparse Autoencoders (SAEs) for Qwen3.5-27B. Compatible with Qwen3.6-27B-Uncensored (same architecture: 5120 hidden, 64 layers).

**Download location**: `~/Downloads/Qwen-Scope-3.5-27B/` (Mac)
- 33/64 SAE files downloaded (layers 0-36, 104G)
- Remaining 31 files (~96G) wait for 8TB SSD Friday
- Each file: ~3.1G (81920 features × 5120 hidden)

**Transfer to Spark**: AFTER Batch 3 + FrankenV8 fully trained
**Apply to**: Qwen3.6-27B-Uncensored BEFORE draft-coupling training

**Use cases**:
- Analyze which SAE features FrankenV8 draft activates in target model
- Steer target model behavior based on draft quality
- Debug why certain drafts work better than others

**Cannot use on FrankenV8 directly** — SAEs trained on standard Qwen residual stream, FrankenV8's graft modules distort feature space.

**Transfer command** (run after SSD mounted):
```bash
rsync -avP ~/Downloads/Qwen-Scope-3.5-27B/ spark-85e8.local:/data/Qwen-Scope/
```

### Resume Implementation (CRITICAL)
The training script does NOT natively support `--resume-from`. You must patch it in:

```python
# Add to argparse:
parser.add_argument('--resume-from', type=str, default=None)

# Add before training loop:
if args.resume_from and os.path.exists(args.resume_from):
    logger.info(f'Resuming from checkpoint: {args.resume_from}')
    # Load to CPU first to avoid OOM, then transfer
    checkpoint = torch.load(args.resume_from, map_location='cpu')
    model.load_state_dict(checkpoint['model_state_dict'])
    try:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
    except Exception as e:
        logger.warning(f'Could not restore optimizer: {e}. Restarting from scratch.')
    start_step = checkpoint.get('step', 0)
    global_step = start_step
    del checkpoint  # Free memory immediately
    torch.cuda.empty_cache()
```

**Why this matters**: Checkpoints are 67GB on disk but expand to ~96GB in memory (model + optimizer). Loading directly to GPU causes OOM kill. Load to CPU first, restore model, optionally restore optimizer, then free.

## Freeze Detection
Training can freeze (not crash, not OOM — just hang). Set up monitoring:

```bash
# On Spark: /tmp/freeze_detector.sh
#!/bin/bash
LOG_FILE="/data/models/FrankenV8-Batch2/training_dual_mode.log"
STATE_FILE="/tmp/last_step_state.txt"
ALERT_FILE="/tmp/FREEZE_ALERT"

CURRENT_STEP=$(grep -o "Step [0-9]*/3332" "$LOG_FILE" | tail -1 | sed "s/Step \([0-9]*\)\/3332/\1/")
CURRENT_TIME=$(date +%s)

if [ -f "$STATE_FILE" ]; then
    read LAST_TIME LAST_STEP < "$STATE_FILE"
    TIME_DIFF=$((CURRENT_TIME - LAST_TIME))
    if [ "$CURRENT_STEP" -eq "$LAST_STEP" ] && [ "$TIME_DIFF" -gt 600 ]; then
        echo "FREEZE at step $CURRENT_STEP after ${TIME_DIFF}s" > "$ALERT_FILE"
    fi
fi
echo "$CURRENT_TIME:$CURRENT_STEP" > "$STATE_FILE"
```

Add to crontab: `*/5 * * * * /tmp/freeze_detector.sh`

## Known Failure Modes
| Symptom | Cause | Fix |
|---------|-------|-----|
| "Killed" during resume | OOM loading checkpoint to GPU | Load checkpoint to CPU first |
| Hang during GraftManager setup | `module.to('cpu')` on CUDA-initialized model deadlocks on Blackwell SM120 | **Create GraftManager BEFORE `model.to(device)`** |
| Hang at step ~2100+ (iteration time >60s) | Speculation Heavy wave (SSD+DART+LTD) deadlocks on Blackwell SM120 | **Remove Speculation Heavy wave from GraftManager** |
| Loss spike to 200+ | Speculation Heavy wave activation (normal, but now removed) | N/A — wave removed |
| FA4 backward error | CuTeDSL kernel bug on SM120 | Use SDPA for training (already patched) |
| SSH timeouts during training | Spark overloaded | Wait for init to complete (~5 min) |

## Blackwell SM120 CUDA→CPU Transfer Deadlock
**Critical**: On NVIDIA Blackwell (SM120), calling `module.to('cpu')` on a module that has been moved to CUDA can deadlock indefinitely. This affects GraftManager's CPU offloading.

**Root cause**: PyTorch's `Tensor.to('cpu')` on Blackwell can hang when there are pending CUDA operations or memory synchronization issues.

**Fix**: Always create `GraftManager` BEFORE moving the model to CUDA:
```python
# CORRECT (avoids deadlock)
graft_manager = GraftManager(model, device=device, cpu_offload=True)
model = model.to(device)  # Aux modules stay on CPU via GraftManager

# WRONG (causes hang on Blackwell)
model = model.to(device)
graft_manager = GraftManager(model, device=device, cpu_offload=True)  # Hangs here!
```

**Verification**: Model creation takes ~90s on Spark. If GraftManager setup hangs for >5min, this is the cause.

## Speculation Heavy Wave Removal (Blackwell)
**Critical**: The Speculation Heavy wave (SSD + DART + LTD) causes **deadlocks** on Blackwell SM120, not just slow loss spikes. When this wave activates at step ~2100+, iteration time explodes from ~5s to 60-100s+ and the process eventually hangs or gets killed.

**Fix**: Remove the Speculation Heavy wave from GraftManager.WAVES entirely:
```python
# BEFORE (causes hang):
WAVES = [
    {'name': 'Core Architecture', ...},
    {'name': 'Speculation Light (MTP-4 + PARD)', ...},
    {'name': 'Speculation Heavy (SSD + DART + LTD)', ...},  # REMOVE THIS
    {'name': 'Advanced Attention', ...},
]

# AFTER (stable):
WAVES = [
    {'name': 'Core Architecture', ...},
    {'name': 'Speculation Light (MTP-4 + PARD)', ...},
    {'name': 'Advanced Attention', ...},
]
```

**Why**: The SSD/DART/LTD modules are large (8.5B params combined) and their GPU↔CPU transfer deadlocks on Blackwell. The remaining waves (Core, Speculation Light, Advanced Attention) are stable at ~5s/step.

**Impact**: Training loses the SSD/DART/LTD grafts but gains stability. Loss converges fine without this wave (reached -0.08 at step 2030).

## Hermes Curator Integration

The Curator (new in merged commits) auto-manages agent-created skills. **Critical**: Pin this skill and all meta/iteration skills to prevent auto-archival:

```bash
hermes curator pin franken-v8-training-pipeline
hermes curator pin iteration-pipeline-wiring
hermes curator pin adaptive-cortex-v2
# ... etc
```

Curator runs every 7 days by default. Config in `config.yaml`:
```yaml
curator:
  enabled: true
  interval_hours: 168  # 7 days
  stale_after_days: 30
  archive_after_days: 90
```

**254 agent-created skills** in the system, **71 pinned** to protect from auto-modification.
