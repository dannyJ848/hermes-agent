# Plugin Hook Invocation Gaps in run_agent.py

## Discovery Date: 2026-05-10
## Affects: All Hermes plugins registering pre_tool_call / post_tool_call hooks

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

| Hook | Registered by plugins | Actually invoked? |
|------|----------------------|-------------------|
| `pre_tool_call` | ✅ Yes | ❌ **NO** |
| `post_tool_call` | ✅ Yes | ❌ **NO** |

**Impact:** Plugins registering `pre_tool_call` and `post_tool_call` handlers will have those handlers exist but never be called by the main loop. The plugin manager's `invoke_hook()` function supports them, but run_agent.py never calls it for these two hooks.

**Workaround:** Use the iteration engine's `before_action()` / `after_action()` methods (wired at lines 10053-10154) for per-tool logging. Or use `pre_llm_call` for prompt injection.

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

## Lessons

1. **Registration ≠ Invocation** — Just because a plugin registers a hook doesn't mean run_agent.py calls it. Always verify the hook name appears in an `_invoke_hook()` call in the main loop.

2. **Silent failures accumulate** — `except Exception: pass` around import blocks hides broken integrations forever. Remove dead code rather than leaving it "just in case."

3. **The iteration engine is the reliable hook** — `before_action()` and `after_action()` at lines 10053-10154 are the most reliable place to inject per-tool behavior because they're directly wired, not going through the plugin dispatch layer.
