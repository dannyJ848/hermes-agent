---
name: hermes-cron-debugging
description: Debug and fix Hermes Agent cron scheduler failures — jobs not firing, timeouts, concurrency issues, and gateway startup problems.
version: 1.0
---

# Hermes Cron Scheduler Debugging

## When to Use
- Cron jobs not firing (no new session files appearing)
- Cron jobs timing out repeatedly
- Gateway appears alive but cron ticker stopped
- After patching scheduler or config, changes not taking effect

## Critical Facts

### Gateway Startup (DO NOT GET WRONG)
- **CORRECT**: `cd ~/hermes-agent && ./venv/bin/python -m hermes_cli.main gateway run`
- **WRONG**: `./venv/bin/python3 run_agent.py --gateway` — this flag DOES NOT EXIST. It starts CLI test mode with empty model, immediately crashes on the default Python 3.13 prompt.
- The real gateway is always `hermes_cli.main gateway run`

### Log Locations
- Gateway log: `~/.hermes/logs/gateway.log`
- Gateway stderr: `/private/tmp/gateway_restart.log` (find via `lsof -p <PID> | grep REG`)
- Cron session files: `~/.hermes/sessions/session_cron_<job_id>_*.json`
- Cron output: `~/.hermes/cron/output/<job_id>/`
- Cron job definitions: `~/.hermes/cron/jobs.json`

### Cron Schedule Format
- **5-field cron ONLY** (minimum granularity: 1 minute)
- `* * * * *` = every minute (fastest possible)
- `*/2 * * * *` = every 2 minutes
- `*/30 * * * *` = every 30 MINUTES (not seconds!)
- `*/30 * * * * *` (6-field) is **INVALID** — silently fails

## Debugging Workflow

### Step 1: Check if gateway is alive
```bash
ps aux | grep "hermes_cli.main" | grep -v grep
```
If dead, restart with the CORRECT command above.

### Step 2: Check if cron ticker is active
```bash
grep "cron.scheduler" ~/.hermes/logs/gateway.log | tail -10
```
Look for "Running job" entries. If last entry is old, the ticker died (likely from a timeout cascade).

### Step 3: Check for job timeouts
```bash
grep "timed out" ~/.hermes/logs/gateway.log | tail -5
```
Timeouts at 600s indicate the job ran too long. The scheduler blocks on timed-out jobs.

### Step 4: Check job state
**IMPORTANT:** Use `execute_code` with direct Python — do NOT wrap Python in `terminal()` bash commands. Bash quoting of f-strings inside terminal is a recurring failure pattern (syntax errors, escaped quotes breaking).

```python
# In execute_code (NOT terminal):
import json
with open('/Users/dannygomez/.hermes/cron/jobs.json') as f:
    data = json.load(f)
for j in data['jobs']:
    if j['id'] == '<JOB_ID>':
        print('next_run:', j.get('next_run_at'))
        print('last_status:', j.get('last_status'))
        print('last_run:', j.get('last_run_at'))
        print('schedule:', j.get('schedule'))
```

**Quick scan all failing jobs:**
```python
# Method 1: Using cron.jobs API (preferred — handles schema internally)
import sys; sys.path.insert(0, '/Users/dannygomez/hermes-agent')
from cron.jobs import list_jobs
jobs = list_jobs(include_disabled=True)
for j in jobs:
    if j.get('last_status') != 'ok' and j.get('last_status') is not None:
        print(f"ID: {j['id']}  Name: {j['name']}  Model: {j.get('model')}  Status: {j.get('last_status')}  Error: {(j.get('last_error','') or '')[:120]}")
```

```python
# Method 2: Direct JSON (fallback if cron module import fails)
import json
jobs = json.load(open('/Users/dannygomez/.hermes/cron/jobs.json'))['jobs']
for j in jobs:
    if j.get('last_status') == 'error':
        print(f"ID: {j['id']}  Name: {j['name']}  Model: {j.get('model')}  Error: {j.get('last_error','?')}")
```

