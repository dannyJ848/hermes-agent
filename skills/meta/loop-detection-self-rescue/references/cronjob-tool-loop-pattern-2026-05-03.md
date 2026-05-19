# Cronjob Tool Loop Pattern — May 3, 2026

## Incident
The `cronjob(action='list')` tool returned `{'error': "'id'", 'success': False}` on every call. I called it 3+ times in a row without trying a different approach.

## Root Cause
- The cronjob tool has a bug where `list` action fails with `KeyError: 'id'`
- I kept calling it because it was the "right" tool for the job
- No hard enforcement prevented the repetition

## Lesson
**When a tool returns the SAME error repeatedly, STOP after the FIRST failure.** Do not retry the same broken tool 2+ times. Switch to a workaround immediately:
- Direct file editing (e.g., `cat ~/.hermes/cron/jobs.json | python3 -m json.tool`)
- Alternative tool (e.g., `terminal` with `ls` and `grep`)
- Escalate to user

## User Signal
User said: "no fix your toolfix your toolfix your tool" — this was a frustration escalation. The repetition in their message mirrored my repetition. When user repeats themselves, severity is HIGH.

## Fix Applied
- Built `/tmp/hermes_loop_guard.py` hard enforcement script
- Patched `cron/jobs.py` line 845: `rj["id"]` → `rj.get("id")`
- Started scheduler daemon `/tmp/hermes_scheduler_daemon.py`
