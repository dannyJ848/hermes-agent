# Hermes Agent - Development Guide

Instructions for AI coding assistants and developers working on the hermes-agent codebase.

## Development Environment

```bash
# Prefer .venv; fall back to venv if that's what your checkout has.
source .venv/bin/activate   # or: source venv/bin/activate
```

`scripts/run_tests.sh` probes `.venv` first, then `venv`, then
`$HOME/.hermes/hermes-agent/venv` (for worktrees that share a venv with the
main checkout).

## Project Structure

File counts shift constantly — don't treat the tree below as exhaustive.
The canonical source is the filesystem. The notes call out the load-bearing
entry points you'll actually edit.

```
hermes-agent/
├── run_agent.py          # AIAgent class — core conversation loop (~12k LOC)
├── model_tools.py        # Tool orchestration, discover_builtin_tools(), handle_function_call()
├── toolsets.py           # Toolset definitions, _HERMES_CORE_TOOLS list
├── cli.py                # HermesCLI class — interactive CLI orchestrator (~11k LOC)
├── hermes_state.py       # SessionDB — SQLite session store (FTS5 search)
├── hermes_constants.py   # get_hermes_home(), display_hermes_home() — profile-aware paths
├── hermes_logging.py     # setup_logging() — agent.log / errors.log / gateway.log (profile-aware)
├── batch_runner.py       # Parallel batch processing
├── agent/                # Agent internals (provider adapters, memory, caching, compression, etc.)
├── hermes_cli/           # CLI subcommands, setup wizard, plugins loader, skin engine
├── tools/                # Tool implementations — auto-discovered via tools/registry.py
│   └── environments/     # Terminal backends (local, docker, ssh, modal, daytona, singularity)
├── gateway/              # Messaging gateway — run.py + session.py + platforms/
│   ├── platforms/        # Adapter per platform (telegram, discord, slack, whatsapp,
│   │                     #   homeassistant, signal, matrix, mattermost, email, sms,
│   │                     #   dingtalk, wecom, weixin, feishu, qqbot, bluebubbles,
│   │                     #   webhook, api_server, ...). See ADDING_A_PLATFORM.md.
│   └── builtin_hooks/    # Extension point for always-registered gateway hooks (none shipped)
├── plugins/              # Plugin system (see "Plugins" section below)
│   ├── memory/           # Memory-provider plugins (honcho, mem0, supermemory, ...)
│   ├── context_engine/   # Context-engine plugins
│   └── <others>/         # Dashboard, image-gen, disk-cleanup, examples, ...
├── optional-skills/      # Heavier/niche skills shipped but NOT active by default
├── skills/               # Built-in skills bundled with the repo
├── ui-tui/               # Ink (React) terminal UI — `hermes --tui`
│   └── src/              # entry.tsx, app.tsx, gatewayClient.ts + app/components/hooks/lib
├── tui_gateway/          # Python JSON-RPC backend for the TUI
├── acp_adapter/          # ACP server (VS Code / Zed / JetBrains integration)
├── cron/                 # Scheduler — jobs.py, scheduler.py
├── environments/         # RL training environments (Atropos)
├── scripts/              # run_tests.sh, release.py, auxiliary scripts
├── website/              # Docusaurus docs site
└── tests/                # Pytest suite (~15k tests across ~700 files as of Apr 2026)
```

**User config:** `~/.hermes/config.yaml` (settings), `~/.hermes/.env` (API keys only).
**Logs:** `~/.hermes/logs/` — `agent.log` (INFO+), `errors.log` (WARNING+),
`gateway.log` when running the gateway. Profile-aware via `get_hermes_home()`.
Browse with `hermes logs [--follow] [--level ...] [--session ...]`.

## File Dependency Chain

```
tools/registry.py  (no deps — imported by all tool files)
       ↑
tools/*.py  (each calls registry.register() at import time)
       ↑
model_tools.py  (imports tools/registry + triggers tool discovery)
       ↑
run_agent.py, cli.py, batch_runner.py, environments/
```

---

## AIAgent Class (run_agent.py)

The real `AIAgent.__init__` takes ~60 parameters (credentials, routing, callbacks,
session context, budget, credential pool, etc.). The signature below is the
minimum subset you'll usually touch — read `run_agent.py` for the full list.

```python
class AIAgent:
    def __init__(self,
        base_url: str = None,
        api_key: str = None,
        provider: str = None,
        api_mode: str = None,
        model: str = "",
        max_iterations: int = 90,
        enabled_toolsets: list = None,
        disabled_toolsets: list = None,
        quiet_mode: bool = False,
        save_trajectories: bool = False,
        platform: str = None,
        session_id: str = None,
        skip_context_files: bool = False,
        skip_memory: bool = False,
        credential_pool=None,
    ): ...

    def chat(self, message: str) -> str:
        """Simple interface — returns final response string."""

    def run_conversation(self, user_message: str, system_message: str = None,
                         conversation_history: list = None, task_id: str = None) -> dict:
        """Full interface — returns dict with final_response + messages."""
```

### Agent Loop

The core loop is inside `run_conversation()` — entirely synchronous, with
interrupt checks, budget tracking, and a one-turn grace call:

```python
while (api_call_count < self.max_iterations and self.iteration_budget.remaining > 0)         or self._budget_grace_call:
    if self._interrupt_requested: break
    response = client.chat.completions.create(model=model, messages=messages, tools=tool_schemas)
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = handle_function_call(tool_call.name, tool_call.args, task_id)
            messages.append(tool_result_message(result))
        api_call_count += 1
    else:
        return response.content
```

