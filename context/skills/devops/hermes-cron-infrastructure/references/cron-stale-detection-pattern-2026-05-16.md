# Cron Stale Job Detection Pattern

**Date:** 2026-05-16
**Context:** Hermes cron infrastructure audit — all 16 active jobs had last run dates of 2026-04-22, zero executions in May.

## Detection

```bash
# Check if any jobs ran recently (last 7 days)
hermes cron list | grep "Last run" | grep "2026-05" | wc -l
# → 0 means NO jobs ran in May — stale scheduler

# Alternative: check all last run dates
hermes cron list | grep -E "Name:|Last run"
# Look for dates clustered around a single past date (e.g., all 2026-04-22)
```

## Root Causes

1. **Scheduler daemon dead** — `tick()` not being called, no process running
2. **Gateway down** — cron jobs deliver to local session, but no active session
3. **Jobs all paused** — mass disable or corruption set `enabled: false`
4. **Next run times in past** — scheduler was down, jobs accumulated as overdue

## Quick Diagnostic

```bash
# 1. Check scheduler daemon
ps aux | grep -i "hermes.*scheduler\|cortex.*daemon" | grep -v grep

# 2. Check gateway status
hermes status | grep -A 2 "Gateway"

# 3. Check job states directly
python3 -c "
import json
with open('/Users/dannygomez/.hermes/cron/jobs.json') as f:
    data = json.load(f)

from datetime import datetime, timezone
now = datetime.now(timezone.utc)

for j in data.get('jobs', []):
    name = j.get('name', 'unnamed')
    enabled = j.get('enabled', False)
    last_run = j.get('last_run_at', 'never')
    next_run = j.get('next_run_at', 'none')
    print(f'{name}: enabled={enabled}, last_run={last_run}, next_run={next_run}')
"

# 4. Check for overdue jobs (next_run_at in past)
python3 -c "
import json
from datetime import datetime, timezone
with open('/Users/dannygomez/.hermes/cron/jobs.json') as f:
    data = json.load(f)
now = datetime.now(timezone.utc)
overdue = [j for j in data.get('jobs', []) 
           if j.get('enabled') and j.get('next_run_at') 
           and datetime.fromisoformat(j['next_run_at']) < now]
print(f'Overdue jobs: {len(overdue)}')
"
```

## Recovery

### Option A: Manual tick() trigger

```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "from cron.scheduler import tick; tick(verbose=True)"
```

### Option B: Restart scheduler daemon

If using custom daemon:
```bash
# Kill old daemon
pkill -f "hermes_scheduler_daemon"

# Start fresh
cd ~/hermes-agent && source venv/bin/activate && python3 /tmp/hermes_scheduler_daemon.py &
```

### Option C: Fix next_run_at timestamps

When ALL jobs have `next_run_at` in the past (scheduler not advancing):

```python
import json
from datetime import datetime, timezone, timedelta
from croniter import croniter

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'r') as f:
    data = json.load(f)

now = datetime.now(timezone(timedelta(hours=-5)))

for j in data.get('jobs', []):
    if not j.get('enabled'):
        continue
    schedule = j.get('schedule', '')
    if not schedule:
        continue
    try:
        itr = croniter(schedule, now)
        next_run = itr.get_next(datetime)
        j['next_run_at'] = next_run.isoformat()
        j['state'] = 'scheduled'
    except Exception as e:
        print(f"Failed to parse {j.get('name')}: {e}")

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Fixed {len(data.get('jobs', []))} jobs")
```

### Option D: Unified Daemon Replacement

For persistent reliability, replace cron with unified daemon pattern. See `references/unified-daemon-manual-triggers-pattern.md`.

## Prevention

- Monitor `hermes cron list` weekly for stale last_run dates
- Set up health check cron job that alerts if no jobs ran in 24h
- Use unified daemon instead of cron for critical infrastructure
