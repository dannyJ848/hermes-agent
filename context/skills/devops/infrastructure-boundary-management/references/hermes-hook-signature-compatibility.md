# Hermes Hook Signature Compatibility

**Session:** 2026-05-09  
**Context:** Wiring cognitive systems into `~/.hermes/plugins/distillation/__init__.py`

## The Problem

Hermes core's `invoke_hook()` passes keyword arguments that may not match the plugin hook's expected signature. When a mismatch occurs, Python raises `TypeError`, which is silently swallowed by `invoke_hook`'s try/except. The hook **appears registered but NEVER FIRES**.

**Real example from this session:**
```python
# Core passes these kwargs:
invoke_hook("post_tool_call",
    tool_name="execute_code",
    args={...},
    result={...},
    task_id="...",
    session_id="...",
    tool_call_id="...",
    duration_ms=1234,
)

# Plugin hook that FAILS (silently):
def _on_post_tool_call(tool_name, args, result, status="", error=""):
    # TypeError: unexpected keyword argument 'task_id'
    # → Hook never fires, no error logged

# Plugin hook that WORKS:
def _on_post_tool_call(tool_name, args, result, status="", error="", **kwargs):
    # **kwargs absorbs task_id, session_id, tool_call_id, duration_ms
    # → Hook fires correctly
```

## The Fix Pattern

**Every hook function MUST use `**kwargs` and make all params optional with defaults:**

```python
def _on_pre_llm_call(user_message: str, context: dict = None, **kwargs) -> Optional[str]:
    """Pre-LLM-call: inject relevant tips."""
    # kwargs may contain: session_id, conversation_history, is_first_turn, model, platform, sender_id
    pass

def _on_post_tool_call(tool_name: str, args: dict, result: Any,
                       status: str = "", error: str = "", **kwargs) -> Optional[dict]:
    """Post-tool-call: extract tips from outcomes."""
    # kwargs may contain: task_id, session_id, tool_call_id, duration_ms
    pass

def _on_session_end(session_id: str = "", tool_calls: list = None, **kwargs) -> Optional[dict]:
    """Session end: cleanup and extraction."""
    # kwargs may contain: completed, interrupted, model, platform
    pass
```

## Deriving Status from Result

The core's `invoke_hook` for `post_tool_call` does NOT pass `status` or `error` in all code paths. The plugin must derive status from the result dict:

```python
# Derive status from result if not provided
if not status and result:
    result_str = str(result).lower()
    if '"error"' in result_str or 'error:' in result_str or result_str.startswith('error'):
        status = "error"
    else:
        status = "success"
elif not status:
    status = "success"
```

## Hook Registration in Plugin `__init__.py`

```python
# At module level, register hooks
def register_hooks(ctx):
    ctx.register_hook("pre_llm_call", _on_pre_llm_call)
    ctx.register_hook("post_tool_call", _on_post_tool_call)
    ctx.register_hook("on_session_end", _on_session_end)  # if core supports it
```

## Verification

After adding a new hook or modifying signatures:

```bash
# 1. Syntax check
python3 -c "import py_compile; py_compile.compile('/Users/dannygomez/.hermes/plugins/distillation/__init__.py', doraise=True)"

# 2. Import test
cd ~/.hermes/plugins/distillation && python3 -c "import __init__ as d; print('Hooks:', hasattr(d, '_on_pre_llm_call'), hasattr(d, '_on_post_tool_call'), hasattr(d, '_on_session_end'))"

# 3. Live test: make a tool call and check if data appears in DB tables
```

## Core Hook Invocation Points

| Hook | File | Line | Args Passed |
|------|------|------|-------------|
| `pre_llm_call` | `run_agent.py` | ~11406 | session_id, user_message, conversation_history, is_first_turn, model, platform, sender_id |
| `post_tool_call` | `model_tools.py` | ~775 | tool_name, args, result, task_id, session_id, tool_call_id, duration_ms |
| `on_session_end` | `cli.py` | ~12267 | session_id, completed, interrupted, model, platform |
| `on_session_finalize` | `cli.py` | ~703 | session_id, platform |

## Files Modified in This Session

- `~/.hermes/plugins/distillation/__init__.py` — 4 patches adding `**kwargs` to hooks and wiring cognitive systems
