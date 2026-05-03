# Qwen 27B Training Checkpoint — May 3, 2026 (Updated)

## Status
- **SAE-only training:** PAUSED at step 165 (script has BUG — see below)
- **Full fine-tuning:** ABANDONED after 14 failed attempts across ~6 hours
- **DGX Spark:** Fresh reboot completed, clean state
- **Repo:** Commit c35aba0 (all scripts committed)

## Critical Discovery: train_sae_only.py Script Bug

The `train_sae_only.py` script at `/data/SpecForge/custom_dflash/train_sae_only.py` has a **critical bug**:

**It does NOT freeze Qwen's parameters and uses SGD on `model.parameters()` — meaning it's actually doing full fine-tuning, not SAE-only training.**

Evidence:
```python
# Line 147: Optimizer on ALL model parameters (not just SAEs)
optimizer = torch.optim.SGD(model.parameters(), lr=LEARNING_RATE)

# Missing: model.eval() and param.requires_grad = False for Qwen
# Missing: Only SAE parameters should be passed to optimizer
```

Yet the script somehow reached step 165 with ~59GB GPU usage. Possible explanations:
1. Gradient checkpointing + SGD without momentum might have temporarily stabilized
2. The SAE reconstruction loss provided some gradient regularization
3. The step 165 checkpoint may be corrupted/unreliable

**DO NOT resume from `sae_step_100.pt` without fixing the script first.**

## Full Fine-Tuning Attempts (ALL FAILED)

| # | Approach | Script | Result |
|---|----------|--------|--------|
| 1-6 | SGD + bf16 + grad checkpointing (various configs) | train_standard.py | Gradient explosion (norm=178+) at step 1 |
| 7 | AdamW on GPU | train_standard.py | OOM immediately |
| 8 | DeepSpeed ZeRO-2 | test_deepspeed_zero2.py | OOM during optimizer init |
| 9 | DeepSpeed ZeRO-3 | test_deepspeed_zero3.py | Hangs during init, exit 255 |
| 10 | bitsandbytes 8-bit AdamW | train_full_ft.py | OOM killed CPU RAM |
| 11 | FSDP2 single GPU | train_fsdp.py | Falls back to NO_SHARD — no actual sharding |
| 12 | CPU-offloaded AdamW (fp32 master params) | train_cpu_offload.py | OOM during setup (108GB+ in 121GB CPU RAM) |
| 13 | CPU-offloaded SGD (bf16 momentum) | train_sgd_ft.py | Forward pass extremely slow, system froze from swap thrashing |
| 14 | PagedAdamW8bit (8-bit quantized states) | train_paged_adam.py | System completely frozen, SSH/ping timeout, required hard reboot |

## What Needs to Be Fixed

### 1. train_sae_only.py Script Fix
The script must be modified to:
- Freeze all Qwen parameters: `for param in model.parameters(): param.requires_grad = False`
- Set model to eval mode: `model.eval()`
- Create SAE parameters as trainable tensors (not just hooks)
- Pass only SAE parameters to optimizer
- Remove gradient checkpointing (not needed when model is frozen)

### 2. Checkpoint Verification
The `sae_step_100.pt` checkpoint may be unreliable since it was created by a buggy script. Verify:
- Does it contain only SAE parameter changes?
- Or does it contain full model weight changes (indicating full fine-tuning happened)?

## Resume Procedure (After Fix)

```bash
# 1. SSH to DGX
ssh -i "/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key" djg6228@10.0.0.171

# 2. Fix train_sae_only.py (freeze Qwen, train only SAEs)
# See skill qwen-scope-sae-integration for correct pattern

# 3. Either:
#    a) Start fresh from pretrained Qwen + pretrained SAEs
#    b) Or inspect sae_step_100.pt to see if it's usable

# 4. Run corrected script
cd /data/SpecForge/custom_dflash
python3 train_sae_only_fixed.py
```

## File Locations

| File | Path |
|------|------|
| Buggy script (DO NOT USE) | `/data/SpecForge/custom_dflash/train_sae_only.py` |
| SAE checkpoint (inspect first) | `/data/SpecForge/custom_dflash/checkpoints/sae_step_100.pt` |
| Logs | `/mnt/bigssd/train_sae_only.log` |
| SAE files | `/data/models/Qwen-Scope/` (64 files, 201GB) |
| Student model | `/data/models/Qwen3.6-27B-Uncensored/` |
| Teacher model | `/data/models/FrankenV8-Final/final_model.pt` |
| Dataset | `/data/SpecForge/custom_dflash/hidden_states/` (44 samples) |

## Git Checkpoint

```bash
# Repo at commit c35aba0
cd /data/SpecForge/custom_dflash
git log --oneline -1
# c35aba0 - Session checkpoint May 3 2026: Full fine-tuning attempts 7-14 all failed
```

## Key Findings

1. **Full fine-tuning 27B on single 130GB GPU is NOT viable** — 14 attempts, all failed
2. **SAE-only training is the intended approach** but current script is buggy
3. **Script must freeze Qwen and only train SAE parameters**
4. **DGX Spark requires careful memory management** — pushing to 100% RAM freezes system
5. **Never use SGD for full fine-tuning 27B with bf16** — gradient explosion guaranteed

## Session History

- LCM nodes preserved: 308, 316, 317, 321, 325
- All tool calls logged
- Memory updated with 5 entries
- Skills updated: qwen-scope-sae-integration, large-model-full-finetuning
- Repo committed: c35aba0

## Next Steps

1. **Fix train_sae_only.py** — freeze Qwen, train only SAE parameters
2. **Verify or discard sae_step_100.pt** — check if it's corrupted by full fine-tuning
3. **Restart true SAE-only training** from scratch or verified checkpoint
4. **Monitor with `tail -f /mnt/bigssd/train_sae_only.log`**

## Session Artifacts (Local Machine)

- Checkpoint file: `~/.hermes/CHECKPOINT-may3-qwen27b-sae-only.md`
- Updated skills: `qwen-scope-sae-integration`, `large-model-full-finetuning`
- Updated memory: 5 entries

---
*Checkpoint updated: May 3, 2026 — discovered train_sae_only.py bug*
