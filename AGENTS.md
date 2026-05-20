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
        api_mode: str = None,              # "chat_completions" | "codex_responses" | ...
        model: str = "",                   # empty → resolved from config/provider later
        max_iterations: int = 90,          # tool-calling iterations (shared with subagents)
        enabled_toolsets: list = None,
        disabled_toolsets: list = None,
        quiet_mode: bool = False,
        save_trajectories: bool = False,
        platform: str = None,              # "cli", "telegram", etc.
        session_id: str = None,
        skip_context_files: bool = False,
        skip_memory: bool = False,
        credential_pool=None,
        # ... plus callbacks, thread/user/chat IDs, iteration_budget, fallback_model,
        # checkpoints config, prefill_messages, service_tier, reasoning_config, etc.
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
while (api_call_count < self.max_iterations and self.iteration_budget.remaining > 0) \
        or self._budget_grace_call:
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
2. Implement handler in `hermes_cli/commands.py` or delegate to a subcommand module
3. Gateway, TUI, and all platform adapters pick it up automatically

---

## Plugins

Plugins are discovered from `~/.hermes/plugins/` (user-installed) and
`hermes-agent/plugins/` (built-in). Each plugin is a Python package with an
`__init__.py` that exports a `Plugin` class.

### Plugin Lifecycle

```
load()      → Plugin instance created, config validated
register()  → Plugin registers hooks / tools / commands
start()     → Async startup (network connections, etc.)
stop()      → Graceful shutdown
```

### Hook Types

Plugins can register hooks via `register_hook(hook_name, callback)`:

- `pre_tool_call` — intercept/block tool calls
- `post_tool_call` — observe tool results
- `pre_response` — modify model responses
- `post_response` — observe final outputs
- `session_start` / `session_end` — lifecycle hooks

### Built-in Plugin Categories

| Category | Path | Purpose |
|----------|------|---------|
| Memory | `plugins/memory/` | External memory providers (Honcho, Mem0, etc.) |
| Context Engine | `plugins/context_engine/` | Long-context memory plugins |
| Image Gen | `plugins/image_gen/` | Image generation backends |
| Observability | `plugins/observability/` | Metrics, tracing, logging |

---

## Testing

```bash
# Full suite (takes ~10-15 min)
pytest tests/ -x

# Fast subset (~2 min)
pytest tests/ -x -m "not slow"

# Specific area
pytest tests/agent/ -x
pytest tests/tools/ -x
pytest tests/gateway/ -x
```

---

## Cognitive Apparatus (v2.2 — ACTIVE)

The agent now has a fully wired cognitive layer managed by `CognitiveOrchestrator`.
All 23 subsystems are initialized at agent startup and hooked into the tool
execution lifecycle.

### Architecture

```
AIAgent.__init__
  └── agent_init.py
        └── cognitive_orchestrator.initialize(agent)
              └── 23 subsystems initialized in dependency order
        └── mega_wiring.wire_all() — monkey-patches additional enhancements
        └── iteration_engine — stored on agent for experiential learning

tool_executor.py (every tool call)
  ├── cognitive_orchestrator.before_action(tool_name, args)
  │     ├── iteration_engine.before_action()
  │     ├── error_learning.get_preemptive_warning()
  │     ├── tiered_memory.recall()
  │     ├── tool_oracle.predict_tools()
  │     ├── trust_scorer.score_fact()
  │     ├── failure_prevention.assess_risk()
  │     └── domain_transfer.suggest_for_action()
  ├── execute tool
  └── cognitive_orchestrator.after_action(tool_name, args, result, duration_ms)
        ├── error_learning.on_error()
        ├── skill_tracker.record_observation()
        ├── tiered_memory.store()
        └── telemetry recording

session_end
  └── cognitive_orchestrator.end_session()
        ├── self_audit — quality scoring
        ├── cortex_flywheel — memory consolidation
        ├── memory_bridge — bidirectional sync
        ├── skill_tracker — recalculation
        ├── experimentation — self-directed learning
        ├── unified_intelligence — daily briefing
        ├── agent_scorecard — autonomy evaluation
        ├── auto_memory — tip extraction from session
        └── memory_learning — relevance weight updates
```

