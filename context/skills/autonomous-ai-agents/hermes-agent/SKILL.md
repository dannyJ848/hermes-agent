---
name: hermes-agent
description: "Configure, extend, or contribute to Hermes Agent."
version: 2.0.0
author: Hermes Agent + Teknium
license: MIT
metadata:
  hermes:
    tags: [hermes, setup, configuration, multi-agent, spawning, cli, gateway, development]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [claude-code, codex, opencode]
---

# Hermes Agent

Hermes Agent is an open-source AI agent framework by Nous Research that runs in your terminal, messaging platforms, and IDEs. It belongs to the same category as Claude Code (Anthropic), Codex (OpenAI), and OpenClaw — autonomous coding and task-execution agents that use tool calling to interact with your system. Hermes works with any LLM provider (OpenRouter, Anthropic, OpenAI, DeepSeek, local models, and 15+ others) and runs on Linux, macOS, and WSL.

What makes Hermes different:

- **Self-improving through skills** — Hermes learns from experience by saving reusable procedures as skills. When it solves a complex problem, discovers a workflow, or gets corrected, it can persist that knowledge as a skill document that loads into future sessions. Skills accumulate over time, making the agent better at your specific tasks and environment.
- **Persistent memory across sessions** — remembers who you are, your preferences, environment details, and lessons learned. Pluggable memory backends (built-in, Honcho, Mem0, and more) let you choose how memory works.
- **Multi-platform gateway** — the same agent runs on Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email, and 10+ other platforms with full tool access, not just chat.
- **Provider-agnostic** — swap models and providers mid-workflow without changing anything else. Credential pools rotate across multiple API keys automatically.
- **Profiles** — run multiple independent Hermes instances with isolated configs, sessions, skills, and memory.
- **Extensible** — plugins, MCP servers, custom tools, webhook triggers, cron scheduling, and the full Python ecosystem.

People use Hermes for software development, research, system administration, data analysis, content creation, home automation, and anything else that benefits from an AI agent with persistent context and full system access.

**This skill helps you work with Hermes Agent effectively** — setting it up, configuring features, spawning additional agent instances, troubleshooting issues, finding the right commands and settings, and understanding how the system works when you need to extend or contribute to it.

**Docs:** https://hermes-agent.nousresearch.com/docs/

## Quick Start

```bash
# Install
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# Interactive chat (default)
hermes

# Single query
hermes chat -q "What is the capital of France?"

# Setup wizard
hermes setup

# Change model/provider
hermes model

# Check health
hermes doctor
```

---

## CLI Reference

### Global Flags

```
hermes [flags] [command]

  --version, -V             Show version
  --resume, -r SESSION      Resume session by ID or title
  --continue, -c [NAME]     Resume by name, or most recent session
  --worktree, -w            Isolated git worktree mode (parallel agents)
  --skills, -s SKILL        Preload skills (comma-separate or repeat)
  --profile, -p NAME        Use a named profile
  --yolo                    Skip dangerous command approval
  --pass-session-id         Include session ID in system prompt
```

No subcommand defaults to `chat`.

### Chat

```
hermes chat [flags]
  -q, --query TEXT          Single query, non-interactive
  -m, --model MODEL         Model (e.g. anthropic/claude-sonnet-4)
  -t, --toolsets LIST       Comma-separated toolsets
  --provider PROVIDER       Force provider (openrouter, anthropic, nous, etc.)
  -v, --verbose             Verbose output
  -Q, --quiet               Suppress banner, spinner, tool previews
  --checkpoints             Enable filesystem checkpoints (/rollback)
  --source TAG              Session source tag (default: cli)
```

### Configuration

```
hermes setup [section]      Interactive wizard (model|terminal|gateway|tools|agent)
hermes model                Interactive model/provider picker
hermes config               View current config
hermes config edit          Open config.yaml in $EDITOR
hermes config set KEY VAL   Set a config value
hermes config path          Print config.yaml path
hermes config env-path      Print .env path
hermes config check         Check for missing/outdated config
hermes config migrate       Update config with new options
hermes login [--provider P] OAuth login (nous, openai-codex)
hermes logout               Clear stored auth
hermes doctor [--fix]       Check dependencies and config
hermes status [--all]       Show component status
```

### Tools & Skills

```
hermes tools                Interactive tool enable/disable (curses UI)
hermes tools list           Show all tools and status
hermes tools enable NAME    Enable a toolset
hermes tools disable NAME   Disable a toolset

hermes skills list          List installed skills
hermes skills search QUERY  Search the skills hub
hermes skills install ID    Install a skill (ID can be a hub identifier OR a direct https://…/SKILL.md URL; pass --name to override when frontmatter has no name)
hermes skills inspect ID    Preview without installing
hermes skills config        Enable/disable skills per platform
hermes skills check         Check for updates
hermes skills update        Update outdated skills
hermes skills uninstall N   Remove a hub skill
hermes skills publish PATH  Publish to registry
hermes skills browse        Browse all available skills
hermes skills tap add REPO  Add a GitHub repo as skill source
```

### MCP Servers

```
hermes mcp serve            Run Hermes as an MCP server
hermes mcp add NAME         Add an MCP server (--url or --command)
hermes mcp remove NAME      Remove an MCP server
hermes mcp list             List configured servers
hermes mcp test NAME        Test connection
hermes mcp configure NAME   Toggle tool selection
```

### Gateway (Messaging Platforms)

```
hermes gateway run          Start gateway foreground
hermes gateway install      Install as background service
hermes gateway start/stop   Control the service
hermes gateway restart      Restart the service
hermes gateway status       Check status
hermes gateway setup        Configure platforms
```

Supported platforms: Telegram, Discord, Slack, WhatsApp, Signal, Email, SMS, Matrix, Mattermost, Home Assistant, DingTalk, Feishu, WeCom, BlueBubbles (iMessage), Weixin (WeChat), API Server, Webhooks. Open WebUI connects via the API Server adapter.

Platform docs: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/

### Sessions

```
hermes sessions list        List recent sessions
hermes sessions browse      Interactive picker
hermes sessions export OUT  Export to JSONL
hermes sessions rename ID T Rename a session
hermes sessions delete ID   Delete a session
hermes sessions prune       Clean up old sessions (--older-than N days)
hermes sessions stats       Session store statistics
```

