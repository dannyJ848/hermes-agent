# Anti-Pattern: "Bulletproof" Safety Wrapper Strips All Advanced Training Features

**Date:** May 8, 2026
**Session:** DGX Spark training crash debug
**Severity:** HIGH — 30-40% quality degradation if undetected

## What Happened

A rewrite called `train_bulletproof.py` was created to add atomic launch, OOM recovery, and safe checkpoints. The rewrite's `oom_safe_training_step()` function was called with `loss_fn=None` and only computed basic CE loss via `model(..., labels=labels)`. Teacher distillation, SAE guidance, and multi-objective loss were completely missing.

## Symptoms

- Training "completes" steps but loss is purely CE (no D or SAE components)
- GPU memory stays low (~60GB instead of ~90GB with all features)
- Training runs fast but quality is degraded by ~30-40%
- Log shows only `Step N | Loss: X.XXXX | GPU: YY.YGB` — no CE/D/SAE breakdown

## Root Cause in Code

```python
# In train_bulletproof.py, line 435:
loss_val = oom_safe_training_step(model, batch, optimizer, None, config, monitor, global_step)
#                                               ^^^^ loss_fn=None, never used anyway

# In oom_safe_training_step (line 281):
outputs = model(input_ids=input_ids, labels=labels, output_hidden_states=True)
loss = outputs.loss  # ONLY CE loss, no teacher/SAE
# Teacher cache loaded but NEVER queried
# SAE config fields exist but NEVER used in forward/backward
```

## The Correct Approach

Do NOT rewrite the training loop. Instead, patch the ORIGINAL script with the minimal safety fixes:

1. Add `weights_only=False` to `torch.load()` calls
2. Add atomic launch (kill existing + flock lock)
3. Keep OOM recovery but ADD teacher/SAE loss to it
4. Keep safe checkpoint save

## What to Preserve from Original Script

- Full multi-objective loss: CE + distill_loss + sae_loss
- Teacher cache lookup with content-based MD5 keys
- SAE feature alignment at layers [16, 32, 48]
- Curriculum learning progression
- Synthetic data augmentation
- Proper gradient accumulation with all loss components

## Anti-Pattern Name

**"Safety wrapper reimplements training loop"** — When adding bulletproof protections, NEVER rewrite the core training step. The original script had 20+ hours of debugging to get teacher distillation and SAE alignment working. A rewrite loses all that validated logic. Instead, surgically inject safety code around the existing training loop.

## Validation Checklist Before Launching Any "Improved" Script

```bash
# Verify teacher distillation is actually active
grep -n "distill_loss\|teacher_hidden\|sae_loss" train_script.py | head -10

# Verify multi-objective loss is computed
grep -n "total_loss\|loss =" train_script.py | head -10

# Verify SAE is queried
grep -n "sae\|sparse_autoencoder" train_script.py | grep -v "config\." | head -10

# If any of these return empty, the script has stripped features
```
