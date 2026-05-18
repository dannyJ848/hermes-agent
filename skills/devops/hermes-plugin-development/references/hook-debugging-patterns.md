# Hook Debugging Patterns

## Process Isolation Gotcha

`execute_code` runs each call in a **fresh Python process**. The plugin manager singleton (`get_plugin_manager()`) does NOT persist state across separate `execute_code` calls.

### Wrong (will fail)
```python
# Call 1: discovers plugins
execute_code("discover_plugins(force=True)")

# Call 2: hooks are gone — fresh process, fresh singleton
execute_code("get_pre_tool_call_block_message(...)")  # Hooks empty!
```

### Right (single script)
```python
execute_code("""
from hermes_cli.plugins import discover_plugins, get_pre_tool_call_block_message
discover_plugins(force=True)  # Discover in THIS process

# Now hooks are available
for i in range(5):
    block = get_pre_tool_call_block_message(tool_name='web_search', args={'query': 'same'}, session_id='test')
    print(block)
""")
```

## pre_tool_call Block Format

The `get_pre_tool_call_block_message()` function (called by `model_tools.py`) expects this exact dict format:

```python
{"action": "block", "message": "Reason the tool was blocked"}
```

A plain string return will be silently ignored. The function iterates hook results and checks:
```python
for result in hook_results:
    if not isinstance(result, dict):
        continue
    if result.get("action") != "block":
        continue
    message = result.get("message")
    if isinstance(message, str) and message:
        return message
```

## SQLite COUNT(*) Type Safety

In some SQLite configurations, `COUNT(*)` returns a string instead of int. Always coerce:

```python
c.execute("SELECT COUNT(*) FROM table WHERE ...")
count = int(c.fetchone()[0])  # Safe even if already int
```

Without `int()`, you get:
```
TypeError: '>=' not supported between instances of 'str' and 'int'
```

## Hook Registration Verification

To verify your hook is actually registered and callable:

```python
from hermes_cli.plugins import discover_plugins, get_plugin_manager

discover_plugins(force=True)
pm = get_plugin_manager()

# Check hooks dict directly
for name, callbacks in pm._hooks.items():
    if callbacks:
        print(f"{name}: {len(callbacks)} callbacks")
        for cb in callbacks:
            print(f"  - {getattr(cb, '__name__', repr(cb))}")

# Call your hook directly
hooks = pm._hooks.get('pre_tool_call', [])
for cb in hooks:
    result = cb(tool_name='test', args={}, session_id='s', task_id='t')
    print(f"Result: {result}")
```

## Common Error Patterns

| Error | Cause | Fix |
|-------|-------|-----|
| `'NoneType' object has no attribute 'cursor'` | DB connection failed during brain init | Check SQLite path exists; verify imports |
| `unexpected keyword argument 'task_id'` | Hook signature mismatch | Use `**kwargs` + `.get()` extraction |
| `ModuleNotFoundError: 'plugins.X'` | Plugin loaded as module, not package | Use `importlib.util.spec_from_file_location` for direct loading |
| `No module named 'plugins.memory'; 'plugins' is not a package` | `hermes_cli.plugins` shadows `plugins/` directory in `sys.modules` | Pre-import `plugins` package before `hermes_cli.plugins` loads (see below) |
| `Hooks empty after discovery` | Process isolation — called in separate `execute_code` | Single-script test pattern |
| `Plain string return not blocking` | Wrong return format for pre_tool_call | Return `{"action": "block", "message": "..."}` dict |
| `SQLite COUNT(*) type mismatch` | COUNT returns string in some configs | Wrap with `int()`: `count = int(c.fetchone()[0])` |
| `TypeError: '>=' not supported between instances of 'str' and 'int'` | Config values loaded as strings | `self.threshold = int(threshold)` in `__init__` |

## Real-Time Judge Integration

To wire an LLM judge into the plugin for active evaluation (not just configuration):

