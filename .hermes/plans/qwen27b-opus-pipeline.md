# Qwen 27B Opus-Level Training Pipeline

## ⚠️ CRITICAL: Read MASTER_PLAN.md in repo root BEFORE doing anything

**Repo:** https://github.com/dannyJ848/hermes-agent/  
**Branch:** qwen27b-training-artifacts-may3-2026  
**File:** `MASTER_PLAN.md` — contains full context, dead ends, execution order

---

## Quick Reference (from MASTER_PLAN)

### Current Phase: PHASE 1 — RESEARCH
**Do NOT skip to building or training.**

### What to Research
1. AdamW hyperparameters for 27B full fine-tuning
2. LR warmup + cosine decay schedules
3. Data mixing: SlimOrca + OpenHermes + synthetic ratios
4. Teacher distillation techniques (hidden state vs attention vs logits)
5. SAE-guided training: frozen vs trainable
6. Curriculum learning for reasoning

### Datasets
- SlimOrca-200k: `/data/datasets/slimorca/`
- OpenHermes-200k: `/data/datasets/openhermes/`
- Franken V8 synthetic: generate on DGX

### Hardware
- DGX, NVIDIA GB10, 130.7GB GPU
- Checkpoints: `/mnt/bigssd/`

### Key Files Already Built
- `franken_v8_bridge_v3.py` — loads 11.5B teacher (✅ working)
- `precompute_teacher_v2.py` — generates teacher hidden states (✅ working)
- `train_ultimate_v3_trainonly.py` — previous attempt (⚠️ reference only)

### Dead Ends (Don't Retry)
- SGD optimizer — no learning on 27B
- 44 samples only — overfits
- Logit distillation — teacher logits flat
- SAE-only — signal too weak alone
- No LR warmup — cold start unstable

---

## Execution Checklist

- [ ] Read MASTER_PLAN.md fully
- [ ] Complete Phase 1 research
- [ ] Document findings in MASTER_PLAN.md
- [ ] Build pipeline (Phase 2)
- [ ] Generate synthetic data (Phase 3)
- [ ] Train (Phase 4)
- [ ] Update MASTER_PLAN.md with results

---

## Session Notes

[Add session updates here after each run]
