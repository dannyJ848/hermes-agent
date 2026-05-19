# ⚠️ NEW CLI: READ THIS FIRST BEFORE DOING ANYTHING ⚠️

## This is a living tracking document. Update it after every session.

---

## Project: Qwen 27B → Expert Logician (Claude/Opus Level)

### Current State (Last Updated: May 3, 2026 ~20:45 CDT)
- **Research COMPLETE** — AdamW with scaled β₂, WSD-S schedule, CKA distillation, curriculum learning
- **Pipeline BUILT** — `train_expert_logician_v4.py` with all improvements
- **Generator BUILT** — `generate_synthetic_traces.py` for Franken V8 reasoning traces
- **10 files pushed** to branch `qwen27b-training-artifacts-may3-2026`
- **GPU clean** — DGX ready for training run
- **Datasets ready** — SlimOrca-200k, OpenHermes-200k, synthetic generator ready

### Research Findings Applied
| Finding | Implementation |
|---------|---------------|
| AdamW with β₂ scaled for B=1 | β₂=0.9999 (β₂* = β₂^(B*/B)) |
| WSD-S LR schedule | warmup=500 → stable=8000 → decay=1500 |
| CKA hidden state matching | CKALoss module for teacher distillation |
| Curriculum learning | Difficulty threshold increases with steps |
| Data mixing | SlimOrca 35% + OpenHermes 35% + Synthetic 30% |
| Gradient accumulation | Effective batch size = 16 (B=1, accum=16) |
| SAE-guided training | Reconstruction loss on layers [16,32,48] |

### Datasets Available
| Dataset | Location | Size | Status |
|---------|----------|------|--------|
| SlimOrca | /data/datasets/slimorca/ | ~200k | Ready |
| OpenHermes | /data/datasets/openhermes/ | ~200k | Ready |
| Franken V8 synthetic | /data/datasets/synthetic_reasoning/ | Generator ready | Build Phase 3 |
| CodeContests | N/A | Too big | Skip |
| APPS | N/A | Too big | Skip |
| ShareGPT | N/A | Too big | Skip |
| UltraChat | N/A | Too big | Skip |

### Hardware
- **DGX:** NVIDIA GB10, 130.7GB GPU
- **Storage:** /mnt/bigssd (7.3TB free) for checkpoints
- **RAM:** ~30GB available

---

## ⚡ MANDATORY EXECUTION ORDER ⚡

**DO NOT SKIP PHASES. DO NOT AUTO-EXECUTE.**

### PHASE 1 — RESEARCH ✅ COMPLETE
Research best practices for training 27B models to expert logician level:
- AdamW vs SGD for large model fine-tuning → Use AdamW with β₂=0.9999 for B=1
- LR schedules → WSD-S outperforms cosine (warmup→stable→decay)
- Curriculum learning → Difficulty threshold increases with steps
- Data mixing → 35/35/30 split, GRAPE-style distribution matching
- Gradient accumulation → B=1 with accum=16, scale β₂ accordingly
- Teacher distillation → CKA hidden state matching > cosine loss
- SAE-guided training → Reconstruction loss as auxiliary signal

**Deliverable:** Research summary documented in this file.

### PHASE 2 — BUILD ✅ COMPLETE
Built improved training pipeline:
- `train_expert_logician_v4.py` — Main training script
  - AdamW optimizer (β₁=0.9, β₂=0.9999, weight_decay=0.01)
  - WSD-S LR schedule (warmup=500, stable=8000, decay=1500)
  - Mixed data loader with curriculum learning
  - CKA hidden state matching for teacher distillation
  - SAE reconstruction loss auxiliary signal
  - Gradient accumulation (effective batch=16)
  - Checkpoint every 50 steps
- `generate_synthetic_traces.py` — Synthetic data generator
  - Problem generators for math, code, logic, tool-use
  - Franken V8 interface for trace generation
  - Configurable domain mixing ratios

