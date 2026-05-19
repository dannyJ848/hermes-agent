# Injection Governor V2 — Log Placement Fix

**Date:** May 9, 2026
**Session:** Enhancement Cycle 6, Harness v2.1
**File:** `~/.hermes/plugins/distillation/__init__.py`

## Problem

The `InjectionGovernorV2.log_attempt()` was being called at line ~3706, BEFORE `injection_lines` was defined (it gets defined at line ~3722). This caused:

1. Empty candidate/injected/dropped lists logged to DB
2. `tip_injection_attempts` table stayed at 0 rows despite active injection
3. Governor feedback loop (penalize dropped tips, boost successful tips) never activated

## Root Cause

The cognitive infrastructure V2 hook wiring added the governor log inside the tool router check block (lines 3696-3719), which runs before the injection pipeline collects tips. The `injection_lines` list and `injected_count` variable don't exist yet at that point.

## Fix

**Remove** the early log block (lines 3706-3717):

```python
# REMOVED — This was logging before injection_lines existed:
# gov = get_governor_v2()
# gov.log_attempt(
#     candidate_tips=[t[0] for t in injection_lines],  # ERROR: injection_lines not defined
#     injected_tips=[t[0] for t in injection_lines if t[1] > 0],
#     ...
# )
```

**Add** the log after `final_lines` is assembled (after line ~7041):

```python
# ── Cognitive Infrastructure V2: Governor log injection attempt ──
if _COGNITIVE_INFRA_V2:
    try:
        gov = get_governor_v2()
        gov.turn_number += 1
        for line, priority in injection_lines:
            injected = line in final_lines
            drop_reason = "" if injected else "budget" if len(final_lines) >= _INJECTION_MAX_LINES else "chars" if total_chars >= _INJECTION_MAX_CHARS else "priority"
            gov.log_attempt(
                tip_id=0,  # Session summary marker
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

## Governor Schema

The governor's `log_attempt()` takes per-tip parameters, not batch lists:

```python
def log_attempt(self, tip_id: int, condition: str, priority: int,
                injected: bool, drop_reason: str, chars_used: int, lines_used: int):
```

Table: `tip_injection_attempts` (in `cerebrum_memory.db`)
- `session_id`, `turn_number`, `tip_id`, `tip_condition`, `priority`
- `injected` (0/1), `drop_reason`, `chars_used`, `lines_used`, `created_at`

## Verification

After fix, check DB:
```python
import sqlite3
conn = sqlite3.connect('~/.hermes/cerebrum_memory.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM tip_injection_attempts")
print(f"Rows: {cursor.fetchone()[0]}")  # Should be > 0 after agent LLM turns
conn.close()
```

## Related

- `cognitive_infrastructure_v2.py` — GovernorV2 implementation
- `tool_intelligence_integration.py` — Active routing based on tool success rates
