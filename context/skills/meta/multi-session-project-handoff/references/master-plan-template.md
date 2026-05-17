# MASTER_PLAN.md Template

## Header (MUST be first line)

```markdown
# ⚠️ NEW CLI: READ THIS FIRST BEFORE DOING ANYTHING ⚠️

## This is a living tracking document. Update it after every session.
```

## Sections (mandatory)

### Project Header
```markdown
## Project: [NAME] — [One-line objective]
```

### Current State (update after EVERY session)
```markdown
### Current State (Last Updated: DATE TIME)
- **Previous [action] [result]** — e.g. "Training KILLED at step 50/1000"
- **GPU/infra status** — e.g. "GPU clean, ready for new run"
- **Files pushed** — e.g. "8 scripts in branch BRANCH_NAME"
- **Key learnings** — e.g. "SGD doesn't work for 27B, need AdamW"
```

### Why Previous Attempt Failed (critical for preventing retries)
```markdown
### Why Previous Attempt Failed
| Issue | Root Cause | Fix Required |
|-------|-----------|--------------|
| Loss flat ~58 | SGD lr=1e-5 too weak | Switch to AdamW |
| Teacher loss stuck | Weight 0.5 too low | Increase to 2.0+ |
| No warmup | Cold start unstable | Add linear warmup |
| Only 44 samples | Severe overfitting | Load full datasets |
```

### Datasets / Resources
```markdown
### Datasets Available
| Dataset | Location | Size | Status |
|---------|----------|------|--------|
| SlimOrca | /data/datasets/slimorca/ | ~200k | Ready |
| OpenHermes | /data/datasets/openhermes/ | ~200k | Ready |
| Synthetic | Generated on DGX | Unlimited | Generator ready |
| [Too big] | N/A | Too big | Skip |
```

### Hardware (if remote GPU)
```markdown
### Hardware
- **DGX:** NVIDIA GB10, 130.7GB GPU
- **Storage:** /mnt/bigssd (7.3TB free)
- **See DGX_ENVIRONMENT.md for connection details**
```

### ⚡ MANDATORY EXECUTION ORDER ⚡
```markdown
## ⚡ MANDATORY EXECUTION ORDER ⚡

**DO NOT SKIP PHASES. DO NOT AUTO-EXECUTE.**

### PHASE 1 — RESEARCH (Do this FIRST)
- [ ] Research item 1
- [ ] Research item 2
- **Deliverable:** [specific output]

### PHASE 2 — BUILD (Only after Phase 1 complete)
- [ ] Build item 1
- **Deliverable:** [specific output]

### PHASE 3 — [NAME] (Only after Phase 2 complete)
...

### PHASE 4 — [NAME] (Only after Phase 3 complete)
...
```

### Dead Ends to AVOID (prevent retrying failed approaches)
```markdown
## Dead Ends to AVOID (We already tried these, they failed)

| Approach | Why It Failed | Don't Retry |
|----------|--------------|-------------|
| SAE-only training | Signal too weak, loss ~60 | Don't use alone |
| Logit distillation | Teacher logits flat/uniform | Don't use logit KL |
| SGD optimizer | No learning on 27B params | Must use AdamW |
| 44 samples only | Overfitting, no generalization | Must use 200k+ data |
```

### Key Files
```markdown
## Key Files in Branch

| File | Purpose | Status |
|------|---------|--------|
| `franken_v8_bridge_v3.py` | Load teacher | ✅ Working |
| `train_expert_logician_v4.py` | Training script | ✅ Running |
| `precompute_teacher_v2.py` | Generate teacher states | ✅ Working |
```

### Next Action Required
```markdown
## Next Action Required

**Current Phase:** PHASE [N] — [NAME]
**Do NOT proceed to Phase [N+1] until [condition].**
**Update this file after every session.**
```

### Session History
```markdown
## Session History

### DATE — Session 1
- Built [X]
- Ran [Y] — [result]
- Learned: [key insight]
- Pushed [files] to [branch]

### DATE — Session 2
- [New CLI started]
- [What happened]
- [What was learned]
```

## Update Rules

1. **After EVERY session** — update Current State, Session History, Next Action
2. **Before EVERY session end** — commit and push
3. **When new CLI starts** — read first, verify phase, don't auto-execute
4. **When phase completes** — check the checkbox, update Next Action

## Anti-Patterns

| Anti-Pattern | Why Bad | Fix |
|-------------|---------|-----|
| Plan in subdirectory | New CLI doesn't find it | Always root-level |
| No "READ THIS FIRST" header | New CLI auto-executes | Use screaming header |
| No execution order | New CLI skips phases | Explicit phase list |
| No dead ends | New CLI retries failures | Document all failures |
| Stale plan (3+ sessions old) | Worse than no plan | Update every session |
| Too long (>200 lines) | Nobody reads it | Use Session History for detail |
| Only successes documented | New CLI repeats failures | Document failures prominently |
