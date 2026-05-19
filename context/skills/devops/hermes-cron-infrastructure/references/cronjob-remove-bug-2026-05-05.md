# cronjob Tool Remove Bug — May 5, 2026

## Symptom

`cronjob(action='remove', job_id='...')` returns:
```json
{"error": "'id'", "success": false}
```

The tool fails to remove jobs by ID. All remove syntaxes fail:
- `cronjob(action='remove', job_id='615ecd68d09b')`
- `hermes cron remove 615ecd68d09b`
- `hermes cron rm 615ecd68d09b`
- `hermes cron delete 615ecd68d09b`

## Root Cause

The `cronjob` tool's remove implementation has a bug where it references a key `'id'` that doesn't exist in the job data structure. This is a tool-level bug, not user error.

## Workaround: Shell-Based Cron Management

When the `cronjob` tool fails, use direct shell commands:

### List Jobs (when tool fails)
```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
import json
with open('/Users/dannygomez/.hermes/cron/jobs.json') as f:
    data = json.load(f)
for j in data.get('jobs', []):
    print(f\"{j.get('id', 'NO_ID')}: {j.get('name', 'unnamed')} [{j.get('state', '?')}]\")
"
```

### Remove Duplicate Jobs (direct JSON editing)
```python
import json

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'r') as f:
    data = json.load(f)

# Keep only first occurrence of each name
seen = set()
unique_jobs = []
for j in data.get('jobs', []):
    name = j.get('name', '')
    if name not in seen:
        seen.add(name)
        unique_jobs.append(j)

removed = len(data.get('jobs', [])) - len(unique_jobs)
data['jobs'] = unique_jobs

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Removed {removed} duplicate jobs")
```

### Alternative: System Crontab

For watchdog scripts that need cron scheduling, bypass Hermes cron entirely:

```bash
# Add to system crontab
crontab -l > /tmp/crontab.bak
echo "*/5 * * * * bash /Users/dannygomez/.hermes/cortex_watchdog.sh" >> /tmp/crontab.bak
crontab /tmp/crontab.bak
```

## Prevention

- When creating cron jobs via `cronjob(action='create')`, write down the job_id returned
- If `remove` fails, don't retry — use shell workaround immediately
- Duplicate jobs are harmless but clutter the list. Clean periodically via direct JSON editing
- For critical watchdogs, use system crontab instead of Hermes cron for reliability
