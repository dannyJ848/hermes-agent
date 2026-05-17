# Plugin Hook Wiring Gaps — Hermes Agent Loop

## Discovery Date: 2026-05-10
## Context: Cognitive systems integration into Hermes source

---

## The Gap

Hermes PluginManager supports registering hooks via `ctx.register_hook("hook_name", handler)`.
However, **run_agent.py does NOT invoke all registered hooks**. Only a subset are actually called.

### Hooks INVOKED by run_agent.py (verified in source)

| Hook | Location in run_agent.py | Context Injected? |
|------|--------------------------|-------------------|
| `on_session_start` | Line ~11459 | No (fire-and-forget) |
| `pre_llm_call` | Line ~11593 | **Yes** — context returned is injected into user message |
| `pre_api_request` | Line ~12097 | No (fire-and-forget telemetry) |
| `post_api_request` | Line ~13915 | No (fire-and-forget telemetry) |
| `transform_llm_output` | Line ~14849 | Yes — first non-empty string wins |
| `post_llm_call` | Line ~14870 | No (fire-and-forget) |
| `on_session_end` | Line ~14985 | No (fire-and-forget) |

### Hooks REGISTERED but NOT INVOKED

| Hook | Registered by cognitive-systems plugin | Actually invoked? |
|------|------------------------------------------|-------------------|
| `pre_tool_call` | ✅ Yes | ❌ **NO** |
| `post_tool_call` | ✅ Yes | ❌ **NO** |

**Impact:** The cognitive systems plugin registers handlers for `pre_tool_call` and `post_tool_call` expecting to inject tool-call-time context and log tool outcomes. These handlers exist but are never called by the main loop.

**Workaround:** The iteration engine's `before_action()` and `after_action()` methods (wired at lines 10053-10154) handle pre/post tool logging instead. But they do NOT inject context into prompts — they only record to the experience database.

---

## How to Detect This Gap

```python
# Check if a hook is actually invoked in run_agent.py
import re

with open("run_agent.py") as f:
    content = f.read()

hooks = ["pre_tool_call", "post_tool_call", "pre_llm_call", "post_llm_call",
         "on_session_start", "on_session_end"]

for hook in hooks:
    # Look for _invoke_hook("hook_name" or _invoke_hook('hook_name'
    pattern = f'_invoke_hook\\(["\']{hook}["\']'
    found = bool(re.search(pattern, content))
    print(f"{'✅' if found else '❌'} {hook}: {'invoked' if found else 'NOT invoked'}")
```

---

## Dead Code Pattern in hermes_cli/plugins.py

The function `get_pre_tool_call_block_message()` in `hermes_cli/plugins.py` contained dead code from an old subconscious integration:

```python
# OLD DEAD CODE (removed 2026-05-10):
try:
    from memory_cortex_bridge import MemoryCortexBridge  # ← wrong import path
    bridge = MemoryCortexBridge()
    result = bridge.offload_if_needed()
    # ...
    from tool_intelligence_tracker import ToolIntelligenceTracker  # ← wrong import path
    tracker = ToolIntelligenceTracker()
    tracker.record_call(...)
except Exception:
    pass  # Silently fails forever
```

**Problem:** These imports fail because the modules are now in `agent.` namespace. The `except Exception: pass` swallows the failure silently. The code ran on every tool call but did nothing.

**Fix:** Remove the dead code. The functionality is now handled by:
1. The cognitive-systems plugin's `_pre_tool_call_handler` (registered but not invoked — see gap above)
2. The iteration engine's `before_action()` / `after_action()` (wired and working)

---

## Self-Import Anti-Pattern in agent/ Modules

Multiple agent/ modules had lazy imports inside functions referencing themselves without the `agent.` prefix:

```python
# BAD — inside agent/memory_cortex_bridge.py:
def some_function():
    from memory_cortex_bridge import MemoryCortexBridge  # ← self-import, no agent. prefix
    bridge = MemoryCortexBridge()
```

This works when the module is imported as `agent.memory_cortex_bridge` (it's already in `sys.modules`), but:
- It's confusing and fragile
- It breaks if the module is ever executed directly
- It makes grep searches for bad imports harder

**Fix pattern:**
```python
# GOOD:
def some_function():
    from agent.memory_cortex_bridge import MemoryCortexBridge
    bridge = MemoryCortexBridge()
```

**Files fixed in this session:**
- `agent/memory_cortex_bridge.py` (3 occurrences)
- `agent/subconscious_hook_wiring.py` (2 occurrences)
- `agent/auto_fallback_engine.py` (1 occurrence)
- `agent/hermes_enhancement_suite.py` (2 occurrences)
- `agent/proactive_memory_guard.py` (2 occurrences)
- `agent/tool_intelligence_tracker.py` (1 occurrence)
- `agent/subconscious_systems_manifest.py` (1 occurrence)

---

## Verification Script

Save as `scripts/verify_hook_wiring.py` and run after any plugin integration:

```python
#!/usr/bin/env python3
"""Verify that plugin hooks registered are actually invoked by run_agent.py."""

import re
from pathlib import Path

def verify_hooks():
    run_agent = Path.home() / "hermes-agent/run_agent.py"
    content = run_agent.read_text()
    
    all_hooks = [
        "on_session_start", "pre_llm_call", "pre_api_request",
        "post_api_request", "transform_llm_output", "post_llm_call", "on_session_end",
        "pre_tool_call", "post_tool_call",  # These are the gap
    ]
    
    print("Hook Invocation Status in run_agent.py:")
    print("=" * 50)
    
    for hook in all_hooks:
        pattern = f'_invoke_hook\\(["\']{hook}["\']'
        found = bool(re.search(pattern, content))
        status = "✅ INVOKED" if found else "❌ NOT INVOKED"
        print(f"  {status}: {hook}")
    
    # Check for dead import patterns
    print("\nDead Import Patterns:")
    print("=" * 50)
    
    bad_patterns = [
        ("from memory_cortex_bridge import", "Should be 'from agent.memory_cortex_bridge import'"),
        ("from tool_intelligence_tracker import", "Should be 'from agent.tool_intelligence_tracker import'"),
    ]
    
    for pattern, fix in bad_patterns:
        if pattern in content:
            print(f"  ❌ FOUND: {pattern}")
            print(f"     → {fix}")
        else:
            print(f"  ✅ CLEAN: {pattern}")

if __name__ == "__main__":
    verify_hooks()
```

---

## Lessons

1. **Registration ≠ Invocation** — Just because a plugin registers a hook doesn't mean run_agent.py calls it. Always verify the hook name appears in an `_invoke_hook()` call in the main loop.

2. **Silent failures accumulate** — `except Exception: pass` around import blocks hides broken integrations forever. Remove dead code rather than leaving it "just in case."

3. **Self-imports are technical debt** — They work by accident (module already in sys.modules) but break refactoring. Always use the full `agent.` prefix.

4. **The iteration engine is the reliable hook** — `before_action()` and `after_action()` at lines 10053-10154 are the most reliable place to inject per-tool behavior because they're directly wired, not going through the plugin dispatch layer.
