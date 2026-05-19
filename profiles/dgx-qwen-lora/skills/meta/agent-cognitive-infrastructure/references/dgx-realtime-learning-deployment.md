# DGX Real-Time Learning Apparatus Deployment

**Date:** May 14, 2026
**Context:** Deploying full Hermes Agent on DGX Spark with Qwen3.6-27B-Uncensored + FrankenV8 LoRA
**User requirement:** "I don't wanna run the qwen model unless its able to iterate every turn"

## What Was Deployed

### 1. Cerebrum Memory DB
- Location: `~/.hermes/cerebrum_memory.db` (on DGX)
- Synced from MacBook: 244 experiences, full schema
- Tables: experiences, distilled_tips, tool_predictions, error_patterns, cognitive_sessions, cognitive_actions, etc.

### 2. Learning Hook (`/data/SpecForge/hermes-agent/agent/dgx_learning_hook.py`)
- Intercepts every tool call via `before_action()` and `after_action()`
- Records: tool_name, args, result, duration, error, timestamp
- Distills tips from successful patterns
- Injects warnings for known error patterns

### 3. Model-Tools Patch (`model_tools.py`)
- Added `before_action()` call before `registry.dispatch()`
- Added `after_action()` call after tool execution
- Wraps all tool calls with learning instrumentation

### 4. Run-Agent Patch (`run_agent.py`)
- Injects current learned tips into system prompt each turn
- Queries cerebrum for relevant tips based on current task
- Adds tips to system message context

### 5. Distillation Daemon (`/data/SpecForge/hermes-agent/scripts/dgx_distillation_daemon.py`)
- Runs as systemd service (`dgx-learning.service`)
- Converts experiences → distilled tips every 5 minutes
- Exports training data hourly to ShareGPT format
- Auto-starts on boot

### 6. Session Exporter (`/data/SpecForge/hermes-agent/scripts/dgx_session_exporter.py`)
- Writes ShareGPT-format `.jsonl` to `/data/SpecForge/custom_dflash/datasets/hermes_sessions/`
- Captures full conversation history for training data pipeline
- Runs hourly via daemon

## Toolset Configuration Fix

**Problem:** DGX Hermes only loaded 21 tools vs 90+ on MacBook
**Root cause:** Missing `enabled_toolsets: all` in config.yaml
**Fix:**
```yaml
agent:
  enabled_toolsets: all
```

**Without fix, only these 21 "safe" tools load:**
- delegate_task, execute_code, memory, patch, process, read_file, search_files, session_search, skill_manage, skill_view, skills_list, terminal, todo, vision_analyze, write_file, x_search, x_tweet_fetch, x_user_tweets

**With fix, 90+ tools including:**
- browser_*, web_search, web_extract, cronjob, kanban_*, send_message, ha_*, image_generate, rl_*, spotify_*, discord_*, feishu_*, yb_*, etc.

## Verification Commands

```bash
# Check tool count
cd /data/SpecForge/hermes-agent
venv/bin/python -c "from model_tools import get_tool_definitions; tools = get_tool_definitions(); print(f'Total tools: {len(tools)}')"

# Check learning daemon status
sudo systemctl status dgx-learning

# Check recent experiences
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM experiences WHERE created_at > datetime('now', '-1 hour');"

# Check distilled tips
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM distilled_tips;"

# Check training data export
ls -la /data/SpecForge/custom_dflash/datasets/hermes_sessions/
```

## Key Files

| File | Purpose |
|------|---------|
| `/data/SpecForge/hermes-agent/agent/dgx_learning_hook.py` | Learning hook implementation |
| `/data/SpecForge/hermes-agent/scripts/dgx_distillation_daemon.py` | Distillation daemon |
| `/data/SpecForge/hermes-agent/scripts/dgx_session_exporter.py` | Session exporter |
| `/etc/systemd/system/dgx-learning.service` | systemd service definition |
| `/data/SpecForge/hermes-agent/config.yaml` | Hermes config (needs enabled_toolsets: all) |

## User Preference Signal

**CRITICAL:** The user will NOT consider a model "ready to run" unless real-time learning is fully deployed. This is a hard prerequisite, not a nice-to-have. The learning apparatus must be:
1. WIRED INTO Hermes source code (not standalone scripts)
2. Running as a daemon (not manual triggers)
3. Producing new experiences every turn
4. Exporting training data for model iteration
