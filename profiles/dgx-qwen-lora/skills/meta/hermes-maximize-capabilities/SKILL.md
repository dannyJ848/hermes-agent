---
name: hermes-maximize-capabilities
description: Pattern for rapidly building new tools into Hermes Agent to maximize capabilities. Covers tool registration, testing, and integration.
---

# Hermes Capability Maximization Pattern

When Danny green-lights building anything into Hermes, follow this proven workflow.

## Tool Architecture

Every Hermes tool is a Python module in `tools/` that:

1. Imports `registry` from `tools.registry`
2. Defines a schema dict (OpenAI function-calling format)
3. Defines a handler function
4. Calls `registry.register()` at module level

```python
from tools.registry import registry, tool_error

MY_SCHEMA = {
    "name": "my_tool",
    "description": "What it does and when to use it.",
    "parameters": {
        "type": "object",
        "properties": { ... },
        "required": ["param1"]
    }
}

def my_handler(param1: str) -> dict:
    try:
        # ... do work ...
        return {"success": True, "result": ...}
    except Exception as e:
        return tool_error(str(e))

registry.register(
    name="my_tool",
    toolset="file",  # or web, meta, etc.
    schema=MY_SCHEMA,
    handler=lambda args, **kw: my_handler(**args),
    check_fn=lambda: (True, ""),
    emoji="🚀",
)
```

## Registration & Discovery

- `registry.register()` stores the tool in `registry._tools`
- `discover_builtin_tools()` auto-imports all `tools/*_tool.py` files
- Tools are discovered when Hermes starts or when `importlib.reload()` is called
- Test registration: `registry._tools.get('my_tool')` should return a ToolEntry

## Testing Pattern

```bash
cd /Users/dannygomez/hermes-agent
source venv/bin/activate
python -c "
from tools.my_tool import my_handler
result = my_handler('test')
print(result)
"
```

For file-based tools, test against real temp files:
```python
from pathlib import Path
p = Path('/tmp/test.txt')
p.write_text('hello')
# ... test tool ...
```

## Critical Pitfalls

1. **Syntax in multi-line strings**: When embedding JS/CSS inside Python strings, use raw strings or escape braces carefully. Triple-quoted strings with `{{` and `}}` for JSON inside JS work best.

2. **Escape-drift guard**: The existing `fuzzy_find_and_replace` has an escape-drift detector. When `strategy_name != "exact"`, it checks if new_string contains `\'` or `\"` that weren't in the original. This can reject legitimate replacements.

3. **Module-level registration**: `registry.register()` must be at module level (not inside a function) so `discover_builtin_tools()` finds it.

4. **Toolset assignment**: Use `"file"` for filesystem ops, `"web"` for network, `"meta"` for self-management. This affects which toolsets include the tool.

## Quick Wins Reference

| Tool | Problem Solved | Complexity |
|------|---------------|------------|
| `verify` | Silent edit failures | Low |
| `structural_edit` | Patch fails on complex code | Medium |
| `deep_scrape` | JS-rendered sites return empty | Low |
| `context_snapshot` | Verbatim state lost in compression | Low |
| `self_eval` | Quality degradation undetected | Low |

## delegate_tool.py Fallback Pattern

To add provider fallback on rate limits:

1. Wrap `child.run_conversation()` in a retry loop
2. Catch exceptions, check for rate limit keywords
3. Swap `child.provider` to next in `parent_agent.providers_order`
4. Re-submit with `ThreadPoolExecutor(max_workers=1)`
5. Track `_fallback_attempts` and include in error response

Rate limit keywords: `rate limit`, `429`, `resource_exhausted`, `too many requests`, `quota exceeded`, `capacity exceeded`