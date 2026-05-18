---
name: plugin-sanity-check
description: Verify plugins are actually functional before relying on them. Never queue real work into unverified channels.
version: 1.0
---

# Plugin Sanity Check

## Trigger
Before relying on ANY plugin-based tool (bridge, delegation, messaging, etc.) for the first time in a session, verify it actually works end-to-end.

## Steps
1. **Check prerequisites**: Does the tool need an API key, running service, or external dependency?
2. **Quick smoke test**: Send a trivial request and confirm you get a real response
3. **If no response within 30s**: Assume non-functional. Do it yourself.
4. **Never queue real work** into an unverified channel

## Plugin Shadowing Pattern (CRITICAL)

Hermes has **two layers** of web tools that can conflict:
- **Core**: `~/hermes-agent/tools/web_tools.py` — supports Firecrawl, Parallel, Tavily, Exa backends. Reads `web.backend` from config.yaml.
- **Plugin**: `~/.hermes/plugins/evey-research/__init__.py` — was hardcoded to SearXNG only, **shadows** the core tools by registering with the same names (`web_research`, `web_extract`).

When a plugin and core tool share the same name, the **plugin wins**. Configuring `web.backend: firecrawl` in config.yaml only affects the core layer — the plugin layer ignores it entirely.

**Fix pattern:** Patch the plugin to support the new backend, then restart the agent process. Env vars in plugins are module-level constants (`os.environ.get(...)` at import time) — they require a full process restart to take effect, not just a config reload.

```
# Clear cached bytecode after patching a plugin
rm -f ~/.hermes/plugins/evey-research/__pycache__/__init__.cpython-*.pyc
# Full restart — must kill ALL hermes processes, not just run_agent.py
pkill -f hermes_cli.main   # kills the gateway process
pkill -f "hermes -p"       # kills squad profiles
pkill -f run_agent.py      # kills the main agent
# Then relaunch with the hermes CLI (reads config.yaml):
hermes
# NOT: python run_agent.py (that uses Google Fire args, ignores config.yaml)
```

## Status (Apr 2026)
- `claude_bridge_task`: No Anthropic API key. Bridge directory exists but nothing reads it.
- `delegate_task` (subagent): Requires delegation API key not configured.
- `web_research`: Patched evey-research plugin to use Firecrawl (FIRECRAWL_API_KEY in .env). SearXNG as fallback. Needs agent restart to activate.
- `news_scan`: Still uses SearXNG via evey-news plugin (separate patch needed if Firecrawl desired).

## Working Alternatives
- Code changes: `patch`, `terminal`, or `write_file` directly
- Delegation: `delegate_with_model` (ZAI endpoint)
- Web search (when plugin active): `web_research` via Firecrawl
- Web search (fallback): `web_extract` on known URLs
- Browser testing: `browser_navigate` + `browser_vision`

## Hermes Process Architecture (CRITICAL for restarts)

Hermes runs **multiple processes** that survive partial kills:
- **Gateway**: `hermes_cli.main gateway run` (PID varies) — handles Telegram/sessions, survives `pkill -f run_agent.py`
- **Main agent**: `run_agent.py` or `hermes` CLI — the agent loop
- **Squad profiles**: `hermes -p soma-coder` etc. — separate agent processes in tmux

Killing only `run_agent.py` leaves the gateway alive, which keeps serving the old session with stale plugins/env vars. A proper restart must kill ALL of them.

**IMPORTANT**: `python run_agent.py` does NOT read `~/.hermes/config.yaml`. It uses Google Fire CLI args and defaults to OpenRouter. Use `hermes` command instead, which reads config.yaml (model, provider, base_url, .env, etc.).

## Diagnosing Plugin Load Status (when logs are ambiguous)

When you need to verify a plugin is loaded but the gateway log doesn't show explicit load messages:

1. **Check the plugin discovery count**: `grep "plugin discovery" ~/.hermes/logs/gateway.log | tail -5`
   - Shows "N found, M enabled" — count includes your plugin if M matches expected number
   - 2 expected failures: evey-honcho (missing module), evey-mesh (no register)
   - No WARNING for your plugin = it loaded without error

2. **Test the plugin code in isolation**: Load `__init__.py` via `importlib.util.spec_from_file_location()` with a fake `PluginContext` and call `register()` directly. Confirms the code is syntactically valid and the hook registers.

3. **Check side effects, not logs**: The definitive proof is whether the plugin's hook is producing output.
   - For distillation: `sqlite3 ~/subconscious/tool_capability.db "SELECT COUNT(*) FROM call_log; SELECT MAX(timestamp) FROM call_log"` — if latest timestamp is recent, the hook is actively firing.
   - The plugin's `logger.info()` may be filtered by gateway log level (gateway only shows WARNING+ for non-core loggers). Absent log line != absent plugin.

4. **Plugin scan paths** (in order):
   - `~/.hermes/plugins/` (user plugins — ALWAYS scanned)
   - `./.hermes/plugins/` (project plugins — only if `HERMES_ENABLE_PROJECT_PLUGINS` env var set)
   - Pip entry-point plugins (`hermes_plugins` group)
   - Files at `~/hermes-agent/plugins/` are NOT auto-discovered — must be in `~/.hermes/plugins/` or registered as entry points.

