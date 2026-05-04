# ⚠️ NEW CLI: READ THIS FIRST BEFORE DOING ANYTHING ⚠️

## This is a living tracking document. Update it after every session.

---

## Project: Qwen 27B → Expert Logician (Claude/Opus Level)

### Current State (Last Updated: May 3, 2026 ~21:15 CDT)
- **NEW TRAINING RUNNING** — `train_expert_logician_v4.py` launched by second CLI
- **PID 287961** on DGX, CPU 92%, GPU loading model (0% util, 43°C)
- **Previous training KILLED** at step 50/1000 — flat losses, no learning
- **Franken V8** fully loaded via custom bridge (11.5B params, 0 missing keys)
- **Teacher hidden states pre-computed** (991MB, 44 samples, 9 layers each)
- **Qwen-Scope SAEs** integrated: layers 16, 32, 48 loaded from `/data/models/Qwen-Scope/`
- **New scripts added:** `train_expert_logician_v4.py` (660 lines), `generate_synthetic_traces.py` (358 lines)

### Why Previous Run Failed
| Issue | Root Cause | Fix Required |
|-------|-----------|--------------|
| CE loss flat ~58 | SGD lr=1e-5 too weak for 27B params | Switch to AdamW |
| Teacher loss stuck at 8.0 | Normalization helped but weight 0.5 too low | Increase to 2.0+ |
| No warmup | Cold start, gradients unstable | Add linear warmup |
| Only 44 samples | Severe overfitting risk | Load SlimOrca + OpenHermes |
| No LR decay | Flat learning rate | Cosine decay |

### Datasets Available
| Dataset | Location | Size | Status |
|---------|----------|------|--------|
| SlimOrca | /data/datasets/slimorca/ | ~200k | Ready |
| OpenHermes | /data/datasets/openhermes/ | ~200k | Ready |
| Franken V8 synthetic | Generated on DGX | Unlimited | Generator ready |
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

### PHASE 1 — RESEARCH (Do this FIRST)
Research best practices for training 27B models to expert logician level:
- AdamW vs SGD for large model fine-tuning
- LR schedules: warmup + cosine decay specifics
- Curriculum learning for reasoning tasks
- Data mixing ratios (what % SlimOrca vs OpenHermes vs synthetic)
- Gradient accumulation strategies for 130GB GPU
- Teacher distillation: hidden state vs logit vs attention matching
- SAE-guided training: frozen vs trainable, sparsity penalties

**Deliverable:** Research summary with specific hyperparameters to try.

### PHASE 2 — BUILD (Only after Phase 1 complete)
Build improved training pipeline based on research:
- AdamW optimizer (beta1=0.9, beta2=0.999, weight_decay=0.01)
- LR warmup (100 steps) + cosine decay to 1e-6
- Data loader: SlimOrca + OpenHermes + synthetic mix
- Teacher hidden matching with learned layer weights
- Gradient accumulation (8-16 steps)
- Checkpoint every 50 steps to /mnt/bigssd/

**Deliverable:** `train_opus_v1.py` script ready to run.

### PHASE 3 — GENERATE (Only after Phase 2 complete)
Generate synthetic reasoning traces from Franken V8:
- Use Franken V8 to generate 10k+ reasoning chains
- Mix with real datasets at researched ratio
- Save to /mnt/bigssd/synthetic_reasoning/

**Deliverable:** Augmented dataset ready for training.

### PHASE 4 — TRAIN (Only after Phase 3 complete)
Run full training:
- 10k+ steps
- Monitor losses every step
- Save checkpoints every 50 steps
- Evaluate on MMLU/GSM8K if possible

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
| MSE teacher matching | Scale mismatch, loss ~2000 | Use CKA or layer-norm first |

---

## Key Files in Branch

| File | Purpose | Status |
|------|---------|--------|
| `train_expert_logician_v4.py` | New CLI's opus-level pipeline | ✅ RUNNING NOW |
| `generate_synthetic_traces.py` | Franken V8 synthetic data generator | ✅ Ready |
| `franken_v8_bridge_v3.py` | Load Franken V8 (11.5B params) | ✅ Working |
| `precompute_teacher_v2.py` | Generate teacher hidden states | ✅ Working |
| `train_ultimate_v3_trainonly.py` | Previous training script | ⚠️ Reference only |
| `evaluate_checkpoints.py` | Evaluate saved checkpoints | ✅ Working |
| `SESSION_LOG_MAY3.md` | Session history | ✅ Updated |

---

## Next Action Required

**Current Phase:** PHASE 1 — RESEARCH

**Do NOT proceed to Phase 2 until research is complete and documented here.**

**Update this file after every session with:**
- What was done
- What was learned
- What failed
- Current phase status
- Next planned action

---

## Session History

### May 3, 2026 — Session 1 (First CLI)
- Built Franken V8 bridge v3 (complete architecture match)
- Pre-computed teacher hidden states (991MB)
- Ran training with SGD — flat losses, killed at step 50
- Learned: Need AdamW, more data, warmup, higher teacher weight
- Pushed 8 files to `qwen27b-training-artifacts-may3-2026`

### May 3, 2026 — Session 2 (Second CLI)
- **Research phase completed** by second CLI
- Built `train_expert_logician_v4.py` with:
  - AdamW with β₂ scaled for batch=1
  - WSD-S learning rate schedule (warmup-stable-decay)
  - CKA hidden state matching (better than MSE)
  - SAE reconstruction loss (Qwen-Scope layers 16/32/48)
  - Curriculum learning with SlimOrca + OpenHermes
  - Gradient accumulation (effective batch=16)
- Built `generate_synthetic_traces.py` for Franken V8 synthetic data
- **Training launched** — PID 287961, running on DGX
- Pushed all context files: MASTER_PLAN.md, DGX_ENVIRONMENT.md, .hermes/plans/

### [Next session — update here]