### Cron Jobs

```
hermes cron list            List jobs (--all for disabled)
hermes cron create SCHED    Create: '30m', 'every 2h', '0 9 * * *'
hermes cron edit ID         Edit schedule, prompt, delivery
hermes cron pause/resume ID Control job state
hermes cron run ID          Trigger on next tick
hermes cron remove ID       Delete a job
hermes cron status          Scheduler status
```

### Webhooks

```
hermes webhook subscribe N  Create route at /webhooks/<name>
hermes webhook list         List subscriptions
hermes webhook remove NAME  Remove a subscription
hermes webhook test NAME    Send a test POST
```

### Profiles

```
hermes profile list         List all profiles
hermes profile create NAME  Create (--clone, --clone-all, --clone-from)
hermes profile use NAME     Set sticky default
hermes profile delete NAME  Delete a profile
hermes profile show NAME    Show details
hermes profile alias NAME   Manage wrapper scripts
hermes profile rename A B   Rename a profile
hermes profile export NAME  Export to tar.gz
hermes profile import FILE  Import from archive
```

### Credential Pools

```
hermes auth add             Interactive credential wizard
hermes auth list [PROVIDER] List pooled credentials
hermes auth remove P INDEX  Remove by provider + index
hermes auth reset PROVIDER  Clear exhaustion status
```

### Other

```
hermes insights [--days N]  Usage analytics
hermes update               Update to latest version
hermes pairing list/approve/revoke  DM authorization
hermes plugins list/install/remove  Plugin management
hermes honcho setup/status  Honcho memory integration (requires honcho plugin)
hermes memory setup/status/off  Memory provider config
hermes completion bash|zsh  Shell completions
hermes acp                  ACP server (IDE integration)
hermes claw migrate         Migrate from OpenClaw
hermes uninstall            Uninstall Hermes
```

---

## Slash Commands (In-Session)

Type these during an interactive chat session.

### Session Control
```
/new (/reset)        Fresh session
/clear               Clear screen + new session (CLI)
/retry               Resend last message
/undo                Remove last exchange
/title [name]        Name the session
/compress            Manually compress context
/stop                Kill background processes
/rollback [N]        Restore filesystem checkpoint
/background <prompt> Run prompt in background
/queue <prompt>      Queue for next turn
/resume [name]       Resume a named session
```

### Configuration
```
/config              Show config (CLI)
/model [name]        Show or change model
/personality [name]  Set personality
/reasoning [level]   Set reasoning (none|minimal|low|medium|high|xhigh|show|hide)
/verbose             Cycle: off → new → all → verbose
/voice [on|off|tts]  Voice mode
/yolo                Toggle approval bypass
/skin [name]         Change theme (CLI)
/statusbar           Toggle status bar (CLI)
```

### Tools & Skills
```
/tools               Manage tools (CLI)
/toolsets            List toolsets (CLI)
/skills              Search/install skills (CLI)
/skill <name>        Load a skill into session
/cron                Manage cron jobs (CLI)
/reload-mcp          Reload MCP servers
/plugins             List plugins (CLI)
```

### Gateway
```
/approve             Approve a pending command (gateway)
/deny                Deny a pending command (gateway)
/restart             Restart gateway (gateway)
/sethome             Set current chat as home channel (gateway)
/update              Update Hermes to latest (gateway)
/platforms (/gateway) Show platform connection status (gateway)
```

### Utility
```
/branch (/fork)      Branch the current session
/fast                Toggle priority/fast processing
/browser             Open CDP browser connection
/history             Show conversation history (CLI)
/save                Save conversation to file (CLI)
/paste               Attach clipboard image (CLI)
/image               Attach local image file (CLI)
```

### Info
```
/help                Show commands
/commands [page]     Browse all commands (gateway)
/usage               Token usage
/insights [days]     Usage analytics
/status              Session info (gateway)
/profile             Active profile info
```

### Exit
```
/quit (/exit, /q)    Exit CLI
```

---

## Key Paths & Config

```
~/.hermes/config.yaml       Main configuration
~/.hermes/.env              API keys and secrets
$HERMES_HOME/skills/        Installed skills
~/.hermes/sessions/         Session transcripts
~/.hermes/logs/             Gateway and error logs
~/.hermes/auth.json         OAuth tokens and credential pools
~/.hermes/hermes-agent/     Source code (if git-installed)
```

Profiles use `~/.hermes/profiles/<name>/` with the same layout.

### Config Sections

Edit with `hermes config edit` or `hermes config set section.key value`.

| Section | Key options |
|---------|-------------|
| `model` | `default`, `provider`, `base_url`, `api_key`, `context_length` |
| `agent` | `max_turns` (90), `tool_use_enforcement` |
| `terminal` | `backend` (local/docker/ssh/modal), `cwd`, `timeout` (180) |
| `compression` | `enabled`, `threshold` (0.50), `target_ratio` (0.20) |
| `display` | `skin`, `tool_progress`, `show_reasoning`, `show_cost` |
| `stt` | `enabled`, `provider` (local/groq/openai/mistral) |
| `tts` | `provider` (edge/elevenlabs/openai/minimax/mistral/neutts) |
| `memory` | `memory_enabled`, `user_profile_enabled`, `provider` |
| `security` | `tirith_enabled`, `website_blocklist` |
| `delegation` | `model`, `provider`, `base_url`, `api_key`, `max_iterations` (50), `reasoning_effort` |
| `checkpoints` | `enabled`, `max_snapshots` (50) |

Full config reference: https://hermes-agent.nousresearch.com/docs/user-guide/configuration

### Providers

20+ providers supported. Set via `hermes model` or `hermes setup`.