**Deliverable:** Both scripts pushed to branch.

### PHASE 3 — GENERATE ⏳ READY TO RUN
Generate synthetic reasoning traces from Franken V8:
- Run: `python generate_synthetic_traces.py --num-samples 10000`
- Mix with real datasets at 35/35/30 ratio
- Save to /data/datasets/synthetic_reasoning/

**Deliverable:** Augmented dataset ready for training.

### PHASE 4 — TRAIN ⏳ READY TO RUN
Run full training:
- Run: `python train_expert_logician_v4.py`
- 10k steps with WSD-S schedule
- Monitor losses every 10 steps
- Save checkpoints every 50 steps to /mnt/bigssd/
- Evaluate on reasoning benchmarks if possible

**Deliverable:** Trained model checkpoint.

---

## Dead Ends to AVOID (We already tried these, they failed)

| Approach | Why It Failed | Don't Retry |
|----------|--------------|-------------|
| SAE-only training (frozen SAEs) | SAE signal too weak, loss ~60 | Don't use alone |
| Logit distillation from Franken V8 | Teacher logits flat/uniform | Don't use logit KL |
| SGD optimizer | No learning on 27B params | Must use AdamW |
| 44 samples only | Overfitting, no generalization | Must use 200k+ real data |
| No LR warmup | Cold start instability | Always warmup |
| 8-bit AdamW (bnb) | Crashed with CUDA errors | Use full AdamW or test first |
| Full fine-tuning 27B on 130GB | 14 failed attempts, OOM/gradient explosion | Use SAE-guided + curriculum |

---

## Key Files in Branch

| File | Purpose | Status |
|------|---------|--------|
| `franken_v8_bridge_v3.py` | Load Franken V8 (11.5B params) | ✅ Working |
| `train_expert_logician_v4.py` | Improved training pipeline | ✅ Built |
| `generate_synthetic_traces.py` | Synthetic reasoning generator | ✅ Built |
| `precompute_teacher_v2.py` | Generate teacher hidden states | ✅ Working |
| `evaluate_checkpoints.py` | Evaluate saved checkpoints | ✅ Working |
| `BLUEPRINT.md` | Architecture blueprint | ✅ Updated |
| `CHECKPOINT.md` | Session checkpoint | ✅ Updated |
| `MASTER_PLAN.md` | This file | ✅ Updated |

---

## Next Action Required

**Current Phase:** PHASE 3 — GENERATE (ready to execute)

**Immediate next steps:**
1. SSH to DGX: `ssh djg6228@spark-85e8.local`
2. Pull latest branch: `git pull origin qwen27b-training-artifacts-may3-2026`
3. Generate synthetic traces: `python generate_synthetic_traces.py --num-samples 10000`
4. Start training: `python train_expert_logician_v4.py`

**Update this file after every session with:**
- What was done
- What was learned
- What failed
- Current phase status
- Next planned action

---

## Session History

### May 3, 2026 — Session 1
- Built Franken V8 bridge v3 (complete architecture match)
- Pre-computed teacher hidden states (991MB)
- Ran training with SGD — flat losses, killed at step 50
- Learned: Need AdamW, more data, warmup, higher teacher weight
- Pushed 8 files to `qwen27b-training-artifacts-may3-2026`

### May 3, 2026 — Session 2
- **Research Phase COMPLETE**
  - AdamW with β₂=0.9999 for B=1 (arXiv:2507.07101)
  - WSD-S LR schedule (arXiv:2410.05192)
  - CKA hidden state matching (ICLR 2025)
  - GRAPE data selection (arXiv:2502.04194)
  - Curriculum learning for reasoning
- **Build Phase COMPLETE**
  - `train_expert_logician_v4.py` — 660 lines, all improvements
  - `generate_synthetic_traces.py` — 358 lines, 4 domains
- **Pushed to branch** — 10 total files now in branch
- **Ready for Phase 3** — Generate synthetic traces

