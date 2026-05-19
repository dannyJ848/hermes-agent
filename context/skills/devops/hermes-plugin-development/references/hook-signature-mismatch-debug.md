# Hook Signature Mismatch — Silent Failure Debug Recipe

## Symptom
- Plugin registers successfully (`hermes plugins list` shows it enabled)
- Hooks appear registered (plugin manifest lists them)
- Hook callback NEVER FIRES — no logs, no traces, no observable effect
- No error visible even with verbose logging

## Root Cause
`invoke_hook()` in `hermes_cli/plugins.py` wraps each callback in try/except:

```python
for cb in callbacks:
    try:
        ret = cb(**kwargs)
    except Exception as exc:
        logger.warning("Hook '%s' callback %s raised: %s", ...)
```

When the hook signature doesn't match the kwargs passed by the core, Python raises `TypeError` (missing required argument, unexpected keyword argument). This is caught and logged at WARNING level — but if the logger isn't configured to show warnings, or if the log is buried in output, it appears as complete silence.

## Detection

### Method 1: Check `invoke_hook` call site
Read `model_tools.py` (or wherever `invoke_hook` is called for your hook):

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

Compare with your hook signature:
```python
def _on_post_tool_call(tool_name: str, args: dict, result: Any,
                        status: str, error: str = "") -> None:
```

**Mismatch**: core passes `duration_ms`, plugin expects `status` and `error`.

### Method 2: Add **kwargs and log
Change signature to accept everything:
```python
def _on_post_tool_call(tool_name: str, args: dict, result: Any,
                        status: str = "", error: str = "", **kwargs) -> None:
    logger.info(f"[hook] {tool_name} | kwargs={list(kwargs.keys())}")
```

If the log appears, the hook IS firing but was failing silently before.

### Method 3: Direct plugin manager test
```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
from hermes_cli.plugins import get_plugin_manager, invoke_hook
pm = get_plugin_manager()
pm.discover_and_load(force=True)

# Check if your plugin loaded
for p in pm.list_plugins():
    if 'your-plugin' in p['name']:
        print(f'{p[\"name\"]}: hooks={p[\"hooks\"]}')

# Check registered callbacks
for hook_name, callbacks in pm._hooks.items():
    print(f'{hook_name}: {len(callbacks)} callbacks')
    for cb in callbacks:
        print(f'  - {getattr(cb, \"__name__\", repr(cb))}')

# Fire the hook manually
results = invoke_hook('post_tool_call', tool_name='test', args={}, result='test')
print(f'Results: {results}')
"
```

## Fix

Add `**kwargs` to ALL hook signatures, make previously-required params optional with defaults:

```python
# BEFORE (silent failure)
def _on_post_tool_call(tool_name: str, args: dict, result: Any,
                        status: str, error: str = "") -> None:

# AFTER (works)
def _on_post_tool_call(tool_name: str, args: dict, result: Any,
                        status: str = "", error: str = "", **kwargs) -> None:
    # Derive status from result if not provided by core
    if not status and result:
        result_str = str(result).lower()
        if '"error"' in result_str or 'error:' in result_str:
            status = "error"
        else:
            status = "success"
```

Apply to ALL hooks in your plugin:
- `_on_pre_tool_call(tool_name, args)` → `_on_pre_tool_call(tool_name, args, **kwargs)`
- `_on_pre_llm_call(user_message, context=None)` → `_on_pre_llm_call(user_message, context=None, **kwargs)`
- `_on_post_api_request(model_name, usage, response, latency_ms)` → `_on_post_api_request(model_name, usage, response, latency_ms=0, **kwargs)`

## Prevention

**Template for all hook functions:**
```python
def _on_any_hook(required_arg: str, optional_arg: dict = None, **kwargs) -> None:
    """Always accept **kwargs for forward compatibility."""
    # Extract extras if needed
    task_id = kwargs.get('task_id', '')
    session_id = kwargs.get('session_id', '')
    duration_ms = kwargs.get('duration_ms', 0)
    ...
```

## Files Involved
- `hermes_cli/plugins.py:1130-1164` — `invoke_hook()` implementation
- `hermes_cli/model_tools.py:773-786` — `post_tool_call` invocation site
- `hermes_cli/plugins.py:1247-1310` — `pre_tool_call` invocation site
- Your plugin's `__init__.py` — hook function definitions
