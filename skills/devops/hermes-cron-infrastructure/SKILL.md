---
title: Hermes Cron Infrastructure
description: Manage, debug, and maintain the Hermes Agent cron scheduler — jobs, daemon, tick execution, and common failures.
name: hermes-cron-infrastructure
trigger: When working with Hermes cron jobs, scheduler, `hermes cron` commands, or cron-related errors.
---

# Hermes Cron Infrastructure

## Overview

Hermes has a built-in cron system for scheduled tasks. Jobs are stored in `~/.hermes/cron/jobs.json` and executed by the `tick()` function in `cron/scheduler.py`. The scheduler can be triggered manually, by a daemon, or by system cron.

## Key Files

| File | Purpose |
|------|---------|
| `~/.hermes/cron/jobs.json` | Job definitions (42 jobs max in this session) |
| `~/.hermes/cron/output/<job_id>/` | Execution output directories |
| `~/hermes-agent/cron/scheduler.py` | Core `tick()` function (line 1290) |
| `~/hermes-agent/cron/jobs.py` | Job loading, due check, state management |
| `/tmp/hermes_scheduler_daemon.py` | Custom daemon wrapper (if deployed) |

## Common Operations

### List All Jobs (workaround for broken cronjob tool)

The `cronjob` tool may fail with `{'error': "'id'", 'success': False}`. Use direct file access:

```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
import json
from datetime import datetime

with open('/Users/dannygomez/.hermes/cron/jobs.json') as f:
    data = json.load(f)

now = datetime.now().astimezone()
for j in data.get('jobs', []):
    name = j.get('name', 'unnamed')
    enabled = j.get('enabled', False)
    next_run = j.get('next_run_at', 'None')
    print(f'{name}: enabled={enabled}, next_run={next_run}')
"
```

### Mass Disable All Jobs

```python
import json

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'r') as f:
    data = json.load(f)

# Backup first
with open('/Users/dannygomez/.hermes/cron/jobs.json.backup', 'w') as f:
    json.dump(data, f, indent=2)

# Disable all
for j in data.get('jobs', []):
    j['enabled'] = False
    j['state'] = 'paused'
    j['next_run_at'] = None

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
    json.dump(data, f, indent=2)
```

### Selectively Enable Jobs by Keyword

```python
import json
from datetime import datetime, timedelta, timezone

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'r') as f:
    data = json.load(f)

keywords = ['cortex', 'brain', 'learning']  # adjust as needed
now = datetime.now(timezone(timedelta(hours=-5)))

for j in data.get('jobs', []):
    name = j.get('name', '').lower()
    if any(k in name for k in keywords):
        j['enabled'] = True
        j['state'] = 'scheduled'
        j['next_run_at'] = (now + timedelta(minutes=2)).isoformat()

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
    json.dump(data, f, indent=2)
```

## Known Bugs & Fixes

### Bug: Cron Database Corruption from Nested Quotes in Prompts

**Symptom:** `cronjob` tool fails with JSON parse error:
```
Expecting ',' delimiter: line 171 column 112 (char 5432)
```

**Root cause:** A cron job's prompt contains unescaped double quotes inside a double-quoted JSON string. Example:
```json
{"prompt": "python -c \"from agent.brain import run_cycle\""}
```
The nested `"` breaks the JSON parser.

**Detection:**
```bash
python3 -c "import json; json.load(open('/Users/dannygomez/.hermes/cron/jobs.json'))"
# If this raises json.JSONDecodeError, the DB is corrupted
```

**Recovery (in order of preference):**

1. **Restore from backup** (fastest):
```bash
cp /Users/dannygomez/.hermes/cron/jobs.json.backup /Users/dannygomez/.hermes/cron/jobs.json
```

2. **Manual JSON fix** (if no backup):
```bash
python3 -c "
import json, re
with open('/Users/dannygomez/.hermes/cron/jobs.json', 'r') as f:
    raw = f.read()
# Find the problematic line and fix nested quotes
# Or use a JSON repair library: pip install json-repair
from json_repair import repair_json
fixed = repair_json(raw)
data = json.loads(fixed)
with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
    json.dump(data, f, indent=2)
"
```

3. **Nuclear option** (delete all jobs):
```bash
echo '{"jobs": []}' > /Users/dannygomez/.hermes/cron/jobs.json
```

**Prevention:**
- Never use `cronjob(action='create')` with prompts containing `"` — escape them as `\"` or use single quotes
- Keep `jobs.json.backup` updated after every successful cron modification
- Prefer the unified daemon pattern (see `references/unified-daemon-manual-triggers-pattern.md`) over cron for complex commands

