# Cron Job Mass Management Pattern

## Use Case
User wants to quickly disable ALL cron jobs, then selectively re-enable only specific ones.

## Pattern

### Step 1: Mass Disable (Kill All)
```python
import json

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'r') as f:
    data = json.load(f)

# Backup
with open('/Users/dannygomez/.hermes/cron/jobs.json.backup', 'w') as f:
    json.dump(data, f, indent=2)

# Kill all
for j in data.get('jobs', []):
    j['enabled'] = False
    j['state'] = 'paused'
    j['next_run_at'] = None
    j['paused_at'] = datetime.now().isoformat()
    j['paused_reason'] = 'User mass-kill'

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
    json.dump(data, f, indent=2)
```

### Step 2: Selective Re-enable by Keyword
```python
keywords = ['cortex', 'brain', 'learning', 'iteration']
for j in data.get('jobs', []):
    name = j.get('name', '').lower()
    if any(k in name for k in keywords):
        j['enabled'] = True
        j['state'] = 'scheduled'
        j['next_run_at'] = (datetime.now() + timedelta(minutes=2)).isoformat()
```

### Step 3: Start Scheduler Daemon
```bash
cd ~/hermes-agent && source venv/bin/activate && python3 /tmp/hermes_scheduler_daemon.py
```

## Verification
```bash
ls -lt ~/.hermes/cron/output/ | head -5  # Check for fresh output
```

## Lesson from May 3, 2026
User said "holy shit kill all of them" — 42 jobs mass-disabled in one shot. Then "turn on ONLY the learning loop/cortex/cerebrum/iteration loop related" — 15 selectively re-enabled. This pattern is useful for cron hygiene and emergency stops.
