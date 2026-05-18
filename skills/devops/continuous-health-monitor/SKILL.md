---
name: continuous-health-monitor
description: Build continuous health monitoring daemons with cron watchdog and alerting
version: 1.0
created: 2026-04-13
---

# Continuous Health Monitor Daemon

Pattern for building a robust, always-on health monitoring system with automatic recovery.

## Architecture

```
[Daemon (60s cycle)]
    |-- Runs health checks
    |-- Writes state JSON file
    +-- Logs to /tmp/
         |
[ Cron watchdog (30min) ]
    |-- Checks daemon PID alive
    |-- Reads state JSON
    |-- Restarts daemon if dead
    +-- Alerts on crit/warn
```

## Key Components

### 1. Health Check Functions
Each check returns dict with: name, status, message, value, threshold, level
- status: ok / warn / crit
- level: info / warning / critical
- Keep checks atomic (one concern each)
- Time heavy checks (latency, deep metrics) less frequently using cycle counter

### 2. State File (~/.hermes/sentinel_state.json)
JSON with: timestamp, overall status, checks list, pid, cycle number.
Cron reads this. Daemon writes it. Simple coordination.

### 3. Cron Watchdog
Hermes cron job every 30min:
- Read sentinel_state.json
- If daemon PID not running: restart via nohup
- If any check is crit/warn: alert user via Telegram
- If all ok: report "Sentinel: all green" only

### 4. Daemon Launch
```bash
nohup python3 ~/subconscious/cortex_sentinel.py >> /tmp/cortex_sentinel.log 2>&1 &
echo $! > /tmp/cortex_sentinel.pid
```

## Platform-Specific Gotchas

### macOS Memory (CRITICAL)
WRONG: using only free_pages shows ~1% on macOS because macOS caches aggressively.
CORRECT: inactive pages are immediately reclaimable.
```python
available_mem = (free_pages + inactive_pages) * page_size
total_mem = total_pages * page_size
pct_available = available_mem / total_mem * 100
```
macOS memory pressure is fine at 40% used. Only panic below ~5% truly available.

### PostgreSQL Connection
Use psycopg2 directly for raw queries, not high-level wrappers.

### Parameterized SQL (psycopg2)
psycopg2 uses %s placeholders, NOT ? (SQLite).
When adding params to existing query, PREPEND new params:
```python
params = (node_type,) + tuple(existing_params or ())
```

## Recommended Check Catalog

PG connectivity: SELECT 1, timeout 3s
PG latency: timed SELECT 1, threshold 500ms
Dead tuples: pg_stat_user_tables, threshold 50000
Cache hit ratio: heap_blks_hit/(hit+read), threshold 95%
Embedding coverage: nodes with vs without embedding, threshold 90%
Active connections: pg_stat_activity count, threshold 80% of max
Lock waits: pg_locks where not granted, threshold > 0
Disk space: os.statvfs, threshold 10% free
Memory: platform-specific (macOS: free+inactive), threshold 5%
CPU load: os.getloadavg()[0] / cpu_count, threshold 80%
Process alive: os.kill(pid, 0), must exist

## Notification Strategy
ok = silent (cron reports aggregate)
warn = log + next cron cycle alerts
crit = immediate alert (if daemon can reach messaging)
Never spam: aggregate multiple warns into single alert

### CRITICAL: Telegram Alerting from Cron Jobs Does NOT Work
The `TELEGRAM_BOT_TOKEN` is NOT available in cron job environments. It's only loaded
into the running gateway process at startup via `load_hermes_dotenv()`. Even the .env
file may not contain it (it may come from the interactive shell that launched the gateway).
The `proactive_nudge` tool listed in gateway's registry has no corresponding Python
implementation — it's a phantom registration.

**Working fallback for cron alert delivery:**
1. Log alerts to `~/.hermes/logs/sentinel_alerts.log` (always works)
2. Report findings as the cron job's final response (delivered to configured destination)
3. Write a state flag file (e.g., `~/.hermes/sentinel_alert_pending`) that the gateway
   can check on its next cycle and relay to Telegram
4. If gateway is healthy and running, use `send_message(target="telegram")` tool — but
   this only works inside an active agent session, not from raw Python in a cron script

**Do NOT waste time trying to:**
- Import TelegramPlatform directly (class name may not be exported)
- Find the bot token in .env, gateway.json, config.yaml, or plist (it's not there)
- Call the Telegram Bot API with requests (no token available)
- Use `proactive_nudge` as a tool call (it's not a real tool)

## File Layout
Daemon: ~/subconscious/<service>_sentinel.py
Config: ~/.hermes/.hermes_sentinel.yaml (thresholds)
State: ~/.hermes/sentinel_state.json
Log: /tmp/<service>_sentinel.log
PID: /tmp/<service>_sentinel.pid