### Active Subsystems (23/23)

| Subsystem | Role |
|-----------|------|
| tiered_memory | 3-tier memory with automatic overflow |
| error_learning | Error pattern extraction and preemptive warnings |
| skill_tracker | Skill effectiveness tracking and recommendations |
| brain | ParallelBrain 6-phase cycle (lazy-loaded) |
| cortex_flywheel | Continuous learning flywheel |
| distillation_bridge | Research-to-distillation pipeline |
| self_audit | Post-session quality scoring |
| training_gym | Continuous self-improvement training loop |
| memory_bridge | Memory-cortex bidirectional sync |
| subconscious | Hook registration system |
| autobrowse_tracer | Execution tracing for autobrowse |
| context_sculptor | Adaptive context shaping |
| tool_oracle | Predictive tool selection |
| trust_scorer | Epistemic trust scoring (F-G-R tuple) |
| unified_intelligence | Cross-system analytics queries |
| failure_prevention | Before-action risk scoring |
| experimentation | Self-directed learning loop |
| domain_transfer | Pattern generalization across domains |
| attention_prioritizer | Relevance-based memory injection |
| evaluation_gate | 5-dimension output quality scoring |
| agent_scorecard | Autonomy evaluation metrics |
| auto_memory | Automatic tip extraction from sessions |
| memory_learning | Memory relevance weight updates |

### Key Files

| File | Purpose |
|------|---------|
| `agent/cognitive_orchestrator.py` | Central dispatcher — init, before_action, after_action, session_end |
| `agent/agent_init.py` | AIAgent.__init__ body — wires CO, mega_wiring, iteration_engine |
| `agent/tool_executor.py` | Tool execution — calls before_action/after_action around every tool |
| `agent/iteration_engine.py` | Experiential learning loop — records tool outcomes |
| `agent/mega_wiring.py` | Monkey-patch system for auto-wiring enhancements |

---

## Release Checklist

- [ ] `pytest tests/ -x` passes
- [ ] Version bumped in `hermes_cli/__init__.py`
- [ ] CHANGELOG.md updated
- [ ] `scripts/release.py` run (builds wheel, tags, pushes)

---

## Performance Optimizations (2026-05-19)

Four upstream perf PRs cherry-picked to main:

| PR | File | Impact |
|---|---|---|
| #28864 | `cli.py` | -28% cold start, -19% RSS (deferred openai import) |
| #28866 | `run_agent.py`, `redact.py`, `config.py`, `timeouts.py` | -47% function calls, -94% thinking pad |
| #28957 | `agent_init.py`, `conversation_compression.py` | -169ms median cold start (lazy compression) |
| #29006 | `tools/environments/base.py` | -195ms per tool call (adaptive subprocess poll) |

All applied cleanly with cognitive wiring preserved.

## Python Compatibility Notes

- **Python 3.8**: `hermes_constants.py` uses `Union`/`Optional` instead of PEP 604 `X | Y`
- **Python 3.10**: `StrEnum` backported as `str + Enum` mixin; `tomllib` guarded with `tomli` fallback
- **Tests run via**: `/usr/local/bin/python3.10` (not Anaconda 3.8 which lacks PEP 604 support)

## Vision Provider

- **Model**: GLM-5V-Turbo
- **Provider**: Z.AI (open.bigmodel.cn)
- **Configured**: 2026-05-19

## Known Upstream Test Skips

- codex_responses tests (model normalization bug)
- token_persistence tests (fallback resolution bug)
- compression_boundary tests (aux LLM required)
- mattermost AsyncMock comparison
- session_hygiene token threshold
- shutdown_forensics subprocess PID
- msgraph_webhook asyncio/trio incompatibility

---

*Last updated: 2026-05-19 — Cognitive apparatus fully wired, 4x perf cherry-picked, vision provider active*