## Lessons
1. Plugins create the appearance of functionality without the reality. Always verify before committing real work.
2. When a tool doesn't respond to config changes, check if a **plugin is shadowing** the core implementation. Search `~/.hermes/plugins/` for duplicate registrations.
3. Plugin env vars are frozen at import time — `hermes gateway restart` is NOT enough. Need full process kill and relaunch.
4. `python run_agent.py` ignores config.yaml. Always use `hermes` CLI to launch, which reads model/provider/base_url from config.
5. When restarting, kill the gateway separately: `pkill -f hermes_cli.main`. The gateway process does not die with the agent.
6. **CLI and Gateway are SEPARATE Python processes with INDEPENDENT plugin caches.** `hermes gateway restart` reloads plugins for the gateway/Telegram sessions ONLY. A running CLI session (`hermes --resume`) keeps its old plugin code in memory. To update CLI plugins, you must restart the CLI session itself. Verify which process you're IN with: `ps -p $$ -o ppid= | xargs` then `ps -p <ppid> -o command=`. If the parent is a CLI session started before your plugin changes, it's running stale code.
7. **When plugin changes don't take effect despite restarts**, check `__pycache__` timestamps vs `__init__.py`. If .pyc is FRESH but output is still v1, you're almost certainly in the WRONG process. Don't waste time clearing caches — identify and restart the actual process you're running in.

## Stale `.pyc` Cache Bug (Apr 2026 — CONFIRMED)

**Symptom:** Plugin code is updated on disk (verified with `grep`), gateway restarts, but old behavior persists. Gateway log shows old version loading.

**Root cause:** Python's `importlib` in the plugin loader (`hermes_cli/plugins.py` `_load_directory_module()`) uses `spec_from_file_location()` which checks `.pyc` cache. If the `.pyc` timestamp is stale or the filesystem has sub-second timing issues (common on macOS), Python loads the old bytecode instead of recompiling.

**Fix:**
```bash
# ALWAYS do this after editing any plugin .py file, BEFORE restarting:
rm -rf ~/.hermes/plugins/<plugin-name>/__pycache__/

# Then restart:
hermes gateway restart
```

**Prevention:** After ANY plugin edit, delete `__pycache__/` in that plugin directory. Do not rely on Python's timestamp-based recompilation.

**Real case:** Distillation plugin had `post_tool_call` hook only. Added `pre_tool_call` hook to `__init__.py`. Gateway restart still loaded old code (only post_tool_call). `__pycache__/__init__.cpython-311.pyc` was stale. Deleting it and restarting fixed it immediately.

## Missing `register()` Function Bug (Apr 2026 — CONFIRMED)

**Symptom:** Plugin has tool functions but gateway log says `Plugin '<name>' has no register() function`. Tools never appear in the agent's tool list.

**Root cause:** The plugin has `__init__.py` with tool functions and `plugin.yaml` with `provides_tools:` list, but no `register(ctx)` function. Hermes plugin loader (`_load_plugin()`) calls `register_fn(ctx)` — if it's missing, the plugin is marked as failed.

**Fix:** Add a `register(ctx)` function that calls `ctx.register_tool()` for each tool with proper JSON schema:
```python
def register(ctx) -> None:
    """Plugin entry point — register tools with Hermes."""
    try:
        ctx.register_tool(
            name="my_tool",
            toolset="my_plugin",
            schema={
                "type": "object",
                "properties": {
                    "param": {"type": "string", "description": "..."},
                },
                "required": ["param"],
            },
            handler=my_tool_function,
            description="What this tool does.",
            emoji="🔧",
        )
        logger.info("My plugin: tool registered successfully")
    except Exception as e:
        logger.warning("My plugin failed to register: %s", e)
```

**Also fix `plugin.yaml`:** Use `provides_hooks:` (not `hooks:`) and `provides_tools:`. The `hooks:` key is for the separate hooks system (`~/.hermes/hooks/`), not for plugins.

**Real case:** evey-mesh plugin had 4 tool functions (mesh_status, mesh_message, mesh_task, mesh_lock) but no `register()`. Gateway logged `Plugin 'evey-mesh' has no register() function` on every startup. Adding register() with ctx.register_tool() for all 4 fixed it.

## Mesh Direct DB Access Pattern

When mesh tools aren't loaded yet, you can query the mesh database directly:

```bash
sqlite3 ~/.hermes/agent-mesh.db
```

Key tables: `presence` (not `agents`), `activity_stream`, `file_locks`, `task_board`, `messages`.

**Pitfalls:**
- Table is `presence`, not `agents` (the `agents` table does not exist)
- `sqlite3.Row` objects don't have `.get()` — use dict conversion: `dict(zip(cols, row))`
- Column names vary from what the tool functions expect (e.g., `sent_at` may not exist — use `timestamp` instead)
- When schema is unknown, discover columns first: `conn.execute("SELECT * FROM messages LIMIT 1").description`