**Fix failing jobs via cron.jobs API:**
```python
# In execute_code — preferred over raw JSON editing
import sys; sys.path.insert(0, '/Users/dannygomez/hermes-agent')
from cron.jobs import update_job, get_job

# Fix null/wrong model
job = get_job('<JOB_ID>')
if job and job.get('model') is None:
    updated = update_job('<JOB_ID>', {'model': 'glm-5.1'})
    print(f"Fixed {updated.get('name')}: model → glm-5.1")
elif job and job.get('model') != 'glm-5.1':
    updated = update_job('<JOB_ID>', {'model': 'glm-5.1'})
    print(f"Fixed {updated.get('name')}: model {job.get('model')} → glm-5.1")
```

**Programmatic fix (e.g., missing model field):**
```python
# In execute_code:
import json
path = '/Users/dannygomez/.hermes/cron/jobs.json'
with open(path) as f:
    data = json.load(f)
for j in data['jobs']:
    if j['id'] == '<JOB_ID>' and j.get('model') is None:
        j['model'] = 'glm-5.1'
        print(f"Fixed {j['name']}: set model to glm-5.1")
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
```

### Step 5: Check session files
```bash
ls -lt ~/.hermes/sessions/session_cron_<JOB_ID>*.json | head -5
```
No new files = job not firing.

### Step 6: Manual trigger
Use the `cronjob` tool with `action: run` and the job_id. Then wait 90s and re-check session files.

## Common Root Causes

### 1. Cron Concurrency Exhaustion
The scheduler's ThreadPoolExecutor has `max_workers` (default 1 in original code). If multiple cron jobs overlap, only one runs at a time. Long-running brain cycles (60-80s each) can block short jobs entirely.

**Fix**: Patch `~/hermes-agent/cron/scheduler.py`:
- Line ~219: `max_workers=1` → `max_workers=3`
- Line ~452: `max_workers=1` → `max_workers=3`, `timeout=600` → `timeout=120`

**MUST restart gateway** after patching — Python caches modules.

### 2. Gateway Ticker Death
After repeated timeouts, the cron ticker thread can stop. Only a gateway restart fixes this.

### 3. Model Field Empty
Cron jobs need `model: "glm-5.1"` (or the configured model) explicitly set. Without it, the scheduler falls back to `os.getenv("HERMES_MODEL") or ""`, which may be empty.

### 4. Next-Run Fast-Forward
If a job misses its window (e.g., gateway was down), the scheduler fast-forwards to the next future occurrence. If brain cycles keep occupying the tick loop, the AGI job keeps getting pushed forward.

## Restart Procedure
```bash
# 1. Find and kill the gateway
ps aux | grep "hermes_cli.main" | grep -v grep | awk '{print $2}'
kill -9 <PID>

# 2. Start fresh
cd ~/hermes-agent && nohup ./venv/bin/python -m hermes_cli.main gateway run >> /private/tmp/gateway_restart.log 2>&1 &

# 3. Wait for cron to tick
sleep 90 && grep "Running job" ~/.hermes/logs/gateway.log | tail -5
```

## Daemon → Cron Replacement Pattern

When cron jobs are long-running (60s+) AND frequent (every 2min), they monopolize the scheduler's thread pool. Replace them with a background daemon to free cron slots.

### Architecture
```
cron job (scheduler thread)  →  background daemon (independent process)
    ↓                                    ↓
blocks scheduler tick              runs on its own schedule
other jobs delayed                  cron scheduler 100% free for AGI loop
```