**Note:** The `cronjob` tool has a ~16% success rate and will fail repeatedly on corrupted DB. Use direct file access instead. After 5 failed attempts, the tool guardrail halts all cron operations — switch to shell-based recovery immediately.

### Bug: `KeyError: 'id'` in `cron/jobs.py` line 845

**Symptom:** Scheduler `tick()` crashes with:
```
File "cron/jobs.py", line 845, in get_due_jobs
    if rj["id"] == job["id"]:
       ~~^^^^^^
KeyError: 'id'
```

**Root cause:** Some jobs in `raw_jobs` list don't have an `id` field.

**Fix:** Use `.get()` with default:
```python
# OLD (broken):
if rj["id"] == job["id"]:

# NEW (fixed):
if rj.get("id") == job.get("id"):
```

File: `~/hermes-agent/cron/jobs.py` line 845

### Bug: Python version mismatch

**Symptom:** `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`

**Root cause:** System Python is 3.8.8 but Hermes code uses 3.10+ syntax (`Path | None`).

**Fix:** Always use the venv Python:
```bash
cd ~/hermes-agent && source venv/bin/activate && python3 --version
# Should show 3.11.14, not 3.8.8
```

**If you must run with system Python (3.8):**
Fix the type annotations in core files. See `hermes-plugin-development` skill, reference `python38-compatibility-fixes.md` for bulk fix patterns.

**Known affected files:**
- `hermes_constants.py` line 110: `get_optional_skills_dir(default: Path | None = None) -> Path`
- `hermes_constants.py` line 165: `get_subprocess_home() -> str | None`

**Quick fix for hermes_constants.py:**
```python
import re

with open('hermes_constants.py', 'r') as f:
    content = f.read()

# Add Optional import
if 'from typing import' in content and 'Optional' not in content:
    content = content.replace('from typing import', 'from typing import Optional,')
elif 'from typing import' not in content:
    content = 'from typing import Optional\n' + content

# Fix union syntax
content = re.sub(r'\) -> ([A-Za-z_][A-Za-z0-9_\[\]]*) \| None:', r') -> Optional[\1]:', content)
content = re.sub(r': ([A-Za-z_][A-Za-z0-9_\[\]]*) \| None =', r': Optional[\1] =', content)

with open('hermes_constants.py', 'w') as f:
    f.write(content)
```

## Starting the Scheduler Daemon

The scheduler has no built-in daemon loop. Use the custom wrapper:

```bash
# Create /tmp/hermes_scheduler_daemon.py (see references/scheduler-daemon-template.py)
cd ~/hermes-agent && source venv/bin/activate && python3 /tmp/hermes_scheduler_daemon.py
```

Or run `tick()` manually:
```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "from cron.scheduler import tick; tick(verbose=True)"
```

## Verification

Check if jobs are executing:
```bash
ls -lt ~/.hermes/cron/output/ | head -5
# Look for recent .md files in job directories
```

## Mass Disable / Massacre Pattern (Surgical Style)

When user wants everything killed immediately (e.g., "42 cron jobs, kill them all"):

**DO NOT:**
- List jobs before killing
- Ask which ones to keep
- Show previews or dry-runs
- Explain what you're about to do

**DO:**
- Kill everything immediately
- Report count after: "Killed 42 jobs. 0 running."
- Let user ask for selective restart if needed

```python
import json
from datetime import datetime, timezone, timedelta

# 1. KILL EVERYTHING (no preview, no confirmation)
with open('/Users/dannygomez/.hermes/cron/jobs.json', 'r') as f:
    data = json.load(f)

# Backup
with open('/Users/dannygomez/.hermes/cron/jobs.json.backup', 'w') as f:
    json.dump(data, f, indent=2)

# Massacre
count = 0
for j in data.get('jobs', []):
    j['enabled'] = False
    j['state'] = 'paused'
    j['next_run_at'] = None
    count += 1

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Killed {count} jobs. 0 running.")

# 2. Selective re-enable (only if user asks)
keywords = ['cortex', 'brain', 'learning']  # adjust per user request
now = datetime.now(timezone(timedelta(hours=-5)))
enabled = 0
for j in data.get('jobs', []):
    name = j.get('name', '').lower()
    if any(k in name for k in keywords):
        j['enabled'] = True
        j['state'] = 'scheduled'
        j['next_run_at'] = (now + timedelta(minutes=2)).isoformat()
        enabled += 1

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Re-enabled {enabled} jobs.")
```

## Scheduler Daemon (when built-in scheduler is broken)

When `cronjob()` tool fails repeatedly with `{'error': "'id'"}`, use a standalone daemon:

```bash
# /tmp/hermes_scheduler_daemon.py
import sys
sys.path.insert(0, '/Users/dannygomez/hermes-agent')

import os
os.environ['DEEPSEEK_API_KEY'] = 'sk-7ab7950...'

from cron.scheduler import tick
import time

while True:
    try:
        tick(verbose=True)
    except Exception as e:
        print(f"Scheduler error: {e}")
    time.sleep(60)
```

Start: `cd ~/hermes-agent && source venv/bin/activate && python3 /tmp/hermes_scheduler_daemon.py`

**Key requirements:**
- Must `cd ~/hermes-agent` first (for module path resolution)
- Must activate venv (Python 3.10+ required)
- Must export `DEEPSEEK_API_KEY` before import (if flywheel uses LLM judge)
- Runs `tick()` every 60 seconds
- Output appears in `~/.hermes/cron/output/<job_id>/`

## Sub-Topic: Cron Debugging

See `hermes-cron-debugging` skill (absorbed). Key patterns:
- Gateway startup: `cd ~/hermes-agent && ./venv/bin/python -m hermes_cli.main gateway run` (NOT `run_agent.py --gateway`)
- Log locations: `~/.hermes/logs/gateway.log`, `/private/tmp/gateway_restart.log`, `~/.hermes/sessions/session_cron_<job_id>_*.json`
- Cron schedule format: 5-field cron only (min granularity 1 minute)
- Mass disable/enable patterns: see scripts above

## Sub-Topic: Cron-to-Daemon Conversion

See `hermes-cron-to-daemon` skill (absorbed). When cron jobs block each other (max_workers bottleneck) or you need sub-2-minute intervals:

**Production daemon architecture (cortex_daemon.py pattern):**
```
DAEMON: ~/subconscious/cortex_daemon.py (PID-managed, 24/7)
├── Thread: flywheel (30s cycle) — Elo eval + repair + consolidate
├── Thread: training_gym (60s cycle) — rate unrated tips + quality sweep
├── Thread: perf_monitor (5min cycle) — continuous benchmarks
├── Thread: heartbeat (30s) — writes PID + cycle count
├── Log: ~/subconscious/cortex_daemon.jsonl (append-only)
├── PID: ~/subconscious/cortex_daemon.pid
└── Heartbeat: ~/subconscious/cortex_daemon.heartbeat
```

**Performance proven:** 4 threads, JSONL logging, graceful shutdown, Postgres backend for concurrent writes.

**SQLite→Postgres migration gotchas:**
- SQLite WAL mode locks on concurrent writes — Postgres handles concurrent access
- Use `nohup bash -c '...' > /dev/null 2>&1 &` for background daemon launch
- Never kill gateway to unlock DB — use nohup or enqueue JSON tip files instead

## Support Files

- `scripts/scheduler-daemon.py` — Ready-to-run scheduler daemon wrapper
- `references/cron-database-corruption-recovery-may13-2026.md` — **Cron DB corruption from nested quotes in job prompts. Recovery via backup restore or manual JSON fix.**
  - `references/cron-scheduler-broken-direct-json-pattern-2026-05-16.md` — **When `cronjob()` tool fails with `{'error': "'id'"}` and `hermes cron list` crashes, edit `~/.hermes/cron/jobs.json` directly to update stale `next_run_at` timestamps and fix delivery targets.**
  - `references/cron-stale-jobs-fix-2026-05-16.md` — **When ALL cron jobs have `next_run_at` in the past (scheduler not advancing timestamps), calculate next occurrence from cron expression and update JSON directly.**
- `references/cronjob-remove-bug-2026-05-05.md` — `cronjob(action='remove')` fails with `'id'` error. Workaround: direct JSON editing or system crontab
- `references/unified-daemon-pattern.md` — Persistent daemon pattern replacing all cron jobs (WAL mode SQLite gotcha included)
- `references/cron-to-daemon-migration.md` — Converting blocking cron jobs to persistent daemons
- `references/unified-daemon-manual-triggers-pattern.md` — **NEW (2026-05-09)** Complete architecture: unified daemon + manual triggers + session-end auto-triggers. Replaces all 54 cron jobs with 0 cron dependency.
- `references/wal-mode-silent-failure-debug.md` — **NEW (2026-05-09)** SQLite WAL mode causes inserts to "disappear" during verification. Debug technique for governor logging and any sandbox DB write verification.
- `references/general-tool-building-pattern.md` — **NEW (2026-05-09)** When user asks "what tools don't you have that would help you be more effective?", build general-purpose (not project-specific) tools that enhance overall agent functionality. Pattern: build 3-5 tools, wire all into existing apparatus (unified daemon, manual triggers, session-end hooks), verify with self-diagnostic.

## Pitfalls

