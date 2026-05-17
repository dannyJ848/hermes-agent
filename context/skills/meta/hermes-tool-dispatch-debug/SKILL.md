---
name: hermes-tool-dispatch-debug
description: Debug Hermes agent tool dispatch failures where a tool appears in the system prompt schema but returns "Unknown tool" at runtime.
version: 1.0
category: meta
tags: [debugging, hermes-agent, tools, dispatch, memory-provider]
---

# Hermes Tool Dispatch Debug

## Symptom
A tool (e.g., `cerebrum`, `fact_store`, `fact_feedback`) appears in the system prompt's tool schema list, but calling it returns `{"error": "Unknown tool: <name>"}`.

## Root Cause Architecture
Hermes has a **two-tier dispatch system**:

1. **Agent-level dispatch** (`run_agent.py` → `_invoke_tool()`): An elif chain that handles special tools like `todo`, `memory`, `session_search`, `clarify`, `delegate_task`, AND memory provider tools (via `self._memory_manager.handle_tool_call()`).

2. **Registry fallback** (`model_tools.py` → `handle_function_call()` → `tools/registry.py` → `dispatch()`): Catches everything else. Only knows about tools registered via `registry.register()`.

**The gap**: Memory provider tools are injected into the API schema at init time (line ~1093-1099 in run_agent.py) but dispatched via `_memory_manager` at runtime (line ~5620). If `_memory_manager` is None at dispatch time, the tool falls through to the registry which doesn't know about it.

## Critical Discovery (Apr 2026): Gateway Suppresses Print Diagnostics

The gateway passes `quiet_mode=True` to AIAgent (gateway/run.py lines 3897, 5613). This means `print()` statements in the init code are **silently suppressed**. Diagnostic output will NOT appear in gateway.log. 

**Solution**: Use `logger.error()` or `logger.info()` instead of `print()` for diagnostics that must be visible in errors.log. The errors.log handler captures WARNING+ by default; use `logger.error()` for guaranteed visibility.

Also: `_memory_provider_tool_names` was never set during init, making the fallback diagnostic in `_invoke_tool` useless. Always set this attribute:
```python
self._memory_provider_tool_names = self._memory_manager.get_all_tool_names()
```

## Debugging Steps

### 1. Verify plugin loads in isolation
```bash
cd ~/hermes-agent && venv/bin/python3 -c "
from plugins.memory import load_memory_provider
mp = load_memory_provider('cerebrum')  # or 'holographic', 'honcho', etc.
if mp:
    print(f'Loaded: {mp.name}, available={mp.is_available()}')
    print(f'Tools: {[s[\"name\"] for s in mp.get_tool_schemas()]}')
else:
    print('FAILED to load')
"
```

### 2. Verify full init flow
```python
from agent.memory_manager import MemoryManager
from plugins.memory import load_memory_provider

mm = MemoryManager()
mp = load_memory_provider('cerebrum')
mm.add_provider(mp)
from hermes_constants import get_hermes_home
mm.initialize_all(session_id='test', platform='cli', hermes_home=str(get_hermes_home()))
result = mm.handle_tool_call('cerebrum', {'action': 'status'})
print(result)
```

### 3. Check CLI status
```bash
hermes memory status
```

### 4. Trace the dispatch path in run_agent.py
- **Schema injection**: Line ~1093 (`if self._memory_manager and self.tools is not None`)
- **Runtime dispatch**: Line ~5620 (`elif self._memory_manager and self._memory_manager.has_tool(...)`)
- **Silent failure**: Line ~1088 (`except Exception as _mpe` — catches and sets `_memory_manager = None`)

### 5. Check logs for init failure
```bash
grep -i "memory provider" ~/.hermes/logs/gateway.log
grep -i "memory provider" ~/.hermes/logs/errors.log
```

## Common Fixes