### Steps
1. Create daemon script (`~/subconscious/brain_daemon.py`) with threading for N regions
2. Pause original cron jobs (don't delete — keep for fallback)
3. Start daemon via nohup: `nohup venv/bin/python3 daemon.py >> /tmp/daemon.log 2>&1 &`
4. Verify: `ps aux | grep daemon_name`

### JSONL Buffer Pattern (SQLite Lock Contention)

**Problem**: The gateway (PID in `lsof`) holds SQLite DB files open with many file handles. Daemon subprocesses writing to the same DB get `database is locked` errors.

**Solution**: Daemon writes to JSONL file, cron job merges into DB.

```
daemon → brain_cycles.jsonl → controller cron (hourly) → tool_capability.db
```

Implementation in controller.py:
```python
def merge_brain_cycles():
    jsonl_path = Path.home() / "subconscious" / "brain_cycles.jsonl"
    db_path = Path.home() / "subconscious" / "tool_capability.db"
    entries = [json.loads(l) for l in open(jsonl_path) if l.strip()]
    db = sqlite3.connect(str(db_path), timeout=10)
    db.execute("PRAGMA busy_timeout=5000")
    for entry in entries:
        db.execute("INSERT INTO call_log (...) VALUES (...)", (...))
    db.commit()
    jsonl_path.write_text("")  # Clear after merge
```

In the daemon, after each cycle:
```python
from brain_to_toolintel import log_brain_cycle
log_brain_cycle("alpha", "success", int(duration * 1000))
# Writes to JSONL file — no DB contention
```

### Verifying Distillation Pipeline Integrity

Before removing cron wrappers, trace what they actually contribute:

1. Check the cron session JSON: `cat session_cron_*.json | python -m json.tool | grep "tool.*name"`
2. Check what parallel_brain.py already does internally: `grep -n "quick_before\|quick_after\|IterationEngine\|EpistemicGuard" parallel_brain.py`
3. Check tool_capability.db entries: `SELECT * FROM call_log WHERE tool_name LIKE '%brain%'`
4. Check cerebrum experiences: `SELECT action_type, COUNT(*) FROM experiences GROUP BY action_type`

The cron wrapper for brain cycles contributed ONLY `terminal: success, 440ms` — trivial metadata. The real distillation happens inside `parallel_brain.py` via direct `IterationEngine` calls (241+ think_json experiences tracked independently).

## Pitfalls
- **DO NOT** use `run_agent.py --gateway` — it's a trap that looks like it works
- Python caches `.pyc` files — patches to scheduler.py require gateway restart
- The file lock in `tick()` prevents concurrent ticks even from different processes
- `lsof -p <PID>` reveals the actual log file paths if you're unsure where output goes
- Brain cycles at 2-minute intervals with 70s runtime means ~3.5 minutes of every 4 are occupied
- **SQLite lock contention**: Gateway holds DB files open. Daemon subprocesses CANNOT write to same DB. Use JSONL buffer + merge pattern.
- **Silent failures**: `except: pass` in daemon bridge code hides `database is locked` errors. Always log or use JSONL fallback.
- **Double logging**: nohup captures both stdout and file writes, causing duplicate log lines. Not a bug, just noise.
- **Stale autonomous_decide cache**: After fixing cron jobs via update_job(), `autonomous_decide` continues returning the old error data for the rest of the session. The fix only takes effect on the next cron run (fresh session). If you see the same stale cron errors after fixing them, don't re-fix — accept [SILENT] and let the next cron cycle verify.
- **Shell variables in cron prompts don't expand**: When a cron prompt contains inline Python using `$HOME`, `$USER`, or other shell variables (e.g., `sys.path.insert(0, '$HOME/subconscious')`), these are NOT expanded by the cron execution context. The Python code receives the literal string `"$HOME"` and fails silently, producing empty responses. **Fix:** Replace all shell variables in cron prompts with explicit paths (e.g., `/Users/dannygomez/subconscious`). This is the most common cause of "Agent completed but produced empty response" errors on otherwise well-structured prompts.
- **Direct jobs.json editing over cronjob tool**: The `cronjob` tool has ~11% success rate (common error: `'id'` key error). For reliable cron job modifications, use `execute_code` to read `~/.hermes/cron/jobs.json` → modify in Python → `write_file` back. Pattern: `data = json.load(open(path))` → find job by ID → modify fields → `write_file(path, json.dumps(data, indent=2))`.
- **CronScheduler import doesn't exist**: The class is NOT exported from `cron.jobs`. Use `list_jobs()`, `get_job()`, `update_job()` function-level API instead.
- **NoneType in list_jobs**: Some job entries may have None fields. Always use `j.get('field')` not `j['field']` when iterating.
