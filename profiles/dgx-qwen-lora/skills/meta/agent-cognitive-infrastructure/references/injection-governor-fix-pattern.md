# Injection Governor Fix Pattern

## Problem

The `_on_pre_llm_call` hook in `~/.hermes/plugins/distillation/__init__.py` had governor logging at lines 3706-3717 that referenced `injection_lines` before it was populated. This produced no actual log entries — the variables were undefined at that point.

## Root Cause

```python
# BROKEN — at lines 3706-3717 (before injection_lines is defined):
if _COGNITIVE_INFRA_V2:
    try:
        gov = get_governor_v2()
        gov.turn_number += 1
        for line, priority in injection_lines:  # ❌ injection_lines not defined yet
            # ... log attempt ...
    except Exception:
        pass  # ❌ Silently swallows everything
```

## Fix

Move the governor log to AFTER `final_lines` is assembled (line ~7040+):

```python
# CORRECT — after final_lines assembly:
result = "\n".join(final_lines)

# ── Cognitive Infrastructure V2: Governor log injection attempt ──
if _COGNITIVE_INFRA_V2:
    try:
        gov = get_governor_v2()
        gov.turn_number += 1
        for line, priority in injection_lines:
            injected = line in final_lines
            drop_reason = "" if injected else "budget" if len(final_lines) >= _INJECTION_MAX_LINES else "chars" if total_chars >= _INJECTION_MAX_CHARS else "priority"
            gov.log_attempt(
                tip_id=0,
                condition=line[:200],
                priority=priority,
                injected=injected,
                drop_reason=drop_reason,
                chars_used=len(line),
                lines_used=len(final_lines)
            )
    except Exception:
        pass
```

## Verification Steps

1. **Check governor code exists in hook:**
   ```python
   import inspect
   source = inspect.getsource(distillation._on_pre_llm_call)
   assert "Governor log injection attempt" in source
   ```

2. **Verify singleton pattern:**
   ```python
   from cognitive_infrastructure_v2 import get_governor_v2
   gov1 = get_governor_v2()
   gov2 = get_governor_v2()
   assert gov1 is gov2  # Same instance
   ```

3. **Test direct insert:**
   ```python
   gov = get_governor_v2()
   gov.log_attempt(tip_id=42, condition="test", priority=1, injected=True, drop_reason="", chars_used=50, lines_used=1)
   
   import sqlite3
   conn = sqlite3.connect(CEREBRUM_DB)
   c = conn.cursor()
   c.execute("SELECT COUNT(*) FROM tip_injection_attempts")
   assert c.fetchone()[0] > 0
   ```

4. **Check hook returns content (not None):**
   If `_on_pre_llm_call(msg)` returns injection text, `final_lines` was not empty and governor code was reached.

## Common Pitfalls

- **Hook returns early:** If `injection_lines` is empty, hook returns `None` at line 7016-7017 before reaching governor. This is correct — no need to log when nothing was injected.
- **Silent failure:** The `except Exception: pass` at line 7055-7056 swallows ALL errors. Add debug prints during development.
- **Wrong DB path:** Verify `CEREBRUM_DB` in `cognitive_infrastructure_v2.py` matches the DB you're querying.
- **Turn number resets:** `get_governor_v2()` may create new instance if module reloaded. Turn number is cosmetic — DB has the data.