| Provider | Auth | Key env var |
|----------|------|-------------|
| OpenRouter | API key | `OPENROUTER_API_KEY` |
| Anthropic | API key | `ANTHROPIC_API_KEY` |
| Nous Portal | OAuth | `hermes auth` |
| OpenAI Codex | OAuth | `hermes auth` |
| GitHub Copilot | Token | `COPILOT_GITHUB_TOKEN` |
| Google Gemini | API key | `GOOGLE_API_KEY` or `GEMINI_API_KEY` |
| DeepSeek | API key | `DEEPSEEK_API_KEY` |
| xAI / Grok | API key | `XAI_API_KEY` |
| Hugging Face | Token | `HF_TOKEN` |
| Z.AI / GLM | API key | `GLM_API_KEY` |
| MiniMax | API key | `MINIMAX_API_KEY` |
| MiniMax CN | API key | `MINIMAX_CN_API_KEY` |
| Kimi / Moonshot | API key | `KIMI_API_KEY` |
| Alibaba / DashScope | API key | `DASHSCOPE_API_KEY` |
| Xiaomi MiMo | API key | `XIAOMI_API_KEY` |
| Kilo Code | API key | `KILOCODE_API_KEY` |
| AI Gateway (Vercel) | API key | `AI_GATEWAY_API_KEY` |
| OpenCode Zen | API key | `OPENCODE_ZEN_API_KEY` |
| OpenCode Go | API key | `OPENCODE_GO_API_KEY` |
| Qwen OAuth | OAuth | `hermes login --provider qwen-oauth` |
| Custom endpoint | Config | `model.base_url` + `model.api_key` in config.yaml |
| GitHub Copilot ACP | External | `COPILOT_CLI_PATH` or Copilot CLI |

Full provider docs: https://hermes-agent.nousresearch.com/docs/integrations/providers

### Toolsets

Enable/disable via `hermes tools` (interactive) or `hermes tools enable/disable NAME`.

| Toolset | What it provides |
|---------|-----------------|
| `web` | Web search and content extraction |
| `browser` | Browser automation (Browserbase, Camofox, or local Chromium) |
| `terminal` | Shell commands and process management |
| `file` | File read/write/search/patch |
| `code_execution` | Sandboxed Python execution |
| `vision` | Image analysis |
| `image_gen` | AI image generation |
| `tts` | Text-to-speech |
| `skills` | Skill browsing and management |
| `memory` | Persistent cross-session memory |
| `session_search` | Search past conversations |
| `delegation` | Subagent task delegation |
| `cronjob` | Scheduled task management |
| `clarify` | Ask user clarifying questions |
| `messaging` | Cross-platform message sending |
| `search` | Web search only (subset of `web`) |
| `todo` | In-session task planning and tracking |
| `rl` | Reinforcement learning tools (off by default) |
| `moa` | Mixture of Agents (off by default) |
| `homeassistant` | Smart home control (off by default) |

Tool changes take effect on `/reset` (new session). They do NOT apply mid-conversation to preserve prompt caching.

---

## Security & Privacy Toggles

Common "why is Hermes doing X to my output / tool calls / commands?" toggles — and the exact commands to change them. Most of these need a fresh session (`/reset` in chat, or start a new `hermes` invocation) because they're read once at startup.

### Secret redaction in tool output

Secret redaction is **off by default** — tool output (terminal stdout, `read_file`, web content, subagent summaries, etc.) passes through unmodified. If the user wants Hermes to auto-mask strings that look like API keys, tokens, and secrets before they enter the conversation context and logs:

```bash
hermes config set security.redact_secrets true       # enable globally
```

**Restart required.** `security.redact_secrets` is snapshotted at import time — toggling it mid-session (e.g. via `export HERMES_REDACT_SECRETS=true` from a tool call) will NOT take effect for the running process. Tell the user to run `hermes config set security.redact_secrets true` in a terminal, then start a new session. This is deliberate — it prevents an LLM from flipping the toggle on itself mid-task.

Disable again with:
```bash
hermes config set security.redact_secrets false
```

### PII redaction in gateway messages

Separate from secret redaction. When enabled, the gateway hashes user IDs and strips phone numbers from the session context before it reaches the model:

```bash
hermes config set privacy.redact_pii true    # enable
hermes config set privacy.redact_pii false   # disable (default)
```

### Command approval prompts

By default (`approvals.mode: manual`), Hermes prompts the user before running shell commands flagged as destructive (`rm -rf`, `git reset --hard`, etc.). The modes are:

- `manual` — always prompt (default)
- `smart` — use an auxiliary LLM to auto-approve low-risk commands, prompt on high-risk
- `off` — skip all approval prompts (equivalent to `--yolo`)

```bash
hermes config set approvals.mode smart       # recommended middle ground
hermes config set approvals.mode off         # bypass everything (not recommended)
```

Per-invocation bypass without changing config:
- `hermes --yolo …`
- `export HERMES_YOLO_MODE=1`

Note: YOLO / `approvals.mode: off` does NOT turn off secret redaction. They are independent.

### Shell hooks allowlist

Some shell-hook integrations require explicit allowlisting before they fire. Managed via `~/.hermes/shell-hooks-allowlist.json` — prompted interactively the first time a hook wants to run.

### Disabling the web/browser/image-gen tools

To keep the model away from network or media tools entirely, open `hermes tools` and toggle per-platform. Takes effect on next session (`/reset`). See the Tools & Skills section above.

---

## Voice & Transcription

### STT (Voice → Text)

Voice messages from messaging platforms are auto-transcribed.

Provider priority (auto-detected):
1. **Local faster-whisper** — free, no API key: `pip install faster-whisper`
2. **Groq Whisper** — free tier: set `GROQ_API_KEY`
3. **OpenAI Whisper** — paid: set `VOICE_TOOLS_OPENAI_KEY`
4. **Mistral Voxtral** — set `MISTRAL_API_KEY`

Config:
```yaml
stt:
  enabled: true
  provider: local        # local, groq, openai, mistral
  local:
    model: base          # tiny, base, small, medium, large-v3
```

### TTS (Text → Voice)

| Provider | Env var | Free? |
|----------|---------|-------|
| Edge TTS | None | Yes (default) |
| ElevenLabs | `ELEVENLABS_API_KEY` | Free tier |
| OpenAI | `VOICE_TOOLS_OPENAI_KEY` | Paid |
| MiniMax | `MINIMAX_API_KEY` | Paid |
| Mistral (Voxtral) | `MISTRAL_API_KEY` | Paid |
| NeuTTS (local) | None (`pip install neutts[all]` + `espeak-ng`) | Free |

