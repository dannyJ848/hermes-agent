---
name: background-maintenance-integration
version: 1.0
created: 2026-04-30
description: |
  Integrate background maintenance/curation systems (skill curators, memory cleaners,
  model refreshers) into the agent's active iteration loop, not just idle cron.
  Covers: dual-path triggering (cron + per-turn), activity-aware context feeding,
  auto-tracking of created artifacts, and validation via fake-state testing.
triggers:
  - When a background system (curator, cleaner, archiver) exists but only runs on cron/idle
  - When the user wants maintenance to happen during active sessions, not just when idle
  - After merging upstream features that are wired to gateway cron but not the agent loop
  - When skill/memory/model maintenance needs to be context-aware (use recent activity)
---

# Background Maintenance Integration

## Problem Class

You have a background maintenance system (e.g., Hermes Curator for skill review,
memory cleaner for stale entries, model refresher for updated weights) that:
- Is fully operational on gateway cron (runs when idle, every N hours/days)
- Has zero integration with the agent's active iteration loop
- Never sees the agent's current activity context (what tools were used, what errors occurred)
- Cannot react to session-level events (skill creation, repeated errors)

This creates a blind spot: maintenance only happens when the agent is idle, missing
opportunities to clean up or curate based on live session data.

## The Dual-Path Integration Pattern

### Path A: Gateway Cron (existing, backup)
- Runs when `idle_for_seconds > threshold` AND `time_since_last_run > interval`
- Good for: heavy operations (full skill sweep, LLM review, cross-session analysis)
- Bad for: reacting to live session events

### Path B: Iteration Pipeline (new, contextual)
- Runs every N turns during active sessions
- Receives: tool usage history, error patterns, recently created skills
- Good for: lightweight maintenance (mark skills used, note error correlations,
  queue items for full cron review)
- Bad for: heavy operations (LLM calls, large DB scans)

## Integration Steps

### Step 1: Create a Shim Module

Create `agent/<feature>_integration.py` that bridges the maintenance system
and the agent loop:

```python
"""Integration shim for <Feature> into the iteration pipeline."""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)
FEATURE_TURN_INTERVAL = 50  # Run every N turns during active sessions


def maybe_run_<feature>_in_iteration(
    turn_count: int,
    tool_usage_history: list,
    error_history: list,
    force: bool = False,
) -> Optional[Dict[str, Any]]:
    """Best-effort trigger from the iteration pipeline."""
    if not force and turn_count % FEATURE_TURN_INTERVAL != 0:
        return None
    
    try:
        from agent.<feature> import maybe_run_<feature>
        activity_summary = _build_activity_summary(tool_usage_history, error_history)
        # Pass activity context to the maintenance system
        result = maybe_run_<feature>(
            idle_for_seconds=float("inf"),  # We're in pipeline, not waiting
            on_summary=lambda msg: logger.info("<feature>[iteration]: %s", msg),
        )
        return result
    except Exception as e:
        logger.debug("<feature> iteration hook failed: %s", e)
        return None


def _build_activity_summary(tool_history: list, error_history: list) -> str:
    """Summarize recent activity for maintenance context."""
    parts = []
    if tool_history:
        from collections import Counter
        tool_counts = Counter(t.get("tool_name", "unknown") for t in tool_history[-20:])
        parts.append(f"Recent tools: {', '.join(f'{n}({c})' for n,c in tool_counts.most_common(5))}")
    if error_history:
        from collections import Counter
        error_counts = Counter(e.get("error_type", "unknown") for e in error_history[-10:])
        parts.append(f"Recent errors: {', '.join(f'{n}({c})' for n,c in error_counts.most_common(3))}")
    return " | ".join(parts) if parts else "No recent activity"


def record_<artifact>_creation(artifact_name: str, trigger: str, quality_score: float = 0.5):
    """Record that an artifact was created by the agent."""
    try:
        from agent.cortex_learning import get_learning_engine
        engine = get_learning_engine()
        engine.store.save_memory_unit(
            content=f"Agent-created <artifact>: {artifact_name} (trigger: {trigger}, quality: {quality_score})",
            memory_type="agent_<artifact>",
            source="iteration_pipeline",
            confidence=quality_score,
        )
    except Exception as e:
        logger.debug("Failed to record <artifact> creation: %s", e)
```

### Step 2: Wire into the Agent Turn Loop

In `run_agent.py`, find the turn counter increment and add the integration hook:

```python
# In the main conversation loop, after turn counter increments:
self._turn_counter = getattr(self, '_turn_counter', 0) + 1

# --- <FEATURE> INTEGRATION ---
try:
    from agent.<feature>_integration import maybe_run_<feature>_in_iteration
    _tool_history = getattr(self, '_recent_tools_used', [])
    _error_history = getattr(self, '_error_history', [])
    maybe_run_<feature>_in_iteration(
        turn_count=self._turn_counter,
        tool_usage_history=_tool_history,
        error_history=_error_history,
    )
except Exception:
    pass
# --- END <FEATURE> INTEGRATION ---
```

### Step 3: Track Artifact Creation

When the agent creates artifacts that the maintenance system should know about,
add tracking in the tool call handler:

