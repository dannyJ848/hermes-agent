# Cronjob Tool: 17% Success Rate — Use Direct Methods Instead

**Date:** 2026-05-15
**Status:** Confirmed over multiple sessions
**Severity:** High — do not rely on this tool for production scheduling

## Problem

The `cronjob` tool (Hermes built-in cron scheduler) has a **~17% success rate** based on observed behavior across sessions. Common failure modes:

1. `{'error: "'id'", success: False}` — KeyError when creating or removing jobs
2. Silent failures — job appears created but never executes
3. Database corruption — nested quotes in prompts break JSON parser
4. No execution — jobs scheduled but `tick()` never triggered

## Evidence

Session 2026-05-15: Creating a simple cron job for propaganda demystifier pipeline:
```
cronjob(action='create', name='propaganda-demystifier-daily', 
        schedule='0 6 * * *', script='cd ~/propaganda-demystifier && python3 run_pipeline.py')
```
Result: Success (but this is the exception, not the rule)

Previous sessions: 5+ consecutive failures before success, requiring manual workarounds.

## Workarounds (In Order of Reliability)

### 1. System Crontab (Most Reliable)
```bash
crontab -e
# Add:
0 6 * * * cd /Users/dannygomez/propaganda-demystifier && python3 run_pipeline.py >> logs/cron.log 2>&1
```

### 2. Persistent Python Daemon
See `references/unified-daemon-pattern.md` — self-looping daemon with signal handling.

### 3. Direct JSON Editing (When Tool Fails)
```python
import json
from datetime import datetime, timezone, timedelta

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'r') as f:
    data = json.load(f)

# Add job manually
new_job = {
    "job_id": "manual-" + datetime.now().strftime("%Y%m%d%H%M%S"),
    "name": "my-job",
    "schedule": "0 6 * * *",
    "script": "cd ~/project && python3 script.py",
    "enabled": True,
    "state": "scheduled",
    "next_run_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
}
data['jobs'].append(new_job)

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
    json.dump(data, f, indent=2)
```

### 4. Launchd (macOS Native)
```xml
<!-- ~/Library/LaunchAgents/com.propaganda.daily.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.propaganda.daily</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/dannygomez/opt/anaconda3/bin/python3</string>
        <string>/Users/dannygomez/propaganda-demystifier/run_pipeline.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/dannygomez/propaganda-demystifier/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/dannygomez/propaganda-demystifier/logs/launchd.error.log</string>
</dict>
</plist>
```
Load: `launchctl load ~/Library/LaunchAgents/com.propaganda.daily.plist`

## When to Use the Tool Anyway

The `cronjob` tool CAN work for simple cases:
- No nested quotes in prompts/scripts
- No special characters in job names
- Immediate verification planned (check `jobs.json` after creation)

**Always verify:**
```bash
cat ~/.hermes/cron/jobs.json | python3 -m json.tool > /dev/null && echo "JSON valid" || echo "JSON BROKEN"
```

## Recommendation

For production automation, **never rely solely on the cronjob tool**. Use system crontab or launchd as the primary mechanism, with the cronjob tool as a convenience wrapper only.
