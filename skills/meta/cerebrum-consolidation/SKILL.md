---
name: cerebrum-consolidation
description: Run cerebrum memory consolidation — episodic→semantic transfer, contradiction check, and status report. Cron task for periodic memory maintenance.
version: 1.0
category: meta
triggers:
  - "cerebrum consolidation"
  - "memory consolidation"
  - "consolidate memories"
---

# Cerebrum Memory Consolidation

Periodic maintenance of the cerebrum memory system: transfer episodic memories to semantic long-term storage, check for contradictions, and report status.

## Critical Path Facts

- **DB location**: `~/.hermes/cerebrum_memory.db` (the REAL one, 8+ MB)
- **Stale DB**: `~/subconscious/cerebrum_memory.db` exists but is 0 bytes — IGNORE IT
- **Controller**: `~/subconscious/controller.py` hardcodes `Path.home() / ".hermes" / "cerebrum_memory.db"`
- The `cerebrum-memory` skill appears in skills_list but is NOT actually installed — cannot be loaded via skill_view

## Database Schema (key tables)

### semantic_facts
```
id, content, source, provenance, category, trust, salience,
access_count, consolidation_count, created_at, last_accessed,
last_consolidated, entities, tags, session_id
UNIQUE(content)
```

### experiences
```
id, action_hash, action_type, action_detail, action_fingerprint,
result, error_pattern, error_snippet, lesson, approach, fix_command,
iterations, frequency, speed_ms, last_seen, created_at, context_tags
```
⚠️ **NO `content` or `category` column** — use `action_type` + `lesson` to build content.

### Other tables to report on
`facts`, `reasoning_traces`, `reasoning_patterns`, `distilled_tips`, `epistemic_facts`, `predictions`, `tool_call_log`

## Three-Phase Operation

### Phase 1: CONSOLIDATE
1. Count total facts, unconsolidated, never-consolidated, reasoning traces
2. **Boost** high-access facts (access_count > 3, trust < 0.85) → trust += 0.05
3. **Decay** low-trust/low-access facts (trust < 0.3, access_count < 2) → trust -= 0.05
4. **Extract** from experiences: `f"{action_type}: {lesson}"` → INSERT OR IGNORE into semantic_facts with category='experience'
5. COMMIT

### Phase 2: CONTRADICT
1. Query category trust distribution (avg, min, max, spread) — flag spreads > 0.5
2. Find near-duplicates: same category, similar length (±30 chars) — LIMIT 10
3. Check exact content conflicts with diverging trust (>0.3 difference)
4. Report total issues

### Phase 3: STATUS
1. Count rows per table (semantic_facts, facts, reasoning_traces, distilled_tips, experiences, predictions, etc.)
2. Trust tier distribution (high >=0.8, medium 0.5-0.8, low 0.3-0.5, very_low <0.3)
3. Last created/accessed timestamps
4. DB file size
5. Top categories by count

## Pitfalls

1. **DO NOT use execute_code for this** — triple-quoted SQL with indentation causes SyntaxError/IndentationError. Use `write_file` to create a script, then `terminal` to run it.
2. **DO NOT query `content` or `category` from experiences** — those columns don't exist. Use `action_type` and `lesson`.
3. **DO NOT use `~/subconscious/cerebrum_memory.db`** — it's empty. Use `~/.hermes/cerebrum_memory.db`.
4. **Always clean up temp scripts** after execution.

## Script Template

Write a Python script to `~/subconscious/tmp_consolidate.py`, run it, then `rm` it. The script should use `sqlite3` directly with `Path.home() / ".hermes" / "cerebrum_memory.db"`.

Keep the output brief — this runs as a cron job and delivers to the user.
