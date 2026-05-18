# Cron Scheduler Broken — Direct JSON Editing Pattern

## Date: 2026-05-16

## Problem

The Hermes cron system has multiple failure modes that make the standard tools unusable:

1. `cronjob(action='list')` → `{"error": "'id'", "success": False}`
2. `hermes cron list` → crashes with `AttributeError` at end of output
3. `cronjob(action='remove')` → `{"error": "'id'"}`
4. Scheduler daemon not advancing `next_run_at` timestamps — all 44 jobs had dates in the past (May 3-4, 2026) while current date was May 16

## Root Cause

The scheduler's `tick()` function or the daemon that calls it is not running. Jobs are stored in `~/.hermes/cron/jobs.json` as a JSON array under the `"jobs"` key. Each job has:
- `id`: unique hex string
- `name`: human-readable
- `schedule`: `{kind: "cron", expr: "0 7 * * *"}`
- `next_run_at`: ISO timestamp with timezone
- `last_run_at`: ISO timestamp
- `enabled`: boolean
- `state`: "scheduled" | "paused"
- `deliver`: "local" | "telegram" | etc.

When the scheduler doesn't run, `next_run_at` never advances past the last execution.

## Solution: Direct JSON Editing

When standard tools fail, edit `jobs.json` directly:

### 1. Read Current State

```bash
cat ~/.hermes/cron/jobs.json | python3 -m json.tool | grep -E '"id"|"name"|"next_run_at"|"last_run_at"|"state"|"enabled"'
```

### 2. Update All next_run Timestamps

```python
import json, os
from datetime import datetime, timedelta, timezone

home = os.path.expanduser("~")
jobs_file = os.path.join(home, ".hermes", "cron", "jobs.json")

with open(jobs_file) as f:
    data = json.load(f)

now = datetime.now(timezone(timedelta(hours=-5)))  # adjust for your TZ

for job in data.get("jobs", []):
    expr = job.get("schedule", {}).get("expr", "")
    next_run = now + timedelta(hours=1)  # default fallback
    
    # Parse common cron patterns
    if expr == "0 7 * * *":  # Daily at 7am
        next_run = now.replace(hour=7, minute=0, second=0, microsecond=0)
        if next_run < now:
            next_run += timedelta(days=1)
    elif expr == "0 9,15,21 * * *":  # 9am, 3pm, 9pm
        times = [9, 15, 21]
        for h in sorted(times):
            candidate = now.replace(hour=h, minute=0, second=0, microsecond=0)
            if candidate > now:
                next_run = candidate
                break
        else:
            next_run = now.replace(hour=9, minute=0) + timedelta(days=1)
    elif expr == "*/5 * * * *":  # Every 5 min
        next_run = now.replace(second=0, microsecond=0)
        while next_run <= now:
            next_run += timedelta(minutes=5)
    # ... add more patterns as needed
    
    job["next_run_at"] = next_run.isoformat()
    job["state"] = "scheduled"
    job["enabled"] = True

with open(jobs_file, 'w') as f:
    json.dump(data, f, indent=2, default=str)
```

### 3. Fix Delivery Targets

Some jobs may target `telegram` when Telegram is not configured. Change to `local`:

```python
for job in data.get("jobs", []):
    if job.get("deliver") == "telegram":
        job["deliver"] = "local"
```

### 4. Verify

```bash
python3 -c "import json; data=json.load(open('/Users/dannygomez/.hermes/cron/jobs.json')); print(f'Jobs: {len(data[\"jobs\"])}'); print('Next runs:', [j['next_run_at'] for j in data['jobs'][:3]])"
```

## Prevention

- Monitor `next_run_at` dates weekly — they should always be in the future
- If scheduler daemon is custom (e.g., `/tmp/hermes_scheduler_daemon.py`), ensure it's running via `ps aux | grep hermes_scheduler`
- Consider migrating to the unified daemon pattern (see `references/unified-daemon-manual-triggers-pattern.md`) to eliminate cron dependency entirely

## Files

- `~/.hermes/cron/jobs.json` — job definitions
- `~/.hermes/cron/jobs.json.backup` — auto-created backup
- `~/.hermes/cron/output/<job_id>/` — execution output directories