```python
from hermes_cli.subconscious.llm_judge import LLMJudge

_judge = None

def _get_judge():
    global _judge
    if _judge is None:
        _judge = LLMJudge(model="deepseek-v4-pro")
    return _judge

def post_tool_call_hook(**kwargs):
    """Auto-evaluate tool results with live judge."""
    brain = _get_brain()
    judge = _get_judge()
    
    tool_name = kwargs.get("tool_name", "")
    args = kwargs.get("args", {})
    result = kwargs.get("result", "")
    
    # Run brain analysis
    analysis = brain.after_tool_call(tool_name, args, result, None)
    
    # If brain extracted a lesson, evaluate it with judge
    if analysis.get("lesson"):
        tip = {
            "text": analysis["lesson"],
            "domain": tool_name,
            "confidence": 0.7
        }
        eval_result = judge.evaluate_single(tip)
        if eval_result.get("quality_score", 0.5) < 0.6:
            # Low quality — don't save to database
            return {"success": True, "analyzed": True, "saved": False}
    
    return {"success": True, "analyzed": True, "saved": True}
```

**Key point:** The judge must be instantiated and called, not just configured. `LLMJudge()` creates a live API client that makes real calls to `deepseek-v4-pro`. The `model` parameter defaults to `deepseek-v4-pro` — if you want a different judge, pass it explicitly.

**Cost tracking:** Each `evaluate_single()` call costs ~$0.0002. The judge tracks cumulative cost in `judge.total_cost` and `judge.total_calls`.

## `plugins` Package Shadowing by `hermes_cli.plugins`

**Symptom:** After importing `run_agent.py`, all `plugins.X` imports fail with:
```
Memory provider plugin init failed: No module named 'plugins.memory'; 'plugins' is not a package
Failed to load plugin 'spotify': No module named 'plugins.spotify'; 'plugins' is not a package
```

**Root cause:** When `run_agent.py` imports `hermes_cli.plugins`, Python registers `plugins` in `sys.modules` pointing to `hermes_cli/plugins.py` (a file, NOT a package). This shadows the `plugins/` directory, breaking all `plugins.X` imports.

**Verification:**
```python
import sys
import run_agent  # Triggers the shadowing

print(sys.modules['plugins'].__file__)
# → /path/to/hermes-agent/hermes_cli/plugins.py  (WRONG — should be plugins/__init__.py)
print(hasattr(sys.modules['plugins'], '__path__'))
# → False  (WRONG — should be True for a package)
```

**Fix:** Pre-import the `plugins` package at the top of `run_agent.py` before `hermes_cli.plugins` can shadow it:

```python
# At the very top of run_agent.py, after imports but before any hermes_cli.plugins usage
import importlib
import sys

_plugins_spec = importlib.util.spec_from_file_location(
    "plugins",
    "/path/to/hermes-agent/plugins/__init__.py",
    submodule_search_locations=["/path/to/hermes-agent/plugins"]
)
_plugins_mod = importlib.util.module_from_spec(_plugins_spec)
sys.modules["plugins"] = _plugins_mod
_plugins_spec.loader.exec_module(_plugins_mod)
```

**Why this works:** By explicitly creating the `plugins` package module and inserting it into `sys.modules` before `hermes_cli.plugins` is imported, Python's module resolution finds the correct package first. Subsequent `import hermes_cli.plugins` creates a separate `hermes_cli.plugins` entry without overwriting `plugins`.

**After fix:**
```python
import run_agent
print(sys.modules['plugins'].__file__)
# → /path/to/hermes-agent/plugins/__init__.py  (CORRECT)
print(hasattr(sys.modules['plugins'], '__path__'))
# → True  (CORRECT)
```

**Impact:** This fixes memory provider initialization, plugin loading, and any other code that relies on `plugins.X` imports. The fix is required for full cognitive orchestrator initialization (20/20 subsystems) on DGX Spark and other deployments where `run_agent.py` is imported directly.