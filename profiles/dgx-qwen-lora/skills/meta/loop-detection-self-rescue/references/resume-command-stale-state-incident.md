# Resume Command Stale State Incident — May 2, 2026

## Incident

User asked for resume command to switch to CLI. Agent generated a resume command referencing:
- Old blocker: `train_modelscope_gpu.py line 247` (vocab_size fix)
- Old PID: 879375
- Old file paths and status from hours earlier

User response: "wait has this all been updated with the deepspeed build you are working on?"

Then: "bro wtf, save and update with the CURRENT status of everything."

## Root Cause

Agent composed resume command from memory of EARLIER session state, without querying current:
- Git commit status
- Running processes on Spark
- File timestamps
- Actual current blockers

The resume command was stale by ~4 hours of active debugging.

## Lesson

**When generating resume commands or status summaries, ALWAYS query current state first:**

1. `git log --oneline -1` — confirm commit hash
2. `git status --short` — confirm working tree clean
3. `ssh spark "ps aux | grep ..."` — confirm running processes
4. `ls -la` key files — confirm timestamps
5. `tail` recent logs — confirm current errors

**Only THEN compose the resume command with CURRENT data.**

Stating stale state as current breaks user trust and wastes their time.

## User Signal

User frustration: "bro wtf" — clear signal that agent was not paying attention to current state.
This is a FIRST-CLASS skill signal, not just a memory signal. The skill governing resume/status generation needs to carry the lesson.
