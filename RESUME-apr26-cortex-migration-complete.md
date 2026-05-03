# Resume Point: Cortex Memory Migration + Hermes Memory Pruning

**Date:** 2026-04-26  
**Session:** Post-restart recovery from corrupted state.db  
**Status:** Cortex DB operational, Hermes memory pruned to 90%, all tools functional

---

## What Was Completed This Session

### 1. Cortex DB Migration (DONE)
- **87 historical entries** migrated from Hermes memory to PostgreSQL `memory_units` table
- Full-text search enabled via `tsvector` index
- All entries accessible via `cortex_memory` tool

### 2. New Tools Built (3)
| Tool | Location | Purpose |
|------|----------|---------|
| `cortex_memory` | `~/.hermes/tools/cortex_memory_tool.py` | Query/add/search Cortex DB |
| `memory_pruner` | `~/.hermes/tools/memory_pruner_tool.py` | Manage Hermes memory overflow |
| `memory_pruner.py` | `~/.hermes/scripts/memory_pruner.py` | Post-restart restoration script |

### 3. Hermes Memory Pruned (DONE)
- **Before:** 99% full (49,987/50,000 chars) — blocking new entries
- **After:** 90% full (45,331/50,000 chars) — safe operating level
- **Method:** Replaced 5 large historical entries with `[ARCHIVED]` placeholders pointing to Cortex DB keys

### 4. State DB Recovery
- `hermes_state.db` was **0 bytes** (corrupted)
- Restored from backup: `state.db.CLEAN_PRE_MERGE_20260423_100929` (859MB)
- Hermes CLI now functional, sessions list working

---

## Current System State

### DGX Spark (GB10/Blackwell SM121)
- **vLLM:** Serving `qwen3.6-27b-uncensored` on port 8000 (eager mode, ~4.5 tok/s)
- **DFlash training:** PID 146221 running since Apr 25 10:38 AM, step ~13, loss ~11.7, GPU 96%
- **Disk:** 37% full (2.2TB free) — safe
- **Model:** Qwen3.6-27B dense, BF16, abliterated, 262K context

### Hermes v0.11.0
- 36 tools, 322 skills, 1 MCP server (biomcp)
- Kimi K2.6 as main model (provider: kimi-coding)
- 101 commits behind upstream (run `hermes update` when ready)

---

## Key Files & References

### Cortex Memory System
- Tool: `~/.hermes/tools/cortex_memory_tool.py`
- Script: `~/.hermes/scripts/memory_pruner.py`
- Migration script: `~/subconscious/hermes_memory_cortex_bridge.py`

### DGX Spark Scripts
- Launch day: `~/dgx-spark-prep/`
- Custom DFlash: `/data/SpecForge/custom_dflash/`
- vLLM patches: `/data/vllm-patches/`

### Checkpoints (DO NOT RESTORE CORRUPTED)
- ✅ `apr26-cortex-migration-complete.md` — This session
- ✅ `apr23-stable-clean` — Clean post-corruption checkpoint
- ❌ `apr22-franken-unleashed` — CORRUPTED (causes `:` parameter injection)

---

## Operating Parameters for New CLI

1. **Memory strategy:** Use `cortex_memory` for long-term storage. Hermes memory only for temporary context.
2. **Context compression:** Warn at ~100K tokens. Force new session after 2 LCM compressions.
3. **DGX Spark:** Check `df -h /` before any large operation. Never load second model while vLLM serving.
4. **Tool building:** Create `tools/<name>_tool.py` with `registry.register()` at module level.
5. **Research first:** Always search online before building. Use direct web_search + web_extract (skip Gemini subagents).

---

## Next Steps (Pending)

1. **DFlash training:** Continue Phase2 on DGX Spark (check PID 146221 status)
2. **Franken Monster v8:** Train ultimate draft model with 25 grafts
3. **Hermes update:** 101 commits behind upstream — update when convenient
4. **Cortex DB:** Continue migrating new entries as Hermes memory fills

---

## Verification Commands for New CLI

```bash
# Verify Cortex DB
python3 ~/.hermes/scripts/memory_pruner.py --verify

# Check DFlash training status
python3 ~/.hermes/scripts/check_dflash_training.py

# Check Hermes memory status
python3 ~/.hermes/tools/memory_pruner_tool.py status

# Check DGX Spark vLLM
ssh djg6228@10.0.0.171 "docker ps | grep vllm"
```

---

**Resume label:** `apr26-cortex-migration-complete`  
**Checkpoint file:** `~/.hermes/CHECKPOINT-apr26-cortex-migration-complete.md`