```python
# In run_agent.py tool call loop:
if function_name == "<artifact_manage>":
    try:
        _args = json.loads(tool_call.function.arguments)
        if isinstance(_args, dict) and _args.get("action") in ("create", "write_file"):
            artifact_name = _args.get("name", "unknown")
            from agent.<feature>_integration import record_<artifact>_creation
            record_<artifact>_creation(
                artifact_name=artifact_name,
                trigger="agent_tool_call",
                quality_score=0.7,
            )
    except Exception:
        pass
```

### Step 4: Track Session Errors

Build `_error_history` when errors occur so the maintenance system sees patterns:

```python
# In error handling block:
error_info = engine.on_error(error_text=str(tool_error), context=..., session_id=...)

# Track for maintenance integration
if not hasattr(self, '_error_history'):
    self._error_history = []
self._error_history.append({
    "error_type": error_info.get('error_type', 'unknown'),
    "tool_name": function_name,
    "timestamp": time.time(),
    "is_known": error_info.get('is_known', False),
})
```

### Step 5: Validate with Fake State

Before declaring the integration works, verify the trigger logic:

```python
# Write fake state showing last run was 8 days ago
from pathlib import Path
import json
from datetime import datetime, timezone, timedelta

state_file = Path.home() / '.hermes' / 'skills' / '.<feature>_state'
state_file.parent.mkdir(parents=True, exist_ok=True)
old_run = datetime.now(timezone.utc) - timedelta(days=8)
json.dump({'last_run_at': old_run.isoformat(), 'paused': False}, state_file.open('w'))

# Test should_run_now()
python3.12 -c "from agent.<feature> import should_run_now; print(should_run_now())"  # → True

# CLEAN UP after test
state_file.unlink()
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Turn interval = 50** | Balance between responsiveness and overhead. Heavy maintenance (LLM review) should still happen on cron. |
| **Activity summary, not raw data** | Pass a text summary to the maintenance system, not full arrays. Keeps the interface simple. |
| **Auto-track artifact creation** | Maintenance systems need to know what exists to curate. Hook into the tool that creates artifacts. |
| **Error history capped** | `_error_history` grows per session. Cap at ~20 entries to avoid unbounded growth. |
| **try/except: pass** | The integration must never crash the agent loop. All hooks are best-effort. |
| **force parameter** | Allows manual triggering for testing or urgent maintenance. |

## Common Pitfalls

1. **Import order bug**: The shim module imports `agent.<feature>` at call time (lazy), not at module load. This avoids circular imports if the feature imports from run_agent.py.

2. **function_args parsed after check**: In the tool call loop, `function_args` is parsed from JSON AFTER the `function_name` check. If you read `function_args` before `json.loads()`, it's undefined. Parse twice or restructure:
   ```python
   # CORRECT: parse first, then check
   _args = json.loads(tool_call.function.arguments)
   if function_name == "skill_manage" and _args.get("action") == "create":
       ...
   ```

3. **Missing `_error_history` initialization**: If the first error occurs before any code initializes `_error_history`, `getattr(self, '_error_history', [])` returns a new empty list each time. Use `hasattr` + explicit initialization:
   ```python
   if not hasattr(self, '_error_history'):
       self._error_history = []
   ```

4. **Curator runs unexpectedly during smoke test**: If `maybe_run_curator()` gets called with a fake state file, it may actually execute auto-transitions. The fake state test should be followed by immediate cleanup.

5. **Activity summary builds but isn't passed**: The `_build_activity_summary()` function exists but the result isn't fed into `maybe_run_<feature>()`. Verify the maintenance system accepts an `activity_context` or similar parameter, or log the summary before calling.

## Verification Checklist

- [ ] Shim module imports cleanly
- [ ] Integration hook runs every N turns (test with `turn_count % N == 0`)
- [ ] Artifact creation is recorded when the create tool is called
- [ ] Error history accumulates across the session
- [ ] Fake state test confirms trigger logic
- [ ] Full smoke test: all modules load, latency < 50ms combined
- [ ] Clean up fake state after validation
- [ ] Gateway cron still works as backup path

## Files Created/Modified

| File | Purpose |
|------|---------|
| `agent/<feature>_integration.py` | New shim module (bridge between maintenance system and agent loop) |
| `run_agent.py` | Add integration hook after turn counter increment |
| `run_agent.py` | Add artifact creation tracking in tool call loop |
| `run_agent.py` | Add error history accumulation in error handling block |

## Example: Hermes Curator Integration

The curator was originally a gateway-level cron task (runs every 7 days when idle).
After integration:
- **Cron path**: Still runs every 7 days, does full LLM review of all agent-created skills
- **Iteration path**: Runs every 50 turns, records skill creation events, feeds activity summary
- **Result**: Curator knows about skills created during active sessions and can prioritize them for the next full review

Smoke test output:
```
Turn 50: CURATOR REVIEW TRIGGERED
Total learning overhead (52 turns): 159.9ms
Average per turn: 3.08ms (budget: <50ms)
Curator status: enabled=True, run_count=1, last_summary="auto: no changes"
```