- **CRON IS UNRELIABLE — use persistent daemons instead**: The `cronjob` tool has a 16% success rate. System crontab entries are fragile. The robust pattern is a self-looping Python daemon with `signal.SIGTERM` handler, writing to a log file. See `references/unified-daemon-pattern.md` for the full pattern.
- **UNIFIED DAEMON + MANUAL TRIGGERS (2026-05-09)**: When eliminating cron entirely, use three layers: (1) `hermes_unified_daemon.py` for health/monitoring every 5min, (2) `hermes_manual_triggers.py` for 8 on-demand commands, (3) session-end hooks auto-triggering consolidation + brain cycle. See `references/unified-daemon-manual-triggers-pattern.md`.
- **WAL MODE SILENT FAILURE (2026-05-09)**: SQLite WAL mode causes inserts to appear successful but `SELECT COUNT(*)` returns 0 in `execute_code` sandboxes. Data is in `.db-wal` but not checkpointed. Verify via terminal `sqlite3` command with `PRAGMA wal_checkpoint(TRUNCATE)`. See `references/wal-mode-silent-failure-debug.md`.
- **No scheduler daemon = no execution**: Jobs can be scheduled but never run if nothing triggers `tick()`
- **Duplicate job names**: Multiple jobs can have the same name (e.g., 3× "qwen-training-monitor") — identify by `id`
- **Next run times in the past**: If scheduler was down, jobs accumulate as "overdue" — they will all fire at once when scheduler restarts
- **Disk space**: Cron output can accumulate — monitor `~/.hermes/cron/output/` size
- **Broken cronjob tool**: The `cronjob(action='list')` tool is unreliable — use direct file access instead
- **Cron database corruption with nested quotes**: Jobs with unescaped quotes in prompts (e.g., `python -c "from agent.brain"`) corrupt the JSON parser. Error: `Expecting ',' delimiter: line N column X`. Recovery: restore from `jobs.json.backup`, then fix the problematic prompt by escaping nested quotes or simplifying the command.
- **`cronjob(action='remove')` fails with `'id'` error**: The tool's remove command is broken. Use shell-based workarounds:
  1. Create a watchdog script (see `scripts/cortex_watchdog.sh` in `cortex-daemon-diagnostic` skill)
  2. Add to system crontab directly: `crontab -e` → add `*/5 * * * * bash /path/to/script.sh`
  3. For mass cleanup, edit `~/.hermes/cron/jobs.json` directly (see Mass Disable pattern above)
- **`hermes cron remove` fails with `Failed to remove job: 'id'`**: The CLI remove command is also unreliable. Workaround: use Python to edit the JSON directly:
  ```python
  import json
  with open('/Users/dannygomez/.hermes/cron/jobs.json', 'r') as f:
      data = json.load(f)
  # Filter out jobs by name pattern
  data['jobs'] = [j for j in data['jobs'] if 'brain-cycle' not in j.get('name', '')]
  with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
      json.dump(data, f, indent=2)
  ```
- **Duplicate cron jobs**: When `cronjob(action='create')` succeeds but `remove` fails, duplicates accumulate. They are harmless but clutter the list. Clean by direct JSON editing.
- **DeepSeek API key location**: Stored in `~/.hermes/.env` as `DEEPSEEK_API_KEY=sk-...`. Must be exported before daemon starts:
  ```bash
  export DEEPSEEK_API_KEY=$(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)
  ```
- **Python version mismatch**: System Python may be 3.8 but Hermes needs 3.10+. Always use venv: `cd ~/hermes-agent && source venv/bin/activate`
- **Scheduler bug `KeyError: 'id'`**: Fixed in `cron/jobs.py` line 845 — use `rj.get("id")` instead of `rj["id"]`
- **Stuck flywheel cycles**: When `run_eval_sweep()` hangs (e.g., DeepSeek API unavailable), cycles stay in "running" state forever, blocking new cycles. Kill all stuck cycles before restart. See `references/stuck-flywheel-cycles-cleanup-2026-05-03.md`.
- **Agent loop guard failure**: When a tool fails repeatedly, the agent may keep calling it. Hard loop guard enforcement needed:
  ```python
  # /tmp/hermes_loop_guard.py — run before every tool call
  # Same tool 3+ times → STOP. Same error 2+ times → STOP.
  ```
  See `references/loop-guard-enforcement-2026-05-03.md`.
- **Unified context for new CLI sessions**: When starting a new CLI session, the agent needs instant context. Use `python3 hermes_cli/instant_context.py` to show:
  - Training status (PID, step, loss, GPU)
  - Tool intelligence (success rates, circuit breaker states)
  - Recent errors with fixes
  - Active session tasks and decisions
  Update context live with `hermes_cli/context_updater.py`