Voice commands: `/voice on` (voice-to-voice), `/voice tts` (always voice), `/voice off`.

---

## Spawning Additional Hermes Instances

Run additional Hermes processes as fully independent subprocesses — separate sessions, tools, and environments.

### When to Use This vs delegate_task

| | `delegate_task` | Spawning `hermes` process |
|-|-----------------|--------------------------|
| Isolation | Separate conversation, shared process | Fully independent process |
| Duration | Minutes (bounded by parent loop) | Hours/days |
| Tool access | Subset of parent's tools | Full tool access |
| Interactive | No | Yes (PTY mode) |
| Use case | Quick parallel subtasks | Long autonomous missions |

### One-Shot Mode

```
terminal(command="hermes chat -q 'Research GRPO papers and write summary to ~/research/grpo.md'", timeout=300)

# Background for long tasks:
terminal(command="hermes chat -q 'Set up CI/CD for ~/myapp'", background=true)
```

### Interactive PTY Mode (via tmux)

Hermes uses prompt_toolkit, which requires a real terminal. Use tmux for interactive spawning:

```
# Start
terminal(command="tmux new-session -d -s agent1 -x 120 -y 40 'hermes'", timeout=10)

# Wait for startup, then send a message
terminal(command="sleep 8 && tmux send-keys -t agent1 'Build a FastAPI auth service' Enter", timeout=15)

# Read output
terminal(command="sleep 20 && tmux capture-pane -t agent1 -p", timeout=5)

# Send follow-up
terminal(command="tmux send-keys -t agent1 'Add rate limiting middleware' Enter", timeout=5)

# Exit
terminal(command="tmux send-keys -t agent1 '/exit' Enter && sleep 2 && tmux kill-session -t agent1", timeout=10)
```

### Multi-Agent Coordination

```
# Agent A: backend
terminal(command="tmux new-session -d -s backend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t backend 'Build REST API for user management' Enter", timeout=15)

# Agent B: frontend
terminal(command="tmux new-session -d -s frontend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t frontend 'Build React dashboard for user management' Enter", timeout=15)

# Check progress, relay context between them
terminal(command="tmux capture-pane -t backend -p | tail -30", timeout=5)
terminal(command="tmux send-keys -t frontend 'Here is the API schema from the backend agent: ...' Enter", timeout=5)
```

### Session Resume

```
# Resume most recent session
terminal(command="tmux new-session -d -s resumed 'hermes --continue'", timeout=10)

# Resume specific session
terminal(command="tmux new-session -d -s resumed 'hermes --resume 20260225_143052_a1b2c3'", timeout=10)
```

### Tips

- **Prefer `delegate_task` for quick subtasks** — less overhead than spawning a full process
- **Use `-w` (worktree mode)** when spawning agents that edit code — prevents git conflicts
- **Set timeouts** for one-shot mode — complex tasks can take 5-10 minutes
- **Use `hermes chat -q` for fire-and-forget** — no PTY needed
- **Use tmux for interactive sessions** — raw PTY mode has `\r` vs `\n` issues with prompt_toolkit
- **For scheduled tasks**, use the `cronjob` tool instead of spawning — handles delivery and retry

### ⚠️ CRITICAL: Never Spawn Autonomous Agents Without Explicit Permission

**User preference (May 17, 2026):** The user explicitly rejected an autonomous Hermes agent running on DGX with the message: *"stop the autonomous hermes. i didn't want that"*

**Rule:** Before spawning ANY persistent autonomous process (screen session, tmux, cron job, daemon, or background task), you MUST get explicit user confirmation. Do NOT assume the user wants autonomous agents running just because the infrastructure exists.

**What counts as "autonomous":**
- Screen/tmux sessions running `hermes` or `run_agent` loops
- Cron jobs that invoke Hermes
- Systemd services for agent processes
- Background `hermes chat -q` loops
- Any process that makes API calls and executes tools without user oversight

**What does NOT require permission:**
- One-shot `hermes chat -q` commands that return immediately
- `delegate_task` subagents (bounded, parent-supervised)
- Manual tool execution during an interactive session
- Starting vLLM or other infrastructure (not an agent)

**Always ask:** "Do you want me to start an autonomous agent that will run continuously and execute tools on its own?" If the answer is no or unclear, do NOT start it.

---

## Troubleshooting

### Voice not working
1. Check `stt.enabled: true` in config.yaml
2. Verify provider: `pip install faster-whisper` or set API key
3. In gateway: `/restart`. In CLI: exit and relaunch.

### Tool not available
1. `hermes tools` — check if toolset is enabled for your platform
2. Some tools need env vars (check `.env`)
3. `/reset` after enabling tools

### Model/provider issues
1. `hermes doctor` — check config and dependencies
2. `hermes login` — re-authenticate OAuth providers
3. Check `.env` has the right API key
4. **Copilot 403**: `gh auth login` tokens do NOT work for Copilot API. You must use the Copilot-specific OAuth device code flow via `hermes model` → GitHub Copilot.

### Changes not taking effect
- **Tools/skills:** `/reset` starts a new session with updated toolset
- **Config changes:** In gateway: `/restart`. In CLI: exit and relaunch.
- **Code changes:** Restart the CLI or gateway process

### Skills not showing
1. `hermes skills list` — verify installed
2. `hermes skills config` — check platform enablement
3. Load explicitly: `/skill name` or `hermes -s name`

### Gateway issues
Check logs first:
```bash
grep -i "failed to send\|error" ~/.hermes/logs/gateway.log | tail -20
```

Common gateway problems:
- **Gateway dies on SSH logout**: Enable linger: `sudo loginctl enable-linger $USER`
- **Gateway dies on WSL2 close**: WSL2 requires `systemd=true` in `/etc/wsl.conf` for systemd services to work. Without it, gateway falls back to `nohup` (dies when session closes).
- **Gateway crash loop**: Reset the failed state: `systemctl --user reset-failed hermes-gateway`

### Platform-specific issues
- **Discord bot silent**: Must enable **Message Content Intent** in Bot → Privileged Gateway Intents.
- **Slack bot only works in DMs**: Must subscribe to `message.channels` event. Without it, the bot ignores public channels.
- **Windows HTTP 400 "No models provided"**: Config file encoding issue (BOM). Ensure `config.yaml` is saved as UTF-8 without BOM.