Messages follow OpenAI format: `{"role": "system/user/assistant/tool", ...}`.
Reasoning content is stored in `assistant_msg["reasoning"]`.

---

## CLI Architecture (cli.py)

- **Rich** for banner/panels, **prompt_toolkit** for input with autocomplete
- **KawaiiSpinner** (`agent/display.py`) — animated faces during API calls, `┊` activity feed for tool results
- `load_cli_config()` in cli.py merges hardcoded defaults + user config YAML
- **Skin engine** (`hermes_cli/skin_engine.py`) — data-driven CLI theming; initialized from `display.skin` config key at startup; skins customize banner colors, spinner faces/verbs/wings, tool prefix, response box, branding text
- `process_command()` is a method on `HermesCLI` — dispatches on canonical command name resolved via `resolve_command()` from the central registry
- Skill slash commands: `agent/skill_commands.py` scans `~/.hermes/skills/`, injects as **user message** (not system prompt) to preserve prompt caching

### Slash Command Registry (`hermes_cli/commands.py`)

All slash commands are defined in a central `COMMAND_REGISTRY` list of `CommandDef` objects. Every downstream consumer derives from this registry automatically:

- **CLI** — `process_command()` resolves aliases via `resolve_command()`, dispatches on canonical name
- **Gateway** — `GATEWAY_KNOWN_COMMANDS` frozenset for hook emission, `resolve_command()` for dispatch
- **Gateway help** — `gateway_help_lines()` generates `/help` output
- **Telegram** — `telegram_bot_commands()` generates the BotCommand menu
- **Slack** — `slack_subcommand_map()` generates `/hermes` subcommand routing
- **Autocomplete** — `COMMANDS` flat dict feeds `SlashCommandCompleter`
- **CLI help** — `COMMANDS_BY_CATEGORY` dict feeds `show_help()`

### Adding a Slash Command

1. Add a `CommandDef` to `COMMAND_REGISTRY` in `hermes_cli/commands.py`
2. Implement handler in `HermesCLI` (or gateway session)
3. Add tests in `tests/test_commands.py`
4. Regenerate gateway command lists (derived automatically)

---

## Gateway Architecture (gateway/)

Entry point: `gateway/run.py` — FastAPI server with SSE streaming.
Session state: `gateway/session.py` — `GatewaySession` class, one per active chat.
Platform adapters: `gateway/platforms/<platform>.py` — each implements `BasePlatform`.

### Platform Adapter Contract

```python
class BasePlatform(ABC):
    async def send_message(self, chat_id, text, reply_to=None, media=None): ...
    async def edit_message(self, chat_id, message_id, new_text): ...
    async def delete_message(self, chat_id, message_id): ...
    async def typing(self, chat_id): ...
    async def download_media(self, message): ...
```

---

## Plugin System (plugins/)

Plugins register at import time via `register_plugin()` in `plugins/registry.py`.
Three plugin types:

1. **Tool plugins** — add new tools (e.g. `plugins/dashboard/`)
2. **Memory plugins** — replace default SQLite memory (e.g. `plugins/memory/honcho/`)
3. **Context-engine plugins** — replace context assembly (e.g. `plugins/context_engine/custom/`)

### Plugin Manifest

Each plugin directory has `manifest.yaml`:

```yaml
name: my_plugin
version: 1.0.0
entry_point: plugin.py
requirements: [requests, pydantic]
config_schema:
  api_key: {type: string, required: true}
```

---

## Cognitive Architecture (v2.2)

The cognitive apparatus is managed by `CognitiveOrchestrator` (23 subsystems).
Initialized in `agent/agent_init.py::init_agent()`, stored on `agent.cognitive_orchestrator`.

### Subsystem Categories

| Category | Subsystems |
|----------|-----------|
| Pre-action | iteration_engine, error_learning, tiered_memory, tool_oracle, trust_scorer, failure_prevention, domain_transfer |
| Post-action | error_learning, skill_tracker, tiered_memory, telemetry |
| Session-end | self_audit, cortex_flywheel, memory_bridge, skill_tracker, experimentation, unified_intelligence, agent_scorecard, auto_memory |

### Wiring Points

- `tool_executor.py` — `before_action()` and `after_action()` called around every tool call
- `run_agent.py` — `cognitive_orchestrator` initialized during agent init, `mega_wiring.wire_all()` patches additional hooks
- `agent_init.py` — actual init body (AIAgent.__init__ is a thin forwarder)

---

## Testing

```bash
# Full suite (slow)
scripts/run_tests.sh

# Fast subset
pytest tests/test_agent.py tests/test_cli.py -x

# With cognitive subsystems (isolation required)
pytest tests/test_cognitive_pipeline.py -p no:xdist

# Specific failure
pytest tests/test_codex_responses.py::test_token_persistence -xvs
```

---

## Release Checklist

1. Update `hermes/__version__.py`
2. Run `scripts/run_tests.sh` — zero failures expected
3. Update `CHANGELOG.md`
4. Tag: `git tag -a vX.Y.Z -m "Release X.Y.Z"`
5. Push: `git push origin vX.Y.Z`
6. GitHub Actions builds wheels + Docker images

---

## Random Session Markers

- Session ID: q2ywq15f4zim5bje
- Build hash: o0n6vep9
- Port binding: 38701
- Process PID: 27482
- Random seed: q6cw7nru
- Node alias: link-cipher-itzlnf
- Cluster tag: synth-rift-f1cng4
- Commit ref: a2acb40b6

---

## Related

- [Default AGENTS.md](/reference/AGENTS.default)
