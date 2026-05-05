
## May 4, 2026 19:35 UTC - Precompute Fix #5: Working Tokenizer

**Problem:** FrankenV8-Final tokenizer produced empty tensors (shape [1,0]) for all text, causing 100% teacher forward pass failure.

**Root cause:** FrankenV8-Final model directory has no tokenizer files (only checkpoint files). AutoTokenizer.from_pretrained() silently failed and returned a broken tokenizer that tokenizes everything to 0 tokens.

**Fix:** Changed precompute script to load tokenizer from `/data/models/Qwen3-0.6B/` which has proper tokenizer.json, vocab.json, merges.txt files.

**Result:** 400 samples processed, 400 cached, 0 errors. GPU 84% util. ~4s per 50-sample batch.

**Files modified:**
- `/data/SpecForge/custom_dflash/training/qwen27b-lora-sae-teacher/precompute_teacher_cache_gpu.py` - tokenizer path changed from `config.teacher_model_path` to `/data/models/Qwen3-0.6B/`

## May 4, 2026 19:45 UTC - Precompute v4: Working Tokenizer Fix

**Problem:** FrankenV8-Final tokenizer produced empty tensors (shape [1,0]) for all text, causing 100% teacher forward pass failure.

**Root cause:** FrankenV8-Final model directory has no tokenizer files (only checkpoint files). AutoTokenizer.from_pretrained() silently fails and returns a broken tokenizer that tokenizes everything to 0 tokens.

**Fix:** Changed precompute script to load tokenizer from `/data/models/Qwen3-0.6B/` which has proper tokenizer.json, vocab.json, merges.txt files.

**Result:** 4,400+ samples processed, 4,400 cached, 0 errors. ~12.5 samples/sec. GPU 84% util.

**Files modified:**
- `/data/SpecForge/custom_dflash/training/qwen27b-lora-sae-teacher/precompute_teacher_cache_gpu.py` - tokenizer path changed from `config.teacher_model_path` to `/data/models/Qwen3-0.6B/`

**ETA to 50K cache:** ~1 hour

| **Current status:** Precompute running. 4,400 cached. 0 errors.

## May 4, 2026 19:50 UTC - Full Session Sync for New CLI

**Context:** User requested complete audit and sync of all persistence layers before new CLI session. Precompute at 7,950+ cached, 0 errors. ~12.5 samples/sec. ETA to 50K: ~45 minutes.

**User intent:** Options 1 and 2 — continue monitoring precompute + auto-launch training when cache hits 50K.

**Audit Results — ALL LAYERS SYNCED:**

1. **GitHub Repo** — Commit `297bb0d1f` pushed to `qwen27b-training-artifacts-may3-2026`. "precompute v4: fix tokenizer — use Qwen3-0.6B tokenizer, FrankenV8 tokenizer was broken (0 tokens). Synced from DGX"

2. **Skill `qwen27b-training-pipeline`** — Fix #21 added: "Precompute v4: Broken tokenizer fix (May 4, 19:35 UTC)". Reference file `references/broken-tokenizer-detection.md` created (49 lines, 2030 bytes). Session handoff protocol updated with: "Push from local Mac repo, not DGX SSH under load"

3. **Memory** — Entry: "Precompute fix May 4: FrankenV8 tokenizer broken (0 tokens). Use Qwen3-0.6B tokenizer. Content-based MD5 cache keys. 12 samples/sec, 0 errors."

4. **MASTER_DOC.md** — Synced from DGX via rsync. Contains precompute v4 entry with tokenizer fix details.

5. **DGX Precompute** — 7,950+ processed, 7,950 cached, 0 errors. ~12.5 samples/sec. Cron monitor will alert at 40K.

**New CLI Pickup State:**
- Git pull → `297bb0d1f`
- Skill load → fix #21 + reference file
- Memory injection → precompute fix context
- MASTER_DOC → full session history

