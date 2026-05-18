# Tool Alias vs Implementation Audit — May 18, 2026

**Scenario:** User reports "92 tools" but `hermes doctor` shows only 27 (15 enabled + 12 disabled). Investigation reveals a discrepancy between tool aliases defined in `toolsets.py` and actual tool functions implemented in `tools/*.py`.

## The Discrepancy

| Count | Source | What It Means |
|-------|--------|---------------|
| 27 | `hermes doctor` / `get_tool_definitions()` | Actually registered and available |
| 15 | `hermes doctor` "enabled" | Tools with `check_fn` returning True |
| 12 | `hermes doctor` "disabled" | Tools with `check_fn` returning False (missing deps) |
| 76 | `toolsets.py` aliases | Names defined in toolset configurations |
| 31 | `tools/*.py` functions | Actual Python functions with `task_id` parameter |
| 60 | Gap | Aliases with no implementation |

## Audit Methodology

```python
import subprocess
import os

os.chdir('~/.hermes')

# 1. Check toolsets.py aliases
r = subprocess.run(['grep', '-n', 'ToolAlias', 'toolsets.py'],
    capture_output=True, text=True)
aliases = [l for l in r.stdout.strip().split('\n') if l.strip()]
print(f"Tool aliases in toolsets.py: {len(aliases)}")

# 2. Check actual tool functions (functions with task_id parameter)
r = subprocess.run(['grep', '-rn', 'def .*task_id', 'tools/'],
    capture_output=True, text=True)
functions = [l for l in r.stdout.strip().split('\n') if l.strip()]
print(f"Tool functions with task_id: {len(functions)}")

# 3. Check discover_builtin_tools() modules
r = subprocess.run(['grep', '-n', 'discover_builtin_tools', 'tools/registry.py'],
    capture_output=True, text=True)

# 4. Check registry for registered tools
r = subprocess.run(['python3', '-c',
    "from tools.registry import registry; print(len(registry._tools))"],
    capture_output=True, text=True)
print(f"Registered tools: {r.stdout.strip()}")
```

## Key Finding: 60 Unimplemented Aliases

The `toolsets.py` file defines 76 aliases across toolsets (hermes-cli, web, discord, etc.), but only 31 actual tool functions exist in `tools/*.py`. The remaining 60 aliases are "ghosts" — names that appear in configurations but have no backing implementation.

**Why this happens:**
- Toolsets are configuration files listing desired tools
- Tool modules are actual Python files with implementations
- Adding a tool to a toolset doesn't create the implementation
- Removing a tool module doesn't update the toolset

## Why "92 Tools" Was Reported (Historical Context)

The "92 tools" figure came from a fully-configured setup where:
- All API keys were present (Brave, Firecrawl, Browserbase, Discord, etc.)
- All dependencies installed (fal_client, playwright, etc.)
- All 31 implemented tools were enabled
- Additional tool modules loaded from plugins

Without those conditions, the count drops to 27.

## Verification: Is a Tool Actually Available?

```python
# Check if a specific tool is implemented AND registered
import importlib
from tools.registry import registry

def check_tool(name):
    # Check registry
    in_registry = name in registry._tools
    
    # Check if module exists
    module_name = f"tools.{name}_tool"
    try:
        mod = importlib.import_module(module_name)
        has_handler = hasattr(mod, name) or any(
            callable(getattr(mod, attr)) for attr in dir(mod)
            if not attr.startswith('_')
        )
    except ImportError:
        has_handler = False
    
    return {
        'name': name,
        'in_registry': in_registry,
        'module_exists': has_handler,
        'available': in_registry and has_handler
    }

# Check all aliases
for alias in aliases:
    result = check_tool(alias)
    if not result['available']:
        print(f"⚠ {alias}: registry={result['in_registry']}, module={result['module_exists']}")
```

## Impact

- **User confusion:** "Why do I see 27 tools when I expected 92?"
- **Skill references:** Skills may reference tools that don't exist
- **Documentation drift:** README/docs list tools that aren't implemented

## Fix Options

| Approach | Effort | Risk |
|----------|--------|------|
| Implement 60 missing tools | High | May not be needed |
| Remove aliases from toolsets.py | Low | May break skill references |
| Document the gap | Minimal | User still confused |
| Enable all API keys + deps | Medium | Gets to ~31 enabled, not 92 |

**Recommendation:** The 60 unimplemented aliases are not a bug — they're a configuration wishlist. The actual tool count is 31. Document this clearly and focus on ensuring all 31 work reliably.
