# Unified Daemon Pattern — Replacing Cron Jobs

## Context

The `cronjob` tool has a 16% success rate (43 calls, 7 successes). System crontab is fragile. The robust pattern is a single persistent Python daemon that replaces all cron jobs.

## Architecture

```
hermes_unified_daemon.py (PID-managed, 24/7)
├── Health checks (tip health, tool health, DB size, plugins)
├── Qwen training monitor (check DGX status)
├── Cortex daemon watchdog (pgrep check)
├── Brain cycle (lightweight cognitive processing)
└── Log: /tmp/hermes_unified.log (append-only)
```

## Key Code Pattern

```python
import signal
import time

_running = True
INTERVAL = 300  # 5 minutes

def _handle_sigterm(signum, frame):
    global _running
    _running = False

signal.signal(signal.SIGTERM, _handle_sigterm)
signal.signal(signal.SIGINT, _handle_sigterm)

def main():
    while _running:
        run_cycle()
        # Sleep in small increments for graceful shutdown
        slept = 0
        while slept < INTERVAL and _running:
            time.sleep(5)
            slept += 5
```

## Migration Steps

1. **Pause all cron jobs**:
   ```python
   import json
   with open('/Users/dannygomez/.hermes/cron/jobs.json', 'r') as f:
       data = json.load(f)
   for j in data['jobs']:
       j['enabled'] = False
       j['state'] = 'paused'
   with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
       json.dump(data, f, indent=2)
   ```

2. **Clear system crontab**:
   ```bash
   crontab -r
   ```

3. **Start unified daemon**:
   ```bash
   cd ~/subconscious && python3 hermes_unified_daemon.py
   # Or with nohup for true background:
   nohup python3 ~/subconscious/hermes_unified_daemon.py > /dev/null 2>&1 &
   ```

## Verification

```bash
tail -f /tmp/hermes_unified.log
```

## WAL Mode SQLite Gotcha

When debugging SQLite inserts that "succeed" but don't appear:
- The DB may be in WAL mode (`PRAGMA journal_mode=WAL`)
- Inserts go to `.db-wal` file before checkpoint
- Check with: `sqlite3 dbfile "PRAGMA wal_checkpoint(TRUNCATE); SELECT COUNT(*) FROM table;"`
- Or query from the same connection that did the insert
