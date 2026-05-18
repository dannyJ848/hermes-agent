# DGX Hermes Tool Registration and check_fn Filtering (May 14, 2026)

## Discovery

When deploying full Hermes on DGX with plugins enabled, tool count went from 21 → 84 → 87 → 97 as different dependencies were resolved. This document tracks the actual resolution path.

## How Tool Loading Actually Works

1. **Plugin discovery:** `discover_plugins()` scans `plugins/` and `~/.hermes/plugins/` directories
2. **Plugin filtering:** Only plugins in `plugins.enabled` list are loaded (opt-in by default)
3. **Tool registration:** Each plugin registers its tools via `registry.register()`
4. **Toolset resolution:** `get_tool_definitions()` resolves tool names from toolsets
5. **Registry filtering:** `registry.get_definitions()` calls each tool's `check_fn` — only tools whose `check_fn` returns `True` are included

## The Four Barriers to Full Tool Coverage

### Barrier 1: Plugin Config Format (21 → 84 tools)

**Problem:** DGX config had `hermes_cli.plugins.*` list format (v0.12), but v0.13 expects `plugins.enabled`/`plugins.disabled` dict.

**Symptom:**
```
Plugin discovery complete: 49 found, 7 enabled
```

**Fix:** Update `~/.hermes/config.yaml` (NOT repo config) with correct plugin format. See `references/dgx-hermes-full-agent-toolset-config.md` for full plugin list.

### Barrier 2: Web API Credentials (84 → 87 tools)

**Problem:** `web_search`, `web_extract` require Brave/Firecrawl/Tavily API keys.

**Symptom:** Tools missing from tool list even though web toolset is enabled.

**Fix:** Add credentials to `~/.hermes/.env`:
```bash
BRAVE_API_KEY=your-key
FIRECRAWL_API_KEY=your-key
```

### Barrier 3: Node.js for Browser Tools (87 → 97 tools)

**Problem:** Browser tools need `agent-browser` CLI (npm package). DGX is aarch64, Node.js not pre-installed.

**Symptom:**
```python
from tools.browser_tool import check_browser_requirements
check_browser_requirements()  # Returns False
```

**Fix:** Install Node.js binary + agent-browser:
```bash
cd /tmp
curl -fsSL https://nodejs.org/dist/v20.12.2/node-v20.12.2-linux-arm64.tar.xz -o node.tar.xz
tar -xf node.tar.xz
mv node-v20.12.2-linux-arm64 ~/node
export PATH=$HOME/node/bin:$PATH
npm install -g agent-browser
```

**Critical:** Update systemd service PATH to include Node.js:
```ini
Environment=PATH=/home/djg6228/node/bin:/data/SpecForge/hermes-agent/venv/bin:/usr/local/bin:/usr/bin:/bin
```

### Barrier 4: Config File Location

**Problem:** Hermes reads config from `~/.hermes/config.yaml`, not the repo directory.

**Symptom:** Changes to `/data/SpecForge/hermes-agent/config.yaml` have no effect.

**Fix:** Always edit `/home/djg6228/.hermes/config.yaml`.

## Debugging Tool Registration

```python
# Check plugin discovery
from hermes_cli.plugins import discover_plugins
import logging
logging.basicConfig(level=logging.INFO)
discover_plugins()
# Look for: "Plugin discovery complete: 49 found, 7 enabled"
# 7 enabled = only built-ins; 40+ enabled = user plugins loaded

# Check which tools pass check_fn
from model_tools import get_tool_definitions
tools = get_tool_definitions(quiet_mode=True)
print(f'Total tools: {len(tools)}')

# Check browser specifically
from tools.browser_tool import check_browser_requirements
print(f'Browser requirements: {check_browser_requirements()}')

# Check why browser fails
from tools.browser_tool import _find_agent_browser, _get_cloud_provider
try:
    cmd = _find_agent_browser()
    print(f'agent-browser found: {cmd}')
except FileNotFoundError as e:
    print(f'agent-browser NOT found: {e}')

provider = _get_cloud_provider()
print(f'Cloud provider: {provider}')
if provider:
    print(f'Provider configured: {provider.is_configured()}')
```

## Tools by Barrier

| Barrier | Tools Added | Count |
|---------|------------|-------|
| None (default) | clarify, delegate_task, execute_code, memory, patch, process, read_file, search_files, session_search, skill_manage, skill_view, skills_list, terminal, text_to_speech, todo, video_analyze, vision_analyze, write_file, x_search, x_tweet_fetch, x_user_tweets | 21 |
| Plugin config fixed | All Evey plugin tools (autonomy, bridge, cost, council, delegation, digest, email, github, goals, habits, identity, learner, memory-adaptive, memory-consolidate, mesh, news, proactive, rag, reflect, research, sandbox, scheduler, session-guard, status, telegram-ux, telemetry, tool-intelligence, validate, verification, watchdog, learning-brain) | +63 = 84 |
| Web APIs synced | web_search, web_extract, web_research | +3 = 87 |
| Node.js installed | browser_back, browser_click, browser_console, browser_get_images, browser_navigate, browser_press, browser_scroll, browser_snapshot, browser_type, browser_vision | +10 = 97 |

## Tools Still Requiring Setup

| Toolset | Tools | Requirement |
|---------|-------|-------------|
| cronjob | cronjob | Cron daemon configured |
| feishu | feishu_doc_read, feishu_drive_* | Feishu app credentials |
| discord | discord, discord_admin | DISCORD_TOKEN env var |
| homeassistant | ha_* | HA_URL + HA_TOKEN env vars |
| image_gen | image_generate | Image generation API key |
| kanban | kanban_* | Kanban worker configured |
| messaging | send_message | Messaging service configured |
| rl | rl_* | RL environment configured |
| spotify | spotify_* | Spotify credentials |
| yuanbao | yb_* | Yuanbao config |

## Key Insight

check_fn filtering is the SECOND layer of filtering. The FIRST layer is plugin enablement. If plugins aren't enabled, their tools never even reach the registry. Always check plugin discovery BEFORE debugging check_fn:

1. `discover_plugins()` → should show 40+ enabled
2. `get_tool_definitions()` → should show 90+ tools
3. If count is low, check `check_browser_requirements()` and other check_fns
