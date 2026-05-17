# Tool Registry Inspection Pattern

When verifying that tools are properly registered after integration, the `hermes tools list` command is the user-facing check. But for deep debugging — especially after moving tools from `~/subconscious/` into `~/hermes-agent/tools/` — you often need to inspect the registry directly via Python.

## The Python Version Trap (CRITICAL)

**System Python 3.8 will crash on `tools/registry.py`.** The file uses `dict[...]` subscript syntax (line 114: `_check_fn_cache: Dict[Callable, tuple[float, bool]] = {}`) which requires Python 3.9+.

```bash
# ❌ WRONG — uses system python (3.8), crashes with TypeError
python3 -c "from tools.registry import _TOOLS"
# TypeError: 'type' object is not subscriptable

# ✅ CORRECT — uses venv python (3.11+)
cd ~/hermes-agent && source venv/bin/activate && python3 -c "..."
# Or directly: ~/hermes-agent/venv/bin/python3 -c "..."
```

## The Import Path Trap

**`tools.model_tools` does NOT exist.** The module is `model_tools` (top-level), not `tools.model_tools`.

```python
# ❌ WRONG — ModuleNotFoundError
from tools.model_tools import discover_builtin_tools

# ✅ CORRECT
from model_tools import discover_builtin_tools
```

## The Empty Registry Trap

**`registry._tools` is empty until discovery runs.** The `ToolRegistry` class initializes with `_tools: dict = dict(len=0)`. Tools are only populated when `discover_builtin_tools()` scans `tools/*.py` files via AST parsing and imports those with `registry.register()` calls.

```python
from tools.registry import registry
print(len(registry._tools))  # 0 — empty!

# Must trigger discovery first
from model_tools import discover_builtin_tools
discover_builtin_tools()

print(len(registry._tools))  # 135+ — populated
```

## Complete Verification Script

```python
import os, sys
sys.path.insert(0, os.path.expanduser("~/hermes-agent"))

# MUST use venv python — system 3.8 will crash
from model_tools import discover_builtin_tools
from tools.registry import registry

# Trigger discovery
discover_builtin_tools()

print(f"Total tools registered: {len(registry._tools)}")

# Check for specific tool categories
categories = {
    "Vision/Screen": ["screen_capture", "gui_click", "gui_type", "vision_analyze", "browser_vision"],
    "X/Twitter": ["x_search", "x_tweet_fetch", "x_user_tweets"],
    "Image": ["image_generate", "browser_get_images"],
}

for cat, names in categories.items():
    found = [n for n in names if n in registry._tools]
    missing = [n for n in names if n not in registry._tools]
    status = "✅" if not missing else "⚠️"
    print(f"  {status} {cat}: {len(found)}/{len(names)} — missing: {missing}")

# List all tools (sample)
print("\nAll tools (first 30):")
for name in sorted(registry._tools.keys())[:30]:
    print(f"  {name}")
```

## Tool Definitions Format Trap

**`get_tool_definitions()` returns OpenAI function-calling format.** The `name` field is nested under `function`, NOT at the top level.

```python
import model_tools as mt
tools = mt.get_tool_definitions()

# ❌ WRONG — returns empty strings for all tools
tool_names = [t.get("name", "") for t in tools]

# ✅ CORRECT
tool_names = [t.get("function", {}).get("name", "") for t in tools]
```

## Plugin Load Warnings (Non-Critical)

During `discover_builtin_tools()`, you may see plugin load failures like:
```
Failed to load plugin 'spotify': No module named 'plugins.spotify'
Failed to load plugin 'evey-honcho': No module named 'honcho_bridge'
```

These are **non-critical** — they're optional plugins with missing dependencies. The core cognitive systems and tools still register correctly. Do NOT chase these unless the user explicitly asks about them.

## Quick CLI Verification

For a fast check without Python scripting:
```bash
hermes tools list 2>&1 | grep -E "screen_capture|gui_click|gui_type|x_"
```

This uses the Hermes CLI's built-in discovery and is reliable. Use it first before resorting to Python inspection.
