# Qwen 27B Training Session - May 3, 2026

## FINAL STATUS

### Training Results

**Standard Training (train_standard.py):**
- ✅ Completed 1000 steps successfully
- Loss: 15.07 → 8.78
- GPU memory: 53.9GB / 111.5GB (stable)
- Time: ~4 hours (242.9 minutes)
- Checkpoints: `/data/SpecForge/custom_dflash/checkpoints/standard_step_*.pt`

**Novel Architecture v2 (train_novel_v2.py):**
- ⚠️ Reached step 200 before disk full crash
- Loss: flat at ~58-61 (no improvement over base)
- GPU memory: 59.1GB / 116.7GB
- Issue: SAE loss (0.2) is 300x smaller than main loss (60) — not guiding training
- Checkpoints: `/data/SpecForge/custom_dflash/checkpoints/novel_v2_step_*.pt`

**Teacher Distillation (train_teacher_distill_v2_fixed.py):**
- ⚠️ KL divergence explodes (1951-2340) due to teacher logits scale mismatch
- Teacher vocab (248320) vs student vocab (248077) — FIXED by truncation
- Teacher logits are very flat (entropy 12.39 vs random 12.30) — teacher is uniform
- Need teacher HIDDEN STATES for feature alignment, not logits

### Key Discoveries

1. **Simple SGD works** — no need for 8-bit optimizers or CPU offloading
2. **Gradient checkpointing is essential** — saves ~20GB GPU memory
3. **Disk space is the limiting factor** — 1.5TB of checkpoints filled 3.7T root fs
4. **Teacher model architecture is incompatible** — Franken V8 uses custom layers (manifold gates, tree attention, highway networks, MTP4, PARD, SSD, DART, LTD)
5. **SAE reconstruction loss is too small** to guide 27B parameter training

### Evaluation Results

- **Base model (no training)**: Loss 4.3185 | Perplexity 75.07
- **Novel v2 Step 50**: Loss 4.3158 | Perplexity 74.87
- Training made essentially no improvement on perplexity

### Files on DGX

| File | Path | Purpose |
|------|------|---------|
| train_standard.py | `/data/SpecForge/custom_dflash/train_standard.py` | Working baseline |
| train_novel_v2.py | `/data/SpecForge/custom_dflash/train_novel_v2.py` | SAE-guided architecture |
| train_teacher_distill_v2.py | `/data/SpecForge/custom_dflash/train_teacher_distill_v2.py` | Teacher distillation (broken) |
| train_teacher_distill_v2_fixed.py | `/data/SpecForge/custom_dflash/train_teacher_distill_v2_fixed.py` | Fixed vocab mismatch |
| evaluate_checkpoints.py | `/data/SpecForge/custom_dflash/evaluate_checkpoints.py` | Perplexity evaluation |
| precompute_teacher.py | `/data/SpecForge/custom_dflash/precompute_teacher.py` | Teacher output pre-computation |
| fix_teacher_distill.py | `/data/SpecForge/custom_dflash/fix_teacher_distill.py` | Vocab mismatch test |

### Next Steps

1. **Pre-compute teacher hidden states** (not logits) for SAE feature alignment
2. **Use larger dataset** — 44 samples is too small for meaningful learning
3. **Increase SAE weight** or use feature matching loss instead of reconstruction
4. **Save checkpoints to /mnt/bigssd** (7.3T free) instead of root fs
5. **Use gradient clipping** to prevent KL divergence explosion

### GitHub Branches

- `qwen27b-training-artifacts-may3-2026` — 41 scripts + BLUEPRINT.md + CHECKPOINT.md
- `qwen27b-dgx-local-commits-may3-2026` — 4 DGX local commits

Both at: https://github.com/dannyJ848/hermes-agent/
