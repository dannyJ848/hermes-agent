---
name: agent-mesh
version: 1.0
created: 2026-04-06
description: Multi-agent coordination layer for Hermes. SQLite-backed presence, messaging, file locks, and task board — zero external dependencies.
tags: [hermes, multi-agent, coordination, mesh, file-locks, task-board]
---

# Agent Mesh — Multi-Agent Coordination

A local SQLite-based coordination layer that lets multiple Hermes agent sessions see each other, communicate, avoid file conflicts, and share tasks. No external broker needed.

## Architecture

```
~/.hermes/agent-mesh.db          # Shared SQLite DB (WAL mode for concurrent access)
~/.hermes/.mesh-signal           # Touch file to notify watchers of DB changes

~/.hermes/plugins/evey-mesh/
├── plugin.yaml                  # Plugin manifest
├── __init__.py                  # Tools: mesh_status, mesh_message, mesh_task, mesh_lock
└── mesh_db.py                   # All DB operations (presence, activity, locks, tasks, messages)

~/.hermes/hooks/agent-mesh/
├── HOOK.yaml                    # Hook manifest (agent:start, agent:step, agent:end)
└── handler.py                   # Registers presence, heartbeats, logs tool calls, deregisters

~/hermes-agent/gateway/run.py    # Context injection at line ~2299 (after distillation block)
```

## How It Works

1. **On agent:start** — Register presence (agent_id, session_id, model, provider)
2. **On agent:step** — Heartbeat + log tool calls to activity_stream
3. **On agent:end** — Deregister + release all file locks
4. **Context injection** — When other agents detected, inject mesh context into session

## 4 Tools

| Tool | Purpose |
|------|---------|
| `mesh_status` | See active agents, locks, messages, tasks, activity |
| `mesh_message` | Send direct or broadcast messages to agents |
| `mesh_task` | Create/claim/complete tasks on shared board |
| `mesh_lock` | Acquire/release file locks (TTL-based, auto-expire) |

## Key Design Decisions

1. **SQLite WAL mode** — Allows concurrent reads/writes from multiple processes without locking. `PRAGMA journal_mode=WAL` + `busy_timeout=5000`.

2. **TTL-based file locks** — Each lock has an expiry time. If an agent crashes, locks auto-expire. Default TTL: 300 seconds.

3. **Context injection only when needed** — Mesh context is only injected into agent sessions when other agents are actually active (solo agents see nothing).

4. **Signal file** — `~/.hermes/.mesh-signal` is touched on every write. Can be watched with fswatch for real-time notification.

5. **Stable agent identity** — Uses 3-tier lookup: (1) `HERMES_MESH_ID` env var, (2) `~/.hermes/.mesh-identity` file, (3) hash of hostname+username. NEVER use `os.getpid()` — it changes per execute_code sandbox call, creating phantom duplicate agents. The identity file is written once and persists across all sessions and sandboxes.

## DB Schema (5 tables)

```sql
presence        — agent_id, session_id, model, provider, status, last_heartbeat
activity_stream — agent_id, session_id, event_type, tool_name, details, timestamp
file_locks      — file_path, agent_id, session_id, lock_type, acquired_at, expires_at
task_board      — task_id, title, description, status, owner_id, priority
messages        — from_agent, to_agent, message_type, subject, body, read_by
```

## Integration Points

### Gateway Context Injection (run.py ~line 2299)

Placed right after the distillation recall injection block. Only fires when `agent-mesh.db` exists AND other agents are active:

```python
# ── Agent Mesh: inject multi-agent coordination context ──
try:
    _mesh_agents = get_active_agents(max_age_seconds=300)
    _other_count = len([a for a in _mesh_agents 
                       if a["agent_id"] != f"agent-{str(session_id)[:12]}"])
    if _other_count > 0:
        _mesh_ctx = format_mesh_context(f"agent-{str(session_id)[:12]}")
        if _mesh_ctx:
            context_prompt += "\n\n" + _mesh_ctx
except Exception as _me:
    logger.debug("Agent Mesh injection failed (non-fatal): %s", _me)
```

### Hook Handler (handler.py)

Uses lazy-load pattern to avoid import errors on gateway startup:

```python
def _ensure_mesh():
    global _mesh_loaded, _mesh_db
    if _mesh_loaded:
        return _mesh_db is not None
    try:
        sys.path.insert(0, MESH_PLUGIN_DIR)
        import mesh_db
        _mesh_db = mesh_db
        mesh_db.init_db()
        _mesh_loaded = True
        return True
    except Exception as e:
        _mesh_loaded = True  # Don't retry
        return False
```

## Testing Pattern

Write test scripts to /tmp/ and run with system python3 (no venv needed — pure stdlib):

```python
import sys
sys.path.insert(0, "/Users/dannygomez/.hermes/plugins/evey-mesh")
from mesh_db import (register_agent, get_active_agents, format_mesh_context,
                     log_activity, send_message, create_task, acquire_lock)

register_agent('test-1', 'sess-abc', 'glm-5.1', 'zai')
register_agent('test-2', 'sess-def', 'claude-opus-4', 'anthropic')

# Test lock conflict
acquire_lock("/path/to/file.py", "test-1", "sess-abc", "write", 300)
result = acquire_lock("/path/to/file.py", "test-2", "sess-def", "write", 300)
# result["success"] == False, result["held_by"] == "test-1"

print(format_mesh_context('test-1'))
```

## Manual Registration

Agents are NOT auto-registered when using the mesh tools directly (only the hook handler registers on agent:start). To manually register yourself:

```python
import sys, os, time
sys.path.insert(0, os.path.expanduser('~/.hermes/plugins/evey-mesh'))
from mesh_db import init_db, register_agent

init_db()
agent_id = 'agent-dannygomez-b20137a0'  # from _stable_agent_id()
session_id = f'cli-{int(time.time())}'
register_agent(agent_id, session_id, model='glm-5.1', provider='zai',
               metadata={"name": "Evey", "role": "primary-agent"})
```

IMPORTANT: `register_agent()` signature is `(agent_id, session_id, model, provider, platform, metadata)` — `session_id` is REQUIRED, there is no `name` or `role` param (those go in `metadata` dict).

## mesh_status Shows OTHER Agents Only

`mesh_status` calls `get_mesh_context(agent_id)` which filters out the calling agent (line 446 in mesh_db.py: `other_agents = [a for a in agents if a["agent_id"] != agent_id]`). So when you're solo, it always says "None (you are solo)" even though you ARE registered. This is by design — it shows your peers, not yourself. To verify your own registration, query the DB directly:

```python
from mesh_db import get_active_agents
agents = get_active_agents(max_age_seconds=300)
for a in agents:
    print(f'{a["agent_id"]} | {a["status"]} | heartbeat={ago}s ago')
```

## Pitfalls

1. **Relative imports fail in plugins** — The Hermes plugin loader may import `__init__.py` without package context. Use try/except with `from .mesh_db import ...` falling back to `sys.path.insert(0, plugin_dir); from mesh_db import ...`.

2. **Variable name typos in f-strings** — `len(other)` vs `len(others)` compiles fine but crashes at runtime. Test format_mesh_context() specifically.

3. **Hook handler must be `async def handle(event_type, context)`** — The hook registry expects this exact signature. No other names.

4. **Gateway restart required** — Plugin files and hook handlers are loaded at gateway startup. Changes to mesh_db.py or handler.py require `bash ~/.hermes/scripts/safe-restart.sh`.

5. **Don't clean up presence on crash** — If an agent crashes without firing agent:end, its presence row stays with a stale heartbeat. `get_active_agents()` filters by `last_heartbeat > now - 120`, so stale entries are automatically excluded. No cleanup needed.

6. **signal() is fire-and-forget** — `SIGNAL_FILE.touch()` can fail (perms, disk full). Wrapped in try/except so it never blocks.

7. **Agent IDs can multiply — session restarts create new IDs** — A single physical agent can register as multiple agent IDs if its session restarts or the hook fires twice. The agent that first appeared as `agent-cli-8335` may later send messages as `agent-dannygomez-b20137a0`. Always check `session_id` to correlate, and look at ALL messages not just those matching a specific `to_agent`.

8. **Message `to_agent` can be empty string** — Some send_message() calls leave `to_agent` as `""` instead of `"broadcast"`. When querying for messages directed at you, check both `to_agent='agent-cli-main'` AND `to_agent=''` AND `to_agent='broadcast'`.

9. **Echo agents — message senders not in presence** — An agent can send messages without ever registering in the presence table (e.g., if registration failed but messaging succeeded). Don't assume all message senders have presence entries. Cross-reference both tables.

10. **Use write_file + python3 for mesh queries** — Inline Python in terminal() breaks on f-strings with newlines. Always write query scripts to `/tmp/mesh_*.py` first, then run with `python3 /tmp/mesh_*.py`. This avoids SyntaxError from nested quotes and newlines.

11. **Manual registration for CLI sessions** — CLI sessions (started via `hermes` command) may not trigger the `agent:start` hook. You can manually register using:
    ```python
    sys.path.insert(0, "/Users/dannygomez/.hermes/plugins/evey-mesh")
    from mesh_db import register_agent, log_activity
    register_agent("agent-cli-main", "session-label", "model", "provider")
    log_activity("agent-cli-main", "session-label", "agent:start", None, {})
    ```

7. **MUST have register(ctx) function** — The Hermes plugin loader (`hermes_cli/plugins.py`) calls `register(ctx)` as the entry point. Without it, the gateway logs "Plugin 'evey-mesh' has no register() function" and skips it entirely. Each tool must be registered via `ctx.register_tool(name=..., toolset=..., schema=..., handler=..., description=..., emoji=...)`. Just having tool functions in the module is NOT enough.

8. **plugin.yaml must use provides_hooks (not hooks)** — The Hermes plugin system reads `provides_hooks:` and `provides_tools:` from plugin.yaml. Using `hooks:` is ignored silently — it's the event hook system format, not the plugin format.

9. **Clear __pycache__ after every plugin edit** — The gateway loads plugins via `importlib` which caches bytecode in `__pycache__/`. If you edit `.py` files without clearing the cache, the gateway may load stale `.pyc` on restart. Always `rm -rf ~/.hermes/plugins/*/ __pycache__/` before `hermes gateway restart`.

10. **Never use os.getpid() for identity in plugin tools** — Hermes executes plugin tools inside execute_code sandboxes with different PIDs each time. Using `os.getpid()` as agent identity creates a new phantom agent per call. Use the `_stable_agent_id()` function instead, which reads from `~/.hermes/.mesh-identity`.

11. **Two separate hook systems** — Hermes has (a) event hooks in `~/.hermes/hooks/` (HOOK.yaml + handler.py, events like agent:start), and (b) plugin hooks via `ctx.register_hook()` (post_tool_call, pre_tool_call, etc.). They are completely independent. The mesh uses BOTH: event hooks for presence/heartbeat, plugin hooks for tool registration.

## Future Enhancements

- [ ] Watch ~/.hermes/.mesh-signal with fswatch for sub-second notification
- [ ] Add mesh_broadcast tool for announcement-style messages
- [ ] Add conflict detection (warn if two agents recently edited same file)
- [ ] Wire mesh_task into distillation cycle (AGI loop can assign tasks to specific agents)
- [ ] Add mesh_negotiate tool for agents to coordinate on approach before starting work
