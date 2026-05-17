# DGX Qwen Training Deadlock Analysis — May 14, 2026

## Summary
Gradient checkpointing deadlocks with Qwen3.5 linear attention on DGX Spark. Without GC, training OOMs at 117GB. The May 8 training script mystery remains unresolved.

## Environment
- **Host:** DGX Spark (10.0.0.171)
- **GPU:** 130GB (121GB usable)
- **Model:** Qwen3.6-27B-Uncensored + FrankenV8 LoRA
- **Python:** System Python `/usr/bin/python3` (NOT train-venv)
- **PyTorch:** 2.11.0+cu130

## The Deadlock

### Symptom
```
model.gradient_checkpointing_enable({"use_reentrant": False})
# Process enters D state (uninterruptible sleep)
# nvidia-smi: GPU memory allocated, 0% utilization
# kill -9: Cannot terminate process
```

### Memory Breakdown (without GC)
| Component | Size |
|-----------|------|
| Model weights (BF16) | ~51GB |
| LoRA adapters (r=128) | ~0.7GB |
| Activations (batch=1, seq=1024) | ~2GB |
| Gradients | ~0.7GB |
| Optimizer states (8-bit AdamW) | ~1.4GB |
| **Subtotal** | **~56GB** |
| Forward+backward spike | ~61GB |
| **Peak (without GC)** | **117GB+** |

**Result:** OOM at 117GB (exceeds 121GB)

### With GC
- Process deadlocks immediately after "Using 8-bit AdamW"
- Same behavior with `use_reentrant=True` and `use_reentrant=False`

## The May 8 Mystery

The script `train_lora_sae_teacher_v1.py` supposedly completed 10k steps on May 8 with gradient checkpointing. But:

1. **Broken log path:** Script writes to `/mnt/bigssd/train_lora_sae_teacher_v1.log` which doesn't exist on current DGX
2. **Different environment:** May 8 may have used different PyTorch/CUDA version
3. **Different model:** May 8 may have trained on base uncensored, not merged model
4. **Unverified claim:** No checkpoint files from May 8 exist to confirm

## Files on DGX

```
/data/SpecForge/custom_dflash/
├── train_lora_sae_teacher_v1.py      # May 8 script, broken log path
├── train_micro.py                     # r=128, seq=1024, NO gradient checkpointing
├── train_reentrant.py                 # r=256, seq=4096, gradient checkpointing (default)
├── train_qwen_all_tiers.py            # Current live script (uses GC, deadlocks)
├── train_final.py                     # transformers.Trainer (517s/step, intractable)
└── checkpoints/
    ├── final_model_merged/            # Post-trained model (FrankenV8 distillation)
    └── final_model/                   # LoRA adapter weights
```

## Next Actions

1. **Fix May 8 script log path**
   ```bash
   sed -i 's|/mnt/bigssd/|/data/SpecForge/custom_dflash/logs/|g' train_lora_sae_teacher_v1.py
   ```

2. **Test May 8 script with minimal steps**
   ```bash
   /usr/bin/python3 train_lora_sae_teacher_v1.py --max-steps 3
   ```

3. **If May 8 script also deadlocks:**
   - The model architecture itself is incompatible with gradient checkpointing
   - Need alternative: smaller model (7B) or bigger GPU (A100/H100)

4. **If May 8 script works:**
   - Compare environment differences (PyTorch version, CUDA version)
   - Compare model differences (base vs merged)
   - Identify what makes it work

## Anti-Patterns

### "GC should work with any model"
- Wrong: Assuming gradient checkpointing is universally compatible
- Right: Testing with minimal steps before committing to full training

### "Without GC we OOM, so we MUST make GC work"
- Wrong: Binary thinking that GC is the only solution
- Right: If GC deadlocks and without GC we OOM, need a different approach entirely

## References
- `qwen27b-training-pipeline` skill for full training configuration
- `references/gb10-training-intractability-qlora-vs-gradient-checkpointing-may13-2026.md` for speed analysis
- `references/dgx-environment-cpu-only-torch-trap-may13-2026.md` for environment verification
