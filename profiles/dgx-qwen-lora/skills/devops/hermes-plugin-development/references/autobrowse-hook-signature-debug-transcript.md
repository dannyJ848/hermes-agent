# Autobrowse Hook Signature Mismatch — Full Debug Transcript

## Session: 2026-05-09
## Context: User asked to debug why autobrowse pipeline wasn't capturing real tool calls

### Symptom
- Autobrowse modules (tracer, analyzer, synthesizer, graduator) fully built and tested in isolation
- Pipeline worked perfectly with simulated calls: 25 calls → 2 patterns → 2 tips
- But in real Hermes sessions, zero traces captured — `_ab_tracer.get_stats()` always showed `{"total": 0}`

### Investigation Steps

1. **Verified tracer works standalone** — `get_instance('default').record_call()` + `get_stats()` confirmed tracer records correctly
2. **Checked plugin registration** — `ctx.register_hook("post_tool_call", _on_post_tool_call)` present in `register()` function
3. **Checked plugin loading** — `hermes plugins list` showed distillation plugin as `enabled`
4. **Checked hook invocation in core** — `grep invoke_hook model_tools.py` confirmed `invoke_hook("post_tool_call", ...)` IS called after every tool execution
5. **The trap**: `invoke_hook` wraps each callback in try/except and logs at debug level only. Errors are invisible.

### Root Cause

`invoke_hook` in `model_tools.py` passes these kwargs to `post_tool_call`:
```python
invoke_hook(
    "post_tool_call",
    tool_name=function_name,
    args=function_args,
    result=result,
    task_id=task_id or "",
    session_id=session_id or "",
    tool_call_id=tool_call_id or "",
    duration_ms=duration_ms,
)
```

But `_on_post_tool_call` expected:
```python
def _on_post_tool_call(tool_name: str, args: dict, result: Any,
                        status: str, error: str = "") -> Optional[dict]:
```

Python raised `TypeError: _on_post_tool_call() missing 1 required positional argument: 'status'` on EVERY tool call. The error was caught by `invoke_hook`'s try/except and logged at debug level — invisible.

### Fix Applied

All 4 hooks in `~/.hermes/plugins/distillation/__init__.py`:

```python
# BEFORE (broken)
def _on_post_tool_call(tool_name: str, args: dict, result: Any,
                        status: str, error: str = "") -> Optional[dict]:

# AFTER (fixed)
def _on_post_tool_call(tool_name: str, args: dict, result: Any,
                        status: str = "", error: str = "", **kwargs) -> Optional[dict]:
```

Plus status derivation logic:
```python
if not status and result:
    result_str = str(result).lower()
    if '"error"' in result_str or 'error:' in result_str or result_str.startswith('error'):
        status = "error"
    else:
        status = "success"
elif not status:
    status = "success"
```

### Verification

Live test after fix: 25 simulated calls → 14 patterns detected → 14 tips generated → strategy.md updated.

### Key Lesson

When a Hermes plugin hook appears registered but never fires, the FIRST thing to check is signature compatibility. Add `**kwargs` defensively to ALL hook callbacks, and derive missing parameters from available data.
