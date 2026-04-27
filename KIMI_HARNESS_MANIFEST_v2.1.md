# KIMI HARNESS ENHANCEMENT MANIFEST v2.1
## Error Pattern Learning System

**Date:** 2026-04-26
**Status:** DEPLOYED

---

## WHAT CHANGED FROM v2.0

v2.0 learned from successful memory injection.
v2.1 learns from **failures** — errors I make and how to fix them.

---

## ARCHITECTURE

### Layer 1: Error Fingerprinting
- Normalizes errors (removes paths, UUIDs, timestamps, numbers)
- Creates stable hash to detect the same error pattern
- Classifies errors by type (syntax, network, permission, docker, etc.)

### Layer 2: Pattern Storage (Cortex)
- `error_patterns` table: Stores unique error patterns with metadata
- `error_occurrences` table: Logs each occurrence with resolution attempt
- Tracks: occurrence_count, resolution, success_rate

### Layer 3: Real-time Feedback
- When a tool fails, the error is fingerprinted and checked against known patterns
- If known: Appends the known resolution to the error message
- If new: Records it for future learning

### Layer 4: Preemptive Warnings
- Before executing actions, checks if similar actions caused errors before
- Warns the model proactively

---

## SCHEMA

```sql
CREATE TABLE error_patterns (
    id UUID PRIMARY KEY,
    fingerprint TEXT UNIQUE NOT NULL,
    error_type TEXT,
    error_summary TEXT,
    context TEXT,
    resolution TEXT,
    resolution_success_rate FLOAT DEFAULT 0.0,
    occurrence_count INTEGER DEFAULT 1,
    last_occurred TIMESTAMP,
    first_occurred TIMESTAMP,
    metadata JSONB
);

CREATE TABLE error_occurrences (
    id UUID PRIMARY KEY,
    pattern_id UUID REFERENCES error_patterns,
    session_id TEXT,
    full_error TEXT,
    resolution_attempted TEXT,
    resolution_successful BOOLEAN,
    timestamp TIMESTAMP
);
```

---

## FILES

### New
- `agent/error_learning.py` — Error learning engine

### Modified
- `run_agent.py` — Added error learning hook in `_execute_tool_calls_concurrent`

---

## HOW IT WORKS

1. **Tool fails** → Error is caught in `_execute_tool_calls_concurrent`
2. **Fingerprint** → Normalize and hash the error
3. **Check known** → Query Cortex for matching pattern
4. **If known** → Append resolution hint to error message
5. **Record** → Log occurrence in `error_occurrences`
6. **On fix** → Update `resolution` and `success_rate` in `error_patterns`

---

## EXAMPLE FLOW

```
[Tool fails with psycopg2 error]
  ↓
[ErrorLearningEngine.on_error()]
  ↓
[Check: Has this happened before?]
  ↓
[YES — 2 previous occurrences]
  ↓
[Append to error message:]
"[LEARNED: This error has occurred 2 times before. 
  Known resolution: Use ARRAY['skill']::varchar[]]"
  ↓
[Model sees hint and applies fix]
  ↓
[Record resolution success]
  ↓
[Future occurrences get the hint immediately]
```

---

## EXPECTED IMPACT

- **First occurrence**: Normal error, no help
- **Second occurrence**: "This has happened before" warning
- **Third+ occurrence**: Known resolution appended automatically
- **Over time**: Common errors become self-healing

---

## FUTURE ENHANCEMENTS

1. **Auto-retry with fix** — Automatically apply known resolutions
2. **Resolution ranking** — Multiple resolutions ranked by success rate
3. **Contextual fixes** — Different fixes for same error in different contexts
4. **Error prevention** — Pre-emptive warnings before executing risky actions
5. **Cross-session learning** — Errors from one session help in future sessions

---

## TESTING

```python
from agent.error_learning import get_error_engine
engine = get_error_engine()

# Record an error
info = engine.on_error("ImportError: No module named 'foo'")
print(f"Pattern: {info['pattern_id']}, Repeat: {info['is_repeat']}")

# Check stats
stats = engine.store.get_error_stats()
print(f"Total patterns: {stats['total_patterns']}")

# Get top errors
top = engine.store.get_top_errors(5)
for e in top:
    print(f"{e['occurrences']}x | {e['error_type']} | {e['summary'][:50]}")
```
