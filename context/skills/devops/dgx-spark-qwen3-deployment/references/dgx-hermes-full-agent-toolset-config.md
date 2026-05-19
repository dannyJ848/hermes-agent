# DGX Hermes Full Agent — Toolset Configuration

**Date:** May 14, 2026
**Problem:** DGX Hermes only loaded 21 tools vs 90+ on MacBook
**Root causes:** (1) Plugin config format mismatch, (2) Config file location wrong, (3) Missing API credentials, (4) Missing Node.js for browser tools
**Final result:** 97 tools loaded (vs 21 default, vs 103 on MacBook)

## The Four Root Causes

### 1. Plugin Config Format Mismatch

The DGX `config.yaml` had plugins listed as `hermes_cli.plugins.*` entries (v0.12 format), but the plugin loader expects `plugins.enabled`/`plugins.disabled` dicts (v0.13 format).

**Wrong (v0.12, silently ignored):**
```yaml
plugins:
  - hermes_cli.plugins.memory
  - hermes_cli.plugins.skills
  - hermes_cli.plugins.knowledge
```

**Correct (v0.13):**
```yaml
plugins:
  disabled:
    - evey-eyes
    - evey-moltbook
    - evey-mqtt
    - evey-wallet
  enabled:
    - cognitive-systems
    - distillation
    - evey-autonomy
    - evey-bridge
    - evey-cache
    - evey-cost-guard
    - evey-council
    - evey-delegate-model
    - evey-delegation-score
    - evey-digest
    - evey-email-guard
    - evey-github
    - evey-goals
    - evey-habits
    - evey-identity
    - evey-learner
    - evey-memory-adaptive
    - evey-memory-consolidate
    - evey-mesh
    - evey-news
    - evey-proactive
    - evey-rag
    - evey-reflect
    - evey-research
    - evey-sandbox
    - evey-scheduler
    - evey-session-guard
    - evey-status
    - evey-telegram-ux
    - evey-telemetry
    - evey-tool-intelligence
    - evey-validate
    - evey-verification
    - evey-watchdog
    - learning-brain
```

**How to check:**
```bash
venv/bin/python -c "
from hermes_cli.plugins import discover_plugins
import logging
logging.basicConfig(level=logging.INFO)
discover_plugins()
"
# Look for: "Plugin discovery complete: 49 found, 7 enabled"
# 7 enabled means only built-in plugins loaded, not user plugins
```

### 2. Config File Location

Hermes loads config from `~/.hermes/config.yaml`, NOT from the repo directory.

**Repo config (`/data/SpecForge/hermes-agent/config.yaml`):** Used for code, NOT for runtime config
**Runtime config (`/home/djg6228/.hermes/config.yaml`):** Where Hermes actually reads from

**Always update the HOME config:**
```bash
# NOT this:
cd /data/SpecForge/hermes-agent && vim config.yaml

# DO this:
vim /home/djg6228/.hermes/config.yaml
```

**Verify which config is loaded:**
```bash
venv/bin/python -c "
from hermes_cli.config import get_config_path
print(get_config_path())
"
# Should show: /home/djg6228/.hermes/config.yaml
```

### 3. Missing API Credentials in ~/.hermes/.env

The `.env` file must also be at `~/.hermes/.env`, not the repo directory.

**Credentials to sync from MacBook:**
```bash
# On MacBook
cat ~/.hermes/.env | grep -E '^(BRAVE|FIRECRAWL|BROWSERBASE|OPENROUTER)'

# On DGX — create/update ~/.hermes/.env
cat > /home/djg6228/.hermes/.env << 'EOF'
BRAVE_API_KEY=your-key
FIRECRAWL_API_KEY=your-key
BROWSERBASE_API_KEY=your-key
BROWSERBASE_PROJECT_ID=your-project-id
BROWSERBASE_PROXIES=true
OPENROUTER_API_KEY=your-key
EOF
```

### 4. Node.js Required for Browser Tools

Browser tools need the `agent-browser` CLI which is an npm package. DGX Spark is aarch64 and Node.js is not pre-installed.

**Install Node.js on aarch64 DGX:**
```bash
cd /tmp
curl -fsSL https://nodejs.org/dist/v20.12.2/node-v20.12.2-linux-arm64.tar.xz -o node.tar.xz
tar -xf node.tar.xz
mv node-v20.12.2-linux-arm64 ~/node

# Verify
~/node/bin/node --version  # v20.12.2
~/node/bin/npm --version   # 10.5.0

# Install agent-browser
export PATH=$HOME/node/bin:$PATH
npm install -g agent-browser
agent-browser --version  # 0.27.0
```

