# Cron Stale Jobs Fix — 2026-05-16

Session: Learning apparatus audit found ALL 44 cron jobs had `next_run_at` dates in the past (May 3-4, 2026) while current date was May 16. The scheduler was not advancing timestamps automatically.

## Symptoms

- `cronjob(action='list')` fails with `{'error': "'id'", 'success': False}`
- `hermes cron list` shows jobs but crashes at end with `AttributeError`
- All jobs show `last_run_at` in April 2026 (3+ weeks stale)
- `next_run_at` dates are in the past
- Jobs with `state: scheduled` and `enabled: true` but never executing

## Root Cause

The cron scheduler daemon is either:
1. Not running at all — nothing triggers `tick()` to advance `next_run_at`
2. Running but `tick()` crashes before it can update timestamps
3. Running but a bug prevents timestamp advancement

## Direct JSON Fix

When the cron tool and CLI are both broken, edit `~/.hermes/cron/jobs.json` directly:

```python
import json, os
from datetime import datetime, timedelta, timezone

home = os.path.expanduser("~")
jobs_file = os.path.join(home, ".hermes", "cron", "jobs.json")

with open(jobs_file) as f:
    data = json.load(f)

now = datetime.now(timezone(timedelta(hours=-5)))  # Adjust for your timezone
updated = 0

for job in data.get("jobs", []):
    next_run_str = job.get("next_run_at", "")
    if next_run_str:
        try:
            next_run = datetime.fromisoformat(next_run_str)
        except:
            next_run = now - timedelta(days=30)
    else:
        next_run = now - timedelta(days=30)
    
    if next_run < now:
        expr = job.get("schedule", {}).get("expr", "")
        
        # Calculate next occurrence based on cron expression
        if expr == "0 7 * * *":  # Daily at 7am
            next_run = now.replace(hour=7, minute=0, second=0, microsecond=0)
            if next_run < now:
                next_run += timedelta(days=1)
        elif expr == "0 9,15,21 * * *":  # 9am, 3pm, 9pm
            times = [9, 15, 21]
            next_run = now.replace(minute=0, second=0, microsecond=0)
            found = False
            for h in times:
                candidate = next_run.replace(hour=h)
                if candidate > now:
                    next_run = candidate
                    found = True
                    break
            if not found:
                next_run = next_run.replace(hour=9) + timedelta(days=1)
        elif expr == "0 3 * * *":  # Daily at 3am
            next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
            if next_run < now:
                next_run += timedelta(days=1)
        elif expr == "0 * * * *":  # Hourly
            next_run = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        elif expr == "*/3 * * * *":  # Every 3 minutes
            next_run = now.replace(second=0, microsecond=0)
            while next_run <= now:
                next_run += timedelta(minutes=3)
        elif expr == "*/5 * * * *":  # Every 5 minutes
            next_run = now.replace(second=0, microsecond=0)
            while next_run <= now:
                next_run += timedelta(minutes=5)
        elif expr == "*/15 * * * *":  # Every 15 minutes
            next_run = now.replace(second=0, microsecond=0)
            while next_run <= now:
                next_run += timedelta(minutes=15)
        elif expr == "1-59/2 * * * *":  # Every 2 minutes
            next_run = now.replace(second=0, microsecond=0)
            while next_run <= now:
                next_run += timedelta(minutes=2)
        else:
            # Default: schedule for 1 hour from now
            next_run = now + timedelta(hours=1)
        
        job["next_run_at"] = next_run.isoformat()
        updated += 1

with open(jobs_file, 'w') as f:
    json.dump(data, f, indent=2, default=str)

print(f"Updated {updated} jobs")
```

## Common Cron Expressions Reference

| Expression | Meaning | Next Run Calculation |
|------------|---------|---------------------|
| `0 7 * * *` | Daily at 7:00 AM | `now.replace(hour=7, minute=0)`, +1 day if past |
| `0 3 * * *` | Daily at 3:00 AM | `now.replace(hour=3, minute=0)`, +1 day if past |
| `0 4 * * *` | Daily at 4:00 AM | `now.replace(hour=4, minute=0)`, +1 day if past |
| `0 9,15,21 * * *` | At 9am, 3pm, 9pm | Find next hour in list, +1 day if all past |
| `0 9,21 * * *` | At 9am, 9pm | Find next hour in list, +1 day if all past |
| `0 * * * *` | Every hour | `now.replace(minute=0)` + 1 hour |
| `*/3 * * * *` | Every 3 minutes | Round up to next multiple of 3 |
| `*/5 * * * *` | Every 5 minutes | Round up to next multiple of 5 |
| `*/15 * * * *` | Every 15 minutes | Round up to next multiple of 15 |
| `1-59/2 * * * *` | Every 2 minutes | Round up to next even minute |
| `*/30 * * * *` | Every 30 minutes | Round up to next half hour |

## Telegram Delivery Fix

Some jobs deliver to `telegram` but Telegram is not configured. Change to `local`:

```python
for job in data.get("jobs", []):
    if job.get("deliver") == "telegram":
        job["deliver"] = "local"
        print(f"Changed {job.get('name')} delivery to local")
```

## Verification

After fixing:
```bash
# Check next_run dates are in the future
python3 -c "
import json
with open('/Users/dannygomez/.hermes/cron/jobs.json') as f:
    data = json.load(f)
from datetime import datetime
now = datetime.now().astimezone()
for j in data.get('jobs', [])[:5]:
    nr = j.get('next_run_at', 'None')
    if nr != 'None':
        nr_dt = datetime.fromisoformat(nr)
        status = 'OK' if nr_dt > now else 'STALE'
        print(f'{j[\"name\"][:30]:30s} next_run={nr_dt.strftime(\"%m-%d %H:%M\")} [{status}]')
"
```

## Prevention

- The scheduler daemon must be running for timestamps to auto-advance
- Consider migrating to persistent daemon pattern (see `references/unified-daemon-pattern.md`)
- Monitor `next_run_at` dates during health checks
- Set up alerts when jobs haven't run in >48 hours
