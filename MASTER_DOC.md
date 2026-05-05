
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

**Current status:** Precompute running. 4,400 cached. 0 errors.