**Add to PATH permanently:**
```bash
echo 'export PATH=/home/djg6228/node/bin:$PATH' >> ~/.bashrc
```

**Update systemd service to include Node.js:**
```ini
[Service]
Environment=PATH=/home/djg6228/node/bin:/data/SpecForge/hermes-agent/venv/bin:/usr/local/bin:/usr/bin:/bin
```

## Tool Count Progression

| Stage | Tools | What Changed |
|-------|-------|-------------|
| Default | 21 | Minimal safe tools only |
| + Plugins enabled | 84 | Added 63 Evey plugin tools |
| + Web APIs | 87 | Added web_search, web_extract |
| + Browser (Node.js) | 97 | Added 10 browser_* tools |
| MacBook reference | 103 | Has cronjob, Feishu, video_analyze |

## Final 97 Tools on DGX

**Browser (10):** browser_back, browser_click, browser_console, browser_get_images, browser_navigate, browser_press, browser_scroll, browser_snapshot, browser_type, browser_vision

**Delegation (6):** delegate_task, delegate_with_model, delegate_parallel, cached_delegate, council_decide, mixture_of_agents

**Evey Plugins (35):** apply_learnings, autonomous_decide, autonomous_plan, autonomous_reflect, claude_bridge_check, claude_bridge_message, claude_bridge_task, consolidate_daily_memory, cost_analytics, cost_check, cost_set_budget, daily_digest, delegation_log, delegation_stats, email_screen, evey_goals, github_pr_status, github_status, gui_click, gui_type, habits_insights, habits_log, learn_from_interaction, memory_decay, memory_score, mesh_lock, mesh_message, mesh_status, mesh_task, news_scan, proactive_budget, proactive_nudge, reflect_on_output, save_finding, update_identity

**Core (20):** clarify, execute_code, memory, patch, process, read_file, search_files, session_search, skill_manage, skill_view, skills_list, terminal, text_to_speech, todo, video_analyze, vision_analyze, write_file

**Web (3):** web_extract, web_research, web_search

**X/Twitter (3):** x_search, x_tweet_fetch, x_user_tweets

**Verification (4):** verify_dns, verify_endpoint, verify_repo, verify_url

**Other (16):** schedule_add, schedule_list, schedule_remove, screen_capture, secure_read, secure_search, session_checkpoint, session_restore, status_check, telegram_card, telegram_status, telemetry_query, tool_intelligence, validate_output, watchdog_heartbeat, watchdog_status

## Still Missing (6 tools vs MacBook)

| Tool | Why Missing | Fix |
|------|------------|-----|
| cronjob | Cron not configured | Enable cron in config, add cron tasks |
| feishu_doc_read | No Feishu credentials | Add Feishu app_id/app_secret to .env |
| feishu_drive_add_comment | No Feishu credentials | Add Feishu app_id/app_secret to .env |
| feishu_drive_list_comment_replies | No Feishu credentials | Add Feishu app_id/app_secret to .env |
| feishu_drive_list_comments | No Feishu credentials | Add Feishu app_id/app_secret to .env |
| feishu_drive_reply_comment | No Feishu credentials | Add Feishu app_id/app_secret to .env |

## Verification Commands

```bash
# Full tool count
cd /data/SpecForge/hermes-agent
venv/bin/python -c "
from model_tools import get_tool_definitions
tools = get_tool_definitions(quiet_mode=True)
print(f'Total tools: {len(tools)}')
"

# Check specific toolset
venv/bin/python -c "
from model_tools import get_tool_definitions
tools = get_tool_definitions(quiet_mode=True)
browser = [t for t in tools if 'browser' in t.get('function',{}).get('name','')]
print(f'Browser tools: {len(browser)}')
"

# Debug why a tool is missing
venv/bin/python -c "
from tools.browser_tool import check_browser_requirements
print(f'Browser requirements: {check_browser_requirements()}')
"
```

## Key Insight

The difference between 21 tools and 97 tools is NOT just "enabling toolsets" — it's:
1. Correct plugin config format (dict vs list)
2. Config in the RIGHT location (~/.hermes/ not repo/)
3. API credentials synced to ~/.hermes/.env
4. Node.js installed for browser automation
5. PATH updated to include Node.js binary

Each of these is independently necessary. Missing any one drops you back to partial tool coverage.
