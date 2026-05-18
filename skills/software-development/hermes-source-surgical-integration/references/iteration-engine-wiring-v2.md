# Iteration Engine Wiring into run_agent.py — May 9, 2026

## Context

The `agent/iteration_engine.py` module (671 lines, class `IterationEngine`) was already present in the codebase but was **NOT wired into the agent loop**. It needed to be integrated into both concurrent and sequential tool execution paths.

## Changes Made to run_agent.py

### 1. Import added (line ~159)
```python
from agent.iteration_engine import IterationEngine, get_engine as _get_iteration_engine
```

### 2. Initialization (line ~2116)
After subconscious plugin loader:
```python
self.iteration_engine = _get_iteration_engine()
```

### 3. Pre-action hooks

**In `_invoke_tool` (concurrent path, line ~10046):**
```python
# Iteration engine pre-action hook
if hasattr(self, 'iteration_engine') and self.iteration_engine:
    try:
        self.iteration_engine.before_action(
            action_type=fn,
            action_detail=json.dumps(args)[:200]
        )
    except Exception:
        pass  # Don't let iteration engine break tool execution
```

**In `_execute_tool_calls_sequential` (sequential path, line ~10679):**
Same pattern as above.

### 4. Post-action hooks

**In `_invoke_tool` (line ~10133):**
```python
# Iteration engine post-action hook
if hasattr(self, 'iteration_engine') and self.iteration_engine:
    try:
        self.iteration_engine.after_action(
            action_type=fn,
            action_detail=json.dumps(args)[:200],
            result=str(result)[:500] if result else "",
            success=not error,
            speed_ms=int((_tool_end_time - _tool_start_time) * 1000) if '_tool_start_time' in dir() else 0
        )
    except Exception:
        pass
```

**In `_execute_tool_calls_sequential` (line ~10930):**
Same pattern.

### 5. Timing capture

Added timing in `_invoke_tool`:
```python
import time as _time
_tool_start_time = _time.time()
# ... tool execution ...
_tool_end_time = _time.time()
```

## Critical Pitfall: ContextCompressor Overwrite

During the wiring process, `agent/context_compressor.py` was accidentally replaced with a minimal `AdaptiveCompressor` class (104 lines) that was missing 17+ methods called by `run_agent.py`:

Missing methods included:
- `update_model`
- `on_session_start`
- `on_session_end`
- `on_session_reset`
- `get_tool_schemas`
- `handle_tool_call`
- `context_length`
- `threshold_percent`
- `protect_first_n`
- `protect_last_n`
- `compression_count`
- `last_prompt_tokens`
- `last_completion_tokens`
- `update_from_response`
- `_context_probed`
- `_context_probe_persistable`

**Recovery:** Extract original from git:
```bash
git show 28a364845:agent/context_compressor.py > /tmp/context_compressor_original.py
# Then restore to agent/context_compressor.py
```

## Verification

After wiring, verify with:
```python
from run_agent import AIAgent
agent = AIAgent(model='anthropic/claude-sonnet-4', provider='anthropic', quiet_mode=True, skip_memory=True)
assert hasattr(agent, 'iteration_engine')
assert agent.iteration_engine is not None
print("✓ Iteration engine wired successfully")
```

## Key Lesson

Always verify the actual method signatures before wiring hooks. The iteration engine's `before_action` returns a Dict with specific keys (`action_hash`, `warnings`, `proven_approaches`, etc.), not a string as might be assumed.