### Auxiliary models not working
If `auxiliary` tasks (vision, compression, session_search) fail silently, the `auto` provider can't find a backend. Either set `OPENROUTER_API_KEY` or `GOOGLE_API_KEY`, or explicitly configure each auxiliary task's provider:
```bash
hermes config set auxiliary.vision.provider <your_provider>
hermes config set auxiliary.vision.model <model_name>
```

---

## Where to Find Things

| Looking for... | Location |
|----------------|----------|
| Config options | `hermes config edit` or [Configuration docs](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |
| Available tools | `hermes tools list` or [Tools reference](https://hermes-agent.nousresearch.com/docs/reference/tools-reference) |
| Slash commands | `/help` in session or [Slash commands reference](https://hermes-agent.nousresearch.com/docs/reference/slash-commands) |
| Skills catalog | `hermes skills browse` or [Skills catalog](https://hermes-agent.nousresearch.com/docs/reference/skills-catalog) |
| Provider setup | `hermes model` or [Providers guide](https://hermes-agent.nousresearch.com/docs/integrations/providers) |
| Platform setup | `hermes gateway setup` or [Messaging docs](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/) |
| MCP servers | `hermes mcp list` or [MCP guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) |
| Profiles | `hermes profile list` or [Profiles docs](https://hermes-agent.nousresearch.com/docs/user-guide/profiles) |
| Cron jobs | `hermes cron list` or [Cron docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron) |
| Memory | `hermes memory status` or [Memory docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) |
| Env variables | `hermes config env-path` or [Env vars reference](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) |
| CLI commands | `hermes --help` or [CLI reference](https://hermes-agent.nousresearch.com/docs/reference/cli-commands) |
| Gateway logs | `~/.hermes/logs/gateway.log` |
| Session files | `~/.hermes/sessions/` or `hermes sessions browse` |
| Source code | `~/.hermes/hermes-agent/` |

---

## Contributor Quick Reference

For occasional contributors and PR authors. Full developer docs: https://hermes-agent.nousresearch.com/docs/developer-guide/

### Project Layout

```
hermes-agent/
├── run_agent.py          # AIAgent — core conversation loop
├── model_tools.py        # Tool discovery and dispatch
├── toolsets.py           # Toolset definitions
├── cli.py                # Interactive CLI (HermesCLI)
├── hermes_state.py       # SQLite session store
├── agent/                # Prompt builder, context compression, memory, model routing, credential pooling, skill dispatch
├── hermes_cli/           # CLI subcommands, config, setup, commands
│   ├── commands.py       # Slash command registry (CommandDef)
│   ├── config.py         # DEFAULT_CONFIG, env var definitions
│   └── main.py           # CLI entry point and argparse
├── tools/                # One file per tool
│   └── registry.py       # Central tool registry
├── gateway/              # Messaging gateway
│   └── platforms/        # Platform adapters (telegram, discord, etc.)
├── cron/                 # Job scheduler
├── tests/                # ~3000 pytest tests
└── website/              # Docusaurus docs site
```

Config: `~/.hermes/config.yaml` (settings), `~/.hermes/.env` (API keys).

### Adding a Tool (3 files)

**1. Create `tools/your_tool.py`:**
```python
import json, os
from tools.registry import registry

def check_requirements() -> bool:
    return bool(os.getenv("EXAMPLE_API_KEY"))

def example_tool(param: str, task_id: str = None) -> str:
    return json.dumps({"success": True, "data": "..."})

registry.register(
    name="example_tool",
    toolset="example",
    schema={"name": "example_tool", "description": "...", "parameters": {...}},
    handler=lambda args, **kw: example_tool(
        param=args.get("param", ""), task_id=kw.get("task_id")),
    check_fn=check_requirements,
    requires_env=["EXAMPLE_API_KEY"],
)
```

**2. Add to `toolsets.py`** → `_HERMES_CORE_TOOLS` list.

Auto-discovery: any `tools/*.py` file with a top-level `registry.register()` call is imported automatically — no manual list needed.

All handlers must return JSON strings. Use `get_hermes_home()` for paths, never hardcode `~/.hermes`.

### Adding a Slash Command

1. Add `CommandDef` to `COMMAND_REGISTRY` in `hermes_cli/commands.py`
2. Add handler in `cli.py` → `process_command()`
3. (Optional) Add gateway handler in `gateway/run.py`

All consumers (help text, autocomplete, Telegram menu, Slack mapping) derive from the central registry automatically.

### Adding Self-Improvement Systems

**Critical rule: Integrate INTO Hermes source code, not as standalone scripts in ~/subconscious/.**

The user gets frustrated when systems are built in `~/subconscious/` or external files but never wired into the actual agent loop. Every cognitive system must be integrated into `cli.py`, `run_agent.py`, or `tools/` where Hermes executes.

**Correct pattern:**
1. Build prototype in `~/subconscious/` (acceptable for testing only)
2. Find integration point in `~/hermes-agent/` (`cli.py`, `run_agent.py`, `tools/`)
3. Inject hooks/methods directly into hermes source
4. Register tools via `registry.register()`
5. Test with `venv/bin/python`
6. Ask user to restart

**Never declare done until Hermes core is patched.**

| System Type | Inject Into | Pattern |
|-------------|-------------|---------|
| Auto-resume / handoff | `cli.py` `HermesCLI.__init__` | Check for pending handoff file before session ID assignment |
| Context pressure actions | `run_agent.py` `_compress_context` | Trigger after compression count threshold |
| New tools | `tools/<name>_tool.py` | `registry.register()` at module level |
| Tool call tracking | `hermes_cli/plugins.py` `dispatch_tool` | Log in `finally` block |
| Session-end hooks | `run_agent.py` session cleanup | Call before session DB close |
| Startup checks | `cli.py` `main()` before agent init | Run health checks, show warnings |
| Iteration engine | `run_agent.py` tool execution paths | Pre/post action hooks in `_invoke_tool` and `_execute_tool_calls_sequential` |
| Blackboard / tool cache | `run_agent.py` `AIAgent.__init__` | Initialize alongside other systems |
| Multi-agent coordinator | `run_agent.py` or new dispatch hook | Wire into delegate_task system |
| **Cognitive orchestrator** | **`run_agent.py` `AIAgent.__init__`** | **Import and initialize `CognitiveOrchestrator` after memory setup. Must pre-import `plugins` package via `importlib.util` before `hermes_cli.plugins` to prevent module shadowing. See `references/module-shadowing-fix-may15-2026.md`.** |

**Cognitive Orchestrator Initialization Pattern:**

The cognitive orchestrator provides 20 subsystems (tiered_memory, error_learning, skill_tracker, brain, cortex_flywheel, etc.) but does NOT auto-load. It must be explicitly initialized in `run_agent.py`:

```python
# In AIAgent.__init__, AFTER memory setup:
from agent.cognitive_orchestrator import CognitiveOrchestrator
self.cognitive_orchestrator = CognitiveOrchestrator(self)
self.cognitive_orchestrator.initialize_cognitive_systems()
```

**Critical:** The cognitive orchestrator must be initialized AFTER the module shadowing fix (pre-import plugins/gateway packages). If `hermes_cli.plugins` shadows the `plugins` package, the orchestrator's subsystem imports will fail silently.

**Verification:**
```python
from agent.cognitive_orchestrator import get_orchestrator
orch = get_orchestrator()
status = orch.get_status()
print(f"Active subsystems: {status['active_count']}/20")
# Should show 20/20 when fully wired
```

**Subsystem list (20 total):**
1. tiered_memory
2. error_learning
3. skill_tracker
4. brain
5. cortex_flywheel
6. memory_cortex_bridge
7. distillation_bridge
8. subconscious_hook_wiring
9. autobrowse_tracer
10. skill_effectiveness_tracker
11. training_gym
12. self_audit_engine
13. loop_guard
14. intent_verifier
15. proactive_tip_injector
16. token_budget_tracker
17. confidence_calibrator
18. context_pressure_gauge
19. iteration_engine
20. multi_agent_blackboard

**Note:** Many of these subsystems are "orphaned" — they exist in `agent/` but their hooks are never called in the main loop. The orchestrator initializes them but the agent loop must also call their hooks (before_action/after_action) for them to be active. See the "Orphaned Systems" section below.

**Anti-pattern:** Building `~/subconscious/hermes_thing.py` that never gets imported by Hermes. These scripts are orphaned code.

**Anti-pattern:** Building `~/subconscious/hermes_thing.py` that never gets imported by Hermes. These scripts are orphaned code.

**Correct pattern for bulk integration:**
When moving multiple modules from `~/subconscious/` into hermes source:
1. Use `execute_code` with Python for bulk file copies — NOT terminal loops (hit `same_tool_failure_halt` after 5 failures)
2. Update all imports: `from agent.X import ...` or `from tools.X import ...`
3. Remove all `sys.path.insert("~/subconscious")` calls
4. Clear all `__pycache__` directories to prevent stale bytecode from referencing old paths
5. Update configuration files (cron, MEMORY.md, SKILL.md) with new paths
6. Restart hermes to clear loaded module state

**Verification after integration:**
1. `venv/bin/python -c "import agent.my_module"` — import test
2. `venv/bin/python -c "from tools.registry import discover_builtin_tools; print('my_tool' in [m for m in discover_builtin_tools()])"` — registration test
3. Start Hermes, verify tool appears in `/tools` list
4. Trigger the condition and verify action fires
5. **Restart Hermes** after modifying `cli.py` or `run_agent.py`
6. Verify old `~/subconscious/` directory is NOT recreated (check with `lsof` if it is)

---

### Module Shadowing Fix (May 15 2026)

**Problem:** When `hermes_cli.plugins` is imported before the `plugins/` directory package, Python registers `plugins` in `sys.modules` pointing to `hermes_cli/plugins.py` (a file, not a package). This breaks ALL `plugins.X` imports (e.g., `plugins.memory`).

**Symptom:**
```
WARNING:run_agent:Memory provider plugin init failed: No module named 'plugins.memory'; 'plugins' is not a package
```

**Root cause:** The `plugins` key in `sys.modules` points to a file module (`hermes_cli/plugins.py`) instead of a package (`plugins/__init__.py`). All subsequent `import plugins.X` lookups fail because `plugins` is not a package.

**Fix:** Pre-import the `plugins` package at the top of `run_agent.py` using `importlib.util` before `hermes_cli.plugins` can shadow it:

```python
# === PATCH: ensure plugins package is imported before anything else shadows it ===
import sys, os, importlib.util
_plugins_pkg_dir = os.path.join(os.path.dirname(__file__), 'plugins')
if os.path.isdir(_plugins_pkg_dir):
    _plugins_spec = importlib.util.spec_from_file_location(
        "plugins",
        os.path.join(_plugins_pkg_dir, "__init__.py"),
        submodule_search_locations=[_plugins_pkg_dir]
    )
    _plugins_mod = importlib.util.module_from_spec(_plugins_spec)
    sys.modules["plugins"] = _plugins_mod
    _plugins_spec.loader.exec_module(_plugins_mod)
# ================================================================================
```

**Same pattern affects `gateway` package** when `hermes_cli/gateway.py` exists. The gateway package (directory) is shadowed by the CLI file, breaking all `gateway.X` imports (e.g., `gateway.status`, `gateway.session_context`).

**Fix for gateway shadowing:**
```python
# Add to run_agent.py BEFORE any hermes_cli imports
import importlib.util
_gateway_spec = importlib.util.spec_from_file_location(
    "gateway",
    "/path/to/hermes-agent/gateway/__init__.py",
    submodule_search_locations=["/path/to/hermes-agent/gateway"]
)
_gateway_mod = importlib.util.module_from_spec(_gateway_spec)
sys.modules["gateway"] = _gateway_mod
_gateway_spec.loader.exec_module(_gateway_mod)
```

**Wrapper script pattern (for systemd services):**
When running Hermes as a systemd service, the pre-import in run_agent.py may not execute early enough. Create a wrapper script that pre-imports BOTH packages before importing run_agent:

```python
# run_hermes_dgx_fixed.py — wrapper for DGX systemd
import sys
import os
import importlib.util

project_root = "/data/SpecForge/hermes-agent"
sys.path.insert(0, project_root)

# Step 1: Pre-load gateway package
gateway_init = os.path.join(project_root, "gateway", "__init__.py")
if os.path.exists(gateway_init) and "gateway" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "gateway",
        gateway_init,
        submodule_search_locations=[os.path.join(project_root, "gateway")]
    )
    gateway_pkg = importlib.util.module_from_spec(spec)
    sys.modules["gateway"] = gateway_pkg
    spec.loader.exec_module(gateway_pkg)

# Step 2: Pre-load plugins package
plugins_init = os.path.join(project_root, "plugins", "__init__.py")
if os.path.exists(plugins_init) and "plugins" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "plugins",
        plugins_init,
        submodule_search_locations=[os.path.join(project_root, "plugins")]
    )
    plugins_pkg = importlib.util.module_from_spec(spec)
    sys.modules["plugins"] = plugins_pkg
    spec.loader.exec_module(plugins_pkg)

# Step 3: Import and run main
from run_agent import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
```

**Systemd service using wrapper (DGX with vLLM dependency):**
```ini
[Unit]
Description=Hermes Agent DGX (Qwen3.6-27B-Uncensored + Dynamic LoRA)
After=docker.service
Requires=docker.service
Wants=vllm-base-lora.service

[Service]
Type=simple
User=djg6228
WorkingDirectory=/data/SpecForge/hermes-agent
Environment=PYTHONPATH=/data/SpecForge/hermes-agent
Environment=HOME=/home/djg6228
Environment=VIRTUAL_ENV=/data/SpecForge/hermes-agent/venv
ExecStart=/data/SpecForge/hermes-agent/venv/bin/python /data/SpecForge/hermes-agent/run_hermes_dgx_fixed.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hermes-dgx

[Install]
WantedBy=multi-user.target
```

**CRITICAL: vLLM must have `--enable-auto-tool-choice` and `--tool-call-parser`**

Without these flags, Hermes fails immediately with:
```
HTTP 400: "auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set
```

**vLLM launch with tool calling (verified May 16, 2026):**
```bash
docker run -d --name vllm-base-lora \
  --runtime nvidia --gpus all -p 8000:8000 \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints:/data/SpecForge/custom_dflash/checkpoints \
  -e CUDA_VISIBLE_DEVICES=0 \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --max-model-len 131072 \
  --enable-lora \
  --max-lora-rank 256 \
  --lora-modules custom-model=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --speculative-config '{"method": "dflash", "model": "/data/models/Qwen3.5-27B-DFlash", "num_speculative_tokens": 5}' \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 256 \
  --gpu-memory-utilization 0.95 \
  --dtype bfloat16 \
  --trust-remote-code \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

**SSH timeout during vLLM initialization (expected):**
DGX becomes unresponsive to SSH for 5-10 minutes during vLLM startup due to CUDA graph capture. This is NORMAL. Wait for vLLM to finish before attempting SSH or starting Hermes service.

**Verification:**
```python
import sys
print(sys.modules['plugins'].__file__)   # Should end with plugins/__init__.py
print(sys.modules['gateway'].__file__)   # Should end with gateway/__init__.py
import plugins.memory     # Should succeed
import gateway.status      # Should succeed
```

**Pitfall — Old process still running:**
After fixing module shadowing, kill any old Hermes processes that were started before the fix. They continue running with broken imports and cause confusing error logs:
```bash
# Kill old Hermes (not the fixed wrapper)
for pid in $(ps aux | grep "venv/bin/hermes" | grep -v "run_hermes_fixed" | grep -v grep | awk '{print $2}'); do
    kill -9 $pid
done
```

**Pitfall — Web search DDGS backend broken in v0.13.0:**
Hermes v0.13.0 has a package name mismatch for the DuckDuckGo search backend. The code imports `ddgs` but the package was renamed from `duckduckgo_search` to `ddgs` in v9.x. This causes web search to fail even when the package is installed.

**Symptom:**
```
Web tools are not configured — set EXA_API_KEY, FIRECRAWL_API_KEY, or TAVILY_API_KEY
```
Or:
```
{"success": false, "error": "ddgs package is not installed — run `pip install ddgs`"}
```

**Fix:**
```bash
# Install the correct package name
/data/SpecForge/hermes-agent/venv/bin/pip install ddgs

# Fix import in tools/web_tools.py (line ~219)
# OLD: import ddgs
# NEW: from ddgs import DDGS as ddgs
sed -i 's/import ddgs/from ddgs import DDGS as ddgs/' /data/SpecForge/hermes-agent/tools/web_tools.py

# Fix import in tools/web_providers/ddgs.py (line ~71)
# OLD: from ddgs import DDGS
# NEW: from duckduckgo_search import DDGS  (if using old package)
# OR: from ddgs import DDGS  (if using new package)
```

**Verification:**
```bash
python3 -c "
import sys
sys.path.insert(0, '/data/SpecForge/hermes-agent')
from tools.web_tools import web_search_tool
result = web_search_tool('test', limit=1)
print(result)
"
```

**Config for DDGS:**
```yaml
web:
  backend: ddgs  # or web_search.backend: ddgs
```

DDGS requires no API key and works out of the box once the import path is fixed.

**Pitfall — Terminal tool backend selection:**
The `terminal` tool uses environment variables to select local vs SSH backend:
- `TERMINAL_ENV=local` — runs commands locally (default)
- `TERMINAL_ENV=ssh` — runs commands on remote host via SSH
- `TERMINAL_SSH_HOST=<hostname>` — SSH target host
- `TERMINAL_SSH_USER=<username>` — SSH username

Set in systemd service or shell environment:
```ini
Environment=TERMINAL_ENV=ssh
Environment=TERMINAL_SSH_HOST=macbook
Environment=TERMINAL_SSH_USER=dannygomez
```

The terminal tool returns a JSON string (not a dict), so parse with `json.loads()`:
```python
import json
result = terminal_tool("echo test")
data = json.loads(result)  # {"output": "test\n", "exit_code": 0, "error": null}
```

**Pitfall — SSH access lost after DGX restart:**
After restarting the DGX server, SSH may reject connections if `~/.ssh/authorized_keys` was reset or SSH config changed. The symptom is `Connection closed by <IP> port 22` immediately after key authentication. Fix requires console access (keyboard/monitor) to re-add the SSH key to `~/.ssh/authorized_keys`.

**References:**
- `references/module-shadowing-fix-may15-2026.md` — Full investigation and fix
- `references/cognitive-orchestrator-20-subsystems-may15-2026.md` — How this fix enables 20/20 cognitive subsystems
- `references/gateway-module-shadowing-may16-2026.md` — Gateway-specific investigation and wrapper script pattern

---

### Old Self-Improvement Systems (Deprecated)

The following systems referenced in earlier versions are no longer active:
- `hermes_brain.py` — replaced by direct integration into `cli.py` and `run_agent.py`
- `loop_guard.py` — replaced by tool intelligence in `hermes_cli/plugins.py`
- `self_healing_dispatch.py` — replaced by adaptive timeout system
- `failure_post_mortem.py` — replaced by session-end extraction hooks
- `intent_verifier.py` — replaced by LLM judge in `subconscious/llm_judge.py`
- `proactive_tip_injector.py` — replaced by GovernorV2 in distillation plugin
- `token_budget_tracker.py` — replaced by context pressure gauge
- `confidence_calibrator.py` — not currently active

**Current active systems (all integrated into hermes source):**
- Context pressure gauge (`tools/context_pressure_gauge.py`)
- Tool intelligence router (`hermes_cli/plugins.py`)
- Adaptive timeout (`tools/adaptive_timeout.py`)
- Session DB with compression lineage (`hermes_state.py`)
- Distillation plugin with GovernorV2 (`~/.hermes/plugins/distillation/`)
- LLM judge (`agent/llm_judge.py`)
- Manual triggers (`agent/hermes_manual_triggers.py`)
- Unified daemon (`agent/hermes_unified_daemon.py`)
- Iteration engine (`agent/iteration_engine.py`)
- Multi-agent blackboard (`agent/multi_agent_blackboard.py`)
- Multi-agent coordinator (`agent/multi_agent_coordinator.py`)
- Self-diagnostic tool (`tools/self_diagnostic.py`)
- Skill generator (`tools/skill_generator.py`)
- Plan executor (`tools/plan_executor.py`)
- Hands/GUI automation (`tools/hands.py`)
- Cortex learning (`agent/cortex_learning.py`)

**ORPHANED SYSTEMS (files present but NEVER imported in run_agent.py):**
These modules exist in `agent/` but are dead code — not wired into the agent loop:

| Module | Size | Status |
|--------|------|--------|
| `brain.py` | 34KB | ORPHANED — ParallelBrain 6-phase cycle never runs |
| `training_gym.py` | 22KB | ORPHANED — continuous training loop never runs |
| `self_audit_engine.py` | 10KB | ORPHANED — post-session quality scoring never runs |
| `cortex_flywheel.py` | 16KB | ORPHANED — flywheel cycle never runs |
| `tiered_memory.py` | 24KB | ORPHANED — 3-tier memory never runs |
| `memory_cortex_bridge.py` | 17KB | ORPHANED — memory sync never runs |
| `distillation_bridge.py` | 39KB | ORPHANED — research-to-distillation pipeline never runs |
| `subconscious_hook_wiring.py` | 14KB | ORPHANED — hook system wires nothing |
| `autobrowse_tracer.py` | 9KB | ORPHANED — execution tracing never runs |
| `skill_effectiveness_tracker.py` | 18KB | ORPHANED — skill quality tracking never runs |
| `error_learning.py` | 19KB | IMPORT_ONLY — imported but hooks never called |

**Total orphaned code: ~211KB (~5,500 lines, ~15% of agent/ directory).**

**Audit methodology:**
```python
# Check if a module is actually wired into the agent loop
import re

with open('run_agent.py', 'r') as f:
    content = f.read()

# A module is WIRED if:
# 1. It's imported: from agent.MODULE import ...
# 2. Its hooks are called: module_name.method_name(...)
# 3. Both in run_agent.py (main loop) or cli.py (startup)

modules = ['brain', 'training_gym', 'cortex_flywheel', 'tiered_memory']
for mod in modules:
    imported = f'from agent.{mod}' in content
    called = any(f'{mod}.' in line for line in content.split('\n'))
    status = 'WIRED' if imported and called else 'ORPHANED'
    print(f'{mod}: {status}')
```

**To activate an orphaned system:**
1. Import it in `run_agent.py` (or `cli.py` for startup systems)
2. Call its initialization method in `AIAgent.__init__`
3. Call its hooks in the main loop (before_action/after_action pattern)
4. Verify with the audit script above
5. Restart Hermes

**All cognitive systems are now in `agent/` or `tools/` — no external `~/subconscious/` dependencies remain.**

### Agent Loop (High Level)

```
run_conversation():
  1. Build system prompt
  2. Loop while iterations < max:
     a. Call LLM (OpenAI-format messages + tool schemas)
     b. If tool_calls → dispatch each via handle_function_call() → append results → continue
     c. If text response → return
  3. Context compression triggers automatically near token limit
```

### Testing

```bash
python -m pytest tests/ -o 'addopts=' -q   # Full suite
python -m pytest tests/tools/ -q            # Specific area
```

- Tests auto-redirect `HERMES_HOME` to temp dirs — never touch real `~/.hermes/`
- Run full suite before pushing any change
- Use `-o 'addopts='` to clear any baked-in pytest flags

### Commit Conventions

```
type: concise subject line

Optional body.
```

Types: `fix:`, `feat:`, `refactor:`, `docs:`, `chore:`

### Key Rules

- **Never break prompt caching** — don't change context, tools, or system prompt mid-conversation
- **Message role alternation** — never two assistant or two user messages in a row
- Use `get_hermes_home()` from `hermes_constants` for all paths (profile-safe)
- Config values go in `config.yaml`, secrets go in `.env`
- New tools need a `check_fn` so they only appear when requirements are met
