# Unified Daemon + Manual Triggers Pattern

## When to Use

When user says "cron is unreliable" or "systemic shift away from cron" — replace all cron jobs with:
1. One persistent unified daemon (health + monitoring)
2. Manual trigger scripts (on-demand execution)
3. Session-end auto-triggers (consolidation, brain cycle)

## Architecture

```
┌─────────────────────────────────────────┐
│  hermes_unified_daemon.py               │
│  (PID 18681, 5min loop, SIGTERM handler)│
│  ├── Health checks (tips, tools, DB)    │
│  ├── Qwen training monitor              │
│  ├── Cortex daemon watchdog             │
│  └── Brain cycle processing             │
└─────────────────────────────────────────┘
                   │
┌─────────────────────────────────────────┐
│  hermes_manual_triggers.py              │
│  (on-demand, CLI invocation)            │
│  ├── training-status                    │
│  ├── research-scan                      │
│  ├── cortex-consolidate                 │
│  ├── brain-cycle                        │
│  ├── daily-backup                       │
│  ├── quality-sweep                      │
│  ├── llm-calibrate                      │
│  └── full-report                        │
└─────────────────────────────────────────┘
                   │
┌─────────────────────────────────────────┐
│  Session-end hook (distillation plugin) │
│  ├── Auto-triggers cortex-consolidate   │
│  └── Auto-triggers brain-cycle          │
└─────────────────────────────────────────┘
```

## Implementation

### Step 1: Pause All Cron Jobs

```python
import json

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'r') as f:
    d = json.load(f)

for j in d['jobs']:
    j['enabled'] = False
    j['state'] = 'paused'
    j['paused_at'] = '2026-05-09T16:35:00-05:00'
    j['paused_reason'] = 'Systemic shift away from cron'

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
    json.dump(d, f, indent=2)
```

Also clear system crontab: `crontab -r`

### Step 2: Create Unified Daemon

Key features:
- `signal.SIGTERM` + `signal.SIGINT` handlers for graceful shutdown
- Sleep in 5-second increments (responsive to shutdown)
- Log to file with timestamps
- No cron dependencies

```python
#!/usr/bin/env python3
import os, time, signal, sqlite3, subprocess

LOG_FILE = "/tmp/hermes_unified.log"
INTERVAL = 300  # 5 minutes
_running = True

def _handle_sigterm(signum, frame):
    global _running
    _running = False

def _log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def main():
    _log("[DAEMON] Started")
    while _running:
        # ... checks ...
        slept = 0
        while slept < INTERVAL and _running:
            time.sleep(5)
            slept += 5
```

### Step 3: Create Manual Triggers

```python
#!/usr/bin/env python3
import sys, subprocess

TRIGGERS = {
    'training-status': trigger_training_status,
    'brain-cycle': trigger_brain_cycle,
    # ... etc
}

def trigger_training_status():
    # Check training data dirs, report status
    pass

def main():
    trigger = sys.argv[1]
    TRIGGERS[trigger]()

if __name__ == "__main__":
    main()
```

### Step 4: Session-End Auto-Triggers

In `cognitive_infrastructure_hooks.py`, `on_session_end()`:

```python
def on_session_end(session_id, tool_calls):
    # Extract lessons
    lessons = se.extract(tool_calls)
    
    # Auto-trigger consolidation
    subprocess.run([
        'python3', '/Users/dannygomez/subconscious/hermes_manual_triggers.py',
        'cortex-consolidate'
    ], capture_output=True, timeout=30)
    
    # Auto-trigger brain cycle
    subprocess.run([
        'python3', '/Users/dannygomez/subconscious/hermes_manual_triggers.py',
        'brain-cycle'
    ], capture_output=True, timeout=30)
```

### Step 5: Start Daemon

```bash
# Kill old daemon if running
pkill -f hermes_unified_daemon.py

# Start new daemon
terminal(background=True):
    cd ~/subconscious && python3 hermes_unified_daemon.py
```

## Verification

Check daemon is running:
```bash
pgrep -f hermes_unified_daemon.py
# Should return PID
tail -20 /tmp/hermes_unified.log
```

## Pitfalls

- **WAL mode SQLite**: When verifying inserts from daemon, data may appear in WAL but not main DB. Use `PRAGMA wal_checkpoint(TRUNCATE)` before querying, or query via terminal (which handles WAL correctly).
- **Plugin path**: Hermes CLI may not be in PATH for daemon. Use full path: `/Users/dannygomez/.local/bin/hermes`
- **Process restart**: Daemon must be manually restarted after code changes. Consider adding a `SIGHUP` handler for config reload.
- **Log rotation**: `/tmp/hermes_unified.log` grows unbounded. Add log rotation or use `logrotate`.
