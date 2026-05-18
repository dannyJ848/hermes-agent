# Cron JSON Direct Repair — When `cronjob()` and `hermes cron` Are Broken

## Date: 2026-05-16

## Problem

The Hermes cron scheduler's API (`cronjob()` tool) and CLI (`hermes cron list`) both crash:
- `cronjob(action='list')` → `KeyError: 'id'`
- `hermes cron list` → `AttributeError` at end of output

All 44 cron jobs have `next_run_at` dates in the past (May 3-4, 2026) and are not advancing. The scheduler daemon is not running or the tick mechanism is broken.

## Root Cause

Jobs are stored in `~/.hermes/cron/jobs.json` as a flat JSON array. The scheduler reads this file but fails to advance timestamps when the daemon isn't running. The `cronjob()` tool expects a different schema (with `id` field at top level) than what's actually stored.

## Direct Repair Protocol

When cron tooling is broken, edit `~/.hermes/cron/jobs.json` directly:

### 1. Read Current State

```bash
cat ~/.hermes/cron/jobs.json | python3 -m json.tool | grep -E '"id"|"name"|"next_run_at"|"last_run_at"|"schedule"'
```

### 2. Parse and Update with Python

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
    next_run = datetime.fromisoformat(job.get("next_run_at", "2000-01-01"))
    
    if next_run < now:
        # Calculate next occurrence based on cron expression
        # Simple cases:
        if expr == "0 7 * * *":  # Daily 7am
            next_run = now.replace(hour=7, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif expr == "*/5 * * * *":  # Every 5 min
            next_run = now.replace(second=0, microsecond=0)
            while next_run <= now:
                next_run += timedelta(minutes=5)
        # ... etc for other patterns
        
        job["next_run_at"] = next_run.isoformat()

# Fix telegram delivery failures
for job in data.get("jobs", []):
    if job.get("deliver") == "telegram" and "brain" in job.get("name", ""):
        job["deliver"] = "local"

with open(jobs_file, 'w') as f:
    json.dump(data, f, indent=2, default=str)
```

### 3. Common Cron Expressions

| Expression | Meaning | Next Calculation |
|-----------|---------|-----------------|
| `0 7 * * *` | Daily 7am | `now.replace(hour=7)` +1 day if past |
| `0 3 * * *` | Daily 3am | `now.replace(hour=3)` +1 day if past |
| `0 9,15,21 * * *` | 9am, 3pm, 9pm | Find next time in list |
| `0 * * * *` | Hourly | `now.replace(minute=0)` +1 hour |
| `*/5 * * * *` | Every 5 min | Round up to next 5-min boundary |
| `*/3 * * * *` | Every 3 min | Round up to next 3-min boundary |
| `*/15 * * * *` | Every 15 min | Round up to next 15-min boundary |
| `1-59/2 * * * *` | Every 2 min | Round up to next even minute |

### 4. Verify

```bash
# Check next_run dates are now in the future
python3 -c "
import json
with open('$HOME/.hermes/cron/jobs.json') as f:
    data = json.load(f)
from datetime import datetime
now = datetime.now()
for job in data['jobs']:
    n = datetime.fromisoformat(job['next_run_at'])
    print(f\"{job['name'][:40]:40s} {n.strftime('%Y-%m-%d %H:%M')}\")
"
```

### 5. Restart Scheduler (if daemon exists)

```bash
# Check if there's a daemon process
ps aux | grep -i cron | grep -i hermes

# If found, kill and restart
kill -9 <pid>
hermes cron start  # or equivalent
```

If no daemon process exists, the scheduler may be event-driven (triggered by hermes CLI startup). The JSON fix alone may be sufficient.

## Why This Works

The cron system is split into two parts:
1. **Storage**: `~/.hermes/cron/jobs.json` — simple JSON, human-readable
2. **Execution**: Daemon or event loop that reads jobs.json and fires at `next_run_at`

When the execution layer breaks, the storage layer is still editable. By fixing `next_run_at` directly, we restore the contract that the execution layer expects.

## Pitfalls

- **Don't use `cronjob()` tool when it's broken** — it'll fail with `KeyError: 'id'`
- **Don't trust `hermes cron list` output** — it crashes after printing, may show stale data
- **Don't forget timezone** — `next_run_at` includes TZ offset (`-05:00`), use `datetime.now(timezone(...))`
- **Don't set next_run in the past** — the scheduler will just skip it again
- **Don't modify `jobs.json` while daemon is running** — risk of corruption; stop daemon first

## Integration with Working State Preservation

When capturing working state, include `jobs.json` in the snapshot:

```bash
cp ~/.hermes/cron/jobs.json $SNAP_DIR/cron-jobs.json
```

When restoring, diff against current jobs to avoid losing newly-created jobs.