### Self-healing: Emergency re-registration
If `_memory_manager` exists but `has_tool()` returns False (tool mapping lost), you can re-register at dispatch time:
```python
# In _invoke_tool, after the memory manager check fails:
if self._memory_manager is not None and not self._memory_manager.has_tool(function_name):
    from plugins.memory import load_memory_provider as _reload
    _mp = _reload('cerebrum')  # or detected from config
    if _mp:
        self._memory_manager.add_provider(_mp)
        if self._memory_manager.has_tool(function_name):
            return self._memory_manager.handle_tool_call(function_name, function_args)
```
This is a band-aid -- the root cause of why the tool mapping is lost still needs investigation.

### Init exception silently swallowed
The init code at line ~1088 catches ALL exceptions and sets `_memory_manager = None`. Add verbose logging:
```python
except Exception as _mpe:
    import traceback as _tb
    logger.warning("Memory provider plugin init failed: %s\n%s", _mpe, _tb.format_exc())
    print(f"⚠️ Memory provider init failed: {_mpe}")
    print(f"   {_tb.format_exc()[:500]}")
    self._memory_manager = None
```

### Plugin not found
Check `plugins/memory/<name>/__init__.py` exists and has a `register(ctx)` function or a `MemoryProvider` subclass.

### is_available() returns False
Check the provider's `is_available()` method — some providers require API keys or external services.

### Stale process
The CLI agent process caches Python modules. After code changes, you MUST restart the full `hermes` CLI (not just the gateway). Python's module cache means `importlib` won't re-read modified `.py` files.

## Critical Discovery (Apr 2026): File-Based Diagnostics Required

`logger.info()` and `logger.error()` from agent init code do NOT reliably appear in gateway.log or errors.log. The gateway's logging configuration may not capture the agent's logger namespace. The only reliable diagnostic method is **direct file writes**:

```python
_diag_f = open("/tmp/memory_diag.log", "a")
_diag_f.write(f"[{datetime.now()}] mem_config={mem_config}, provider={_mem_provider_name}\n")
_diag_f.flush()  # MUST flush — process might crash before close
```

**Lesson**: Spent 10+ iterations checking gateway.log/errors.log before realizing the output was never going to appear there. File writes bypass all logging infrastructure.

## Critical Discovery (Apr 2026): Lazy Agent Creation + Session Caching

Gateway agents are NOT created at startup. They are created **per-message** and **cached per session key** (gateway/run.py lines 5597-5632). Key implications:

1. After adding `memory.provider: cerebrum` to config.yaml, existing sessions continue using their cached agent (without cerebrum)
2. Only NEW sessions (new chat, cron job, or cache invalidation from config signature change) get the new provider
3. Gateway restart clears the in-memory cache, but the next message for an existing session creates a fresh agent — which WILL have the new provider

**To test if a provider loads in the gateway**: Send a new message (Telegram, API, or trigger a cron), then check your diagnostic file. Do NOT expect diagnostics from the gateway startup itself.

## Critical Discovery (Apr 2026): Python Version Mismatch

System `python3` may be an older version (e.g., 3.8) while the venv uses 3.11+. Modern Python syntax (`Path | None`, `X | Y` union types) will fail silently under the system Python. Always test with the venv Python:

```bash
# WRONG — uses system python (may be 3.8)
python3 -c "from plugins.memory import load_memory_provider ..."

# CORRECT — uses venv python (3.11+)
./venv/bin/python -c "from plugins.memory import load_memory_provider ..."
```

The `hermes_constants.py` file uses `Path | None` syntax which crashes under Python <3.10, causing provider load failures that are caught silently.

## Key Files
- `run_agent.py` lines 1030-1100 (init), 5574-5643 (dispatch)
- `agent/memory_manager.py` (MemoryManager class)
- `agent/memory_provider.py` (MemoryProvider ABC)
- `plugins/memory/__init__.py` (plugin loader — `_load_provider_from_dir()`)
- `plugins/memory/<name>/` (individual providers)
- `tools/registry.py` (fallback dispatch)
- `model_tools.py` handle_function_call() (registry entry point)
- `gateway/run.py` lines 5597-5632 (agent cache), 5609 (agent creation)

