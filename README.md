# Hermes Config — May 3 2026 Session

## What This Is
This branch contains the dotfiles and scripts from the May 3 2026 session where we fixed the cron scheduler, added loop guard protection, and wired DeepSeek API for the cortex flywheel.

## Files

### `scripts/hermes_loop_guard.py`
Hard loop detection for Hermes Agent. Run before every tool call:
```bash
python3 ~/.hermes/scripts/hermes_loop_guard.py <tool_name> [error_msg]
```
Returns exit code 1 if loop detected (3+ same tool calls or 2+ same errors).

### `scripts/hermes_scheduler_daemon.py`
Cron scheduler daemon. Runs `tick()` every 60s to execute due jobs:
```bash
export DEEPSEEK_API_KEY="your-key"
python3 ~/.hermes/scripts/hermes_scheduler_daemon.py
```

## Setup for New CLI Instance

```bash
# 1. Clone this branch
git clone -b hermes-config https://github.com/dannyJ848/hermes-agent.git /tmp/hermes-config
cp /tmp/hermes-config/scripts/*.py ~/.hermes/scripts/

# 2. Set DeepSeek API key (get from ~/.hermes/.env or add to ~/.zshrc)
export DEEPSEEK_API_KEY="sk-7ab7950..."

# 3. Pull main repo (has cron/jobs.py fix)
cd ~/hermes-agent && git pull origin main

# 4. Start daemons
python3 ~/.hermes/scripts/hermes_scheduler_daemon.py &
cd ~/subconscious && PYTHONDONTWRITEBYTECODE=1 python3 cortex_daemon.py start
```

## What Was Fixed This Session
1. **Cron scheduler bug** (`cron/jobs.py:845`): `KeyError: 'id'` -> `rj.get("id")`
2. **Loop guard**: New script prevents repetitive tool-call loops
3. **Scheduler daemon**: New background process for cron job execution
4. **DeepSeek API**: Found key in `~/.hermes/.env`, verified working
5. **Flywheel stuck cycles**: Killed 19 zombie cycles in database
6. **Database schema**: Verified `cortex_flywheel` has all required columns

## Running Processes
- **Scheduler daemon**: `python3 ~/.hermes/scripts/hermes_scheduler_daemon.py`
- **Cortex daemon**: `cd ~/subconscious && python3 cortex_daemon.py start`
- Both need `DEEPSEEK_API_KEY` environment variable

## Cron Jobs Status
- 42 jobs mass-killed (disabled)
- 15 learning/cortex jobs re-enabled
- Jobs execute every 60s via scheduler daemon
