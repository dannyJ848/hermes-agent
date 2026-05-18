# Cron Scheduler Daemon Pattern — May 3, 2026

## Problem
The Hermes `cronjob` tool fails with `KeyError: 'id'` when some jobs lack an `id` field. This causes the tool to return `{'error: 'id', success: False}` repeatedly, creating a loop when the agent keeps retrying the broken tool.

## Root Cause
In `cron/jobs.py` line 845, the code does `rj["id"]` instead of `rj.get("id")`. When a job entry lacks the `id` key, it raises `KeyError` which gets swallowed and returned as a cryptic error.

## Fix
Patch `cron/jobs.py`:
```python
# OLD (broken):
id = rj["id"]
# NEW (fixed):
id = rj.get("id")
# Same for job["id"] -> job.get("id")
```

## Workaround: Scheduler Daemon
When the cron tool is broken, start a standalone daemon that bypasses the tool entirely:

```python
# /tmp/hermes_scheduler_daemon.py
import sys, os, time
from pathlib import Path
sys.path.insert(0, str(Path.home() / "hermes-agent"))
from cron.scheduler import tick

while True:
    try:
        tick()
    except Exception as e:
        print(f"Scheduler error: {e}")
    time.sleep(60)
```

Run it:
```bash
export DEEPSEEK_API_KEY=$(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)
cd ~/subconscious && nohup python3 /tmp/hermes_scheduler_daemon.py >> /tmp/scheduler.log 2>&1 &
```

## Key Lessons
1. **Broken tool → immediate workaround**: Don't retry a broken tool 2+ times. Switch to direct file editing or an alternative approach immediately.
2. **Cron jobs.json is the source of truth**: When the tool fails, read `~/.hermes/cron/jobs.json` directly with Python/json instead of using the broken tool.
3. **Mass disable then selective re-enable**: Kill all jobs first (`all_disabled = True`), then selectively re-enable only the ones that matter. This prevents 42 zombie jobs from cluttering the scheduler.
4. **API key in ~/.hermes/.env**: The scheduler daemon needs `DEEPSEEK_API_KEY` from `~/.hermes/.env`. Always export it before starting the daemon.
5. **Monitor output directories**: Job output appears in `~/.hermes/cron/output/<job_id>/`. Check these directories to verify jobs are actually running.