## Pitfalls
- Tool schemas being in the system prompt does NOT prove runtime dispatch works — schema injection and dispatch are separate code paths
- The `except Exception` at line 1088 silently kills the memory manager — always add traceback logging
- `hermes memory status` only checks if the plugin can load, not if it's active in the current agent process
- Gateway restart (`hermes gateway restart`) does NOT restart the CLI agent — they're separate processes
- **Logger output from agent init may not reach any log file** — use direct file writes for diagnostics
- **Existing sessions use cached agents** — adding a new provider to config doesn't retroactively fix running sessions
- **Always test with venv Python** (`./venv/bin/python`), never system `python3`
- The `_load_provider_from_dir()` function pre-loads submodules into `sys.modules` — if any submodule fails to import, the main module's `from .provider import ...` may find a broken module in cache
- **Never use `sed` for multi-line patch cleanup** — sed operates line-by-line and can leave ghost lines (e.g., an `if _mp:` with its body removed but the `if` line remaining). This causes `IndentationError`/`SyntaxError` that crashes the gateway on next agent creation. Always use the `patch` tool instead of `sed` for removing code blocks.
- **After any `run_agent.py` modification, verify compilation** with `./venv/bin/python -c "import py_compile; py_compile.compile('run_agent.py', doraise=True)"` BEFORE restarting the gateway. A SyntaxError in run_agent.py causes ALL agent creation to fail silently — the gateway stays up but every message/cron fails.
- **Gateway can silently die** — after `hermes gateway restart`, verify with `grep "Gateway running" gateway.log | tail -1` that it actually started. The `OnDemand: true` launchd config means it won't auto-restart if it exits cleanly. Use `hermes gateway start` if needed.
- **Config `max_turns` limits iteration depth** — default is 60 which is insufficient for deep debugging (10+ tool chains). Set to 200 in config.yaml for debugging sessions. The setting is at the top level: `max_turns: 200`.
- **When the real problem is session lifecycle, not code** — if a provider loads correctly in isolation tests (venv Python) but the current session says "Unknown tool", the issue is simply that the session's agent was created before the config change. Fix: start a new session (`/reset` on Telegram). No code changes needed.
- **Predictive Tool Routing** — Use historical tool intelligence to route around weak tools before dispatching. Build `tool_performance_summary` table from `tool_calls` and check success rates before execution. Tools with <50% success should be avoided; tools with <80% should trigger caution warnings.
- **Error Pattern Prediction** — Maintain `error_patterns_predictive` table with known failure modes. Before each tool call, check if the args match a known trigger condition. This prevents psyopg2 abort cascades, patch mismatches, and cronjob id confusion.
- **Tool Registration Gap** — Custom tools in `~/.hermes/tools/` that lack `@register_tool` decorator are invisible to the agent. Only 1 of 46 tools may be functional. Always verify registration with `hermes tools list`.
- **Dead Code Bloat** — 91% of subconscious modules may be orphaned (never imported). This creates debugging overhead. Archive orphans to `~/subconscious/archive/` to improve clarity.

## Industry Context (2026)

Agent debugging is a recognized discipline with dedicated platforms (Braintrust, Langfuse, LangSmith, Arize Phoenix, Helicone). Key industry insight: **most agent failures don't trigger visible errors** — the system returns successful status codes even when results are wrong. The agent may select the wrong tool, pass incorrect parameters, or hallucinate a response while monitoring shows clean completion. This is exactly the tool dispatch problem: the tool schema is valid, the call completes, but the wrong tool or wrong parameters were selected. The debugging workflow is: (1) reconstruct full execution path, (2) identify the failing step, (3) reproduce in controlled environment, (4) convert failure into a permanent test case.