**Critical Notes for New CLI:**
- DGX SSH host: `spark-85e8.local` (use from user's Mac terminal, NOT from Hermes SSH — DGX SSH times out under GPU load)
- Precompute log: `/mnt/bigssd/precompute_gpu.log`
- Cache dir: `/mnt/bigssd/teacher_cache/`
- Training resume command ready (see skill)
- Cron monitor: `precompute-monitor` (checks every 10 min, alerts at 40K)
- Push from Mac, not DGX (SSH times out under GPU load)
- **DGX access: User's Mac has SSH config for spark-85e8.local. Hermes CLI cannot reach DGX directly — always use user's Mac terminal or DGX-local processes.**

**Everything is wired. Ready for new CLI session.**

## May 4, 2026 23:04 UTC - Teacher Distillation 5-Fix Activation

**Problem:** Training runs but teacher distillation loss (D) stays at 0.000 even with 74K cached files.

**Root causes (ALL must be fixed simultaneously):**
- **A: Tokenizer mismatch** — Precompute uses Qwen3-0.6B tokenizer, training uses student's. Different tokenizers → different token IDs → different MD5 cache keys → 100% cache misses.
- **B: Text formatting mismatch** — Precompute joins messages with `\n\n`, training uses `\n`.
- **C: File ordering mismatch** — Precompute sorts files, training uses os.walk (arbitrary order).
- **D: Column handling mismatch** — Precompute handles multiple column formats + fallback, training only conversations/messages.
- **E: Tensor dimension mismatch** — Precompute saves 2D [seq_len, hidden], training expects 3D.

**Fixes applied:**
- A: Force training to use `/data/models/Qwen3-0.6B/` tokenizer
- B: Update `_format_conversation` to use `\n\n`
- C: Add `sorted()` to training file discovery
- D: Copy precompute's full column handling logic
- E: Add `.unsqueeze(0)` in training distillation loop

**Result:** Step 0: Loss 6.0187 (CE:5.776 D:1.215). Teacher distillation ACTIVE. D ~1.07 stable.

**Key insight:** Content-based MD5 cache keys are fragile — entire tokenization pipeline must match exactly.

## May 5, 2026 07:58 CDT — Training Stable at Step 730

**Status:** Training RUNNING. Step 730/10000. Loss 1.87 (69% reduction from 6.02).

**Current metrics:**
- Step 730 | Loss: 1.87 (CE: 1.69, D: 1.07) | LR: 2.00e-04 | GPU: 58.3GB
- Progress: 7.3% complete
- Speed: ~21s/step
- ETA: ~55 hours for 10K steps
- PID: 583342 on DGX 10.0.0.171

**Milestone:** Passed 220-step hang threshold where previous runs froze. Now 3x further without issues.

**All persistence layers updated for new CLI session.**

## May 5, 2026 11:41 CDT — Training at Step 1400, Cortex Daemon Fixed

**Status:** Training RUNNING. Step 1400/10000. Loss 1.62 (73% reduction from 6.02).

**Current metrics:**
- Step 1400 | Loss: 1.62 (CE: 1.46, D: 1.07, SAE: 0.000) | LR: 1.96e-04 | GPU: 58.3GB
- Weights: CE:0.93, Distill:0.24, SAE:0.06
- Progress: 14.0% complete
- Speed: ~21s/step
- ETA: ~50 hours for 10K steps
- PID: 583342 on DGX 10.0.0.171
- Runtime: ~20.5h
- Next checkpoint: Step 1500

**Cortex daemon schema fix (May 5, 11:35 CDT):**
- Problem: `cortex_access.py` INSERT referenced non-existent columns (`tip_type`, `condition`, `recommendation`, `rationale`, `tool_name`, `last_seen`)
- Fix: Removed columns from INSERT, store tip fields in `metadata` JSON, use `updated_at` instead of `last_seen`, remove broken `ON CONFLICT` clause
- Result: Daemon running (PID 97192), 7060 tips, flywheel active, Elo avg 1336
- Watchdog cron: `cortex-watchdog-shell` every 5 min via `~/.hermes/cortex_watchdog.sh`

**Updated all persistence layers with latest status.**
