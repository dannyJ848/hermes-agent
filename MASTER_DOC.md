
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
- DGX SSH host: `spark-85e8.local`
- Precompute log: `/mnt/bigssd/precompute_gpu.log`
- Cache dir: `/mnt/bigssd/teacher_cache/`
- Training resume command ready (see skill)
- Cron monitor: `precompute-monitor` (checks every 10 min, alerts at 40K)
- Push from Mac, not DGX (SSH times out under GPU load)

**Everything is wired. Ready for new CLI session.**
