# Iteration Engine Wiring into run_agent.py

## Context

The `agent/iteration_engine.py` module (671 lines, class `IterationEngine`) provides experiential learning — it records tool execution outcomes and warns before repeating known-failing actions.

## Integration Points

### 1. Import (run_agent.py ~line 159)

```python
from agent.iteration_engine import IterationEngine, get_engine as _get_iteration_engine
```

### 2. Initialization (run_agent.py ~line 2116, in AIAgent.__init__)

```python
# After subconscious plugin loader
self.iteration_engine = _get_iteration_engine()
```

### 3. Pre-action Hook — Concurrent Path (_invoke_tool ~line 10044)

```python
# ── Iteration Engine: pre-action lookup ────────────────────────────
_iteration_context = None
if hasattr(self, "iteration_engine") and self.iteration_engine:
    try:
        _iteration_context = self.iteration_engine.before_action(
            action_type=function_name,
            detail=json.dumps(function_args, ensure_ascii=False)[:200],
        )
    except Exception:
        pass
```

### 4. Post-action Hook — Concurrent Path (_invoke_tool ~line 10134)

```python
# ── Iteration Engine: post-action capture ──────────────────────────
if hasattr(self, "iteration_engine") and self.iteration_engine:
    try:
        _tool_end = _time.time()
        _is_error = "error" in result.lower() or result.startswith("Error")
        self.iteration_engine.after_action(
            action_type=function_name,
            detail=json.dumps(function_args, ensure_ascii=False)[:200],
            result="failure" if _is_error else "success",
            error=result[:500] if _is_error else "",
            speed_ms=int((_tool_end - _tool_start_time) * 1000),
        )
    except Exception:
        pass
```

### 5. Pre-action Hook — Sequential Path (_execute_tool_calls_sequential ~line 10679)

Same pattern as concurrent path, but inside the sequential execution loop.

### 6. Post-action Hook — Sequential Path (_execute_tool_calls_sequential ~line 10931)

Same pattern as concurrent path, with `_is_error_result` check instead of string parsing.

## API Reference

### before_action(action_type: str, detail: str = "", extra: str = "") -> Dict

Returns a context dictionary with:
- `action_hash`: str — SHA256 hash of action shape
- `warnings`: List[Dict] — past failures for this action type
- `proven_approaches`: List[Dict] — past successes
- `has_history`: bool — whether we've seen this action before
- `past_failure_count`: int
- `past_success_count`: int
- `confidence`: float — 0.0 to 1.0 prediction confidence
- `skill_candidate`: bool — True if confidence > 0.70 and successes >= 2

### after_action(action_type: str, detail: str = "", result: str = "unknown", error: str = "", lesson: str = "", approach: str = "", fix_command: str = "", speed_ms: int = 0, extra: str = "", context_tags: str = "") -> Dict

Records the experience. Key params:
- `result`: "success" | "failure" | "partial"
- `error`: raw error output (pattern extracted automatically)
- `speed_ms`: execution time in milliseconds

## Common Pitfalls

1. **Wrong parameter name**: Use `detail` not `action_detail`
2. **Wrong return type**: Returns `Dict` not `str`
3. **Error detection**: Must parse result string for "error" or "Error" prefix
4. **Timing**: Use `_time.time()` at method entry and exit for `speed_ms`

## Verification

```python
from run_agent import AIAgent
agent = AIAgent(model='anthropic/claude-sonnet-4', provider='anthropic', quiet_mode=True, skip_memory=True)

# Check initialization
assert hasattr(agent, 'iteration_engine')
assert agent.iteration_engine is not None

# Test before_action
ctx = agent.iteration_engine.before_action(action_type='web_search', detail='{"query": "test"}')
assert 'confidence' in ctx
assert 'warnings' in ctx

# Test after_action
agent.iteration_engine.after_action(
    action_type='web_search',
    detail='{"query": "test"}',
    result='success',
    speed_ms=100,
)
print("✓ Iteration engine fully operational")
```
