# Process Polling Loop Incident — May 3, 2026

## Incident
During Qwen 27B training monitoring, agent fell into a repetitive `process.poll()` loop:
- Polled the same background process 40+ times consecutively
- Output preview was identical across all polls (stuck at "Loading weights: 55%")
- No user message between polls, no meaningful state change
- Burned ~40 tool calls with zero forward progress

## Root Cause
Agent was "waiting" for model loading to complete but used active polling instead of:
1. Single `process.wait(timeout=180)` call, OR
2. Checking log file with `tail`, OR
3. Simply waiting silently

## Pattern: The "Loading Wait" Anti-Pattern
When a background process is loading a large model:
- **DON'T**: Poll every few seconds hoping for progress
- **DO**: Use `process.wait(timeout=300)` once, then check logs
- **DO**: If you MUST poll, max 3 polls with 60s gaps, then check logs directly

## Detection Heuristic
```
if poll_count > 3 and last_output == current_output:
    LOOP_DETECTED → break, check logs instead
```

## Fix Applied
After ~40 wasted polls, agent finally used `process.wait(timeout=180)` which revealed:
- Model loading progressed from 55% → 98% during the wait
- Training started successfully after 172s total load time

## Lesson
For long-running background tasks (model loading, training, compilation):
- Use `wait()` with generous timeout, not rapid-fire polling
- If process output is stale, check the log file — don't re-poll
- Set a hard cap: 3 polls max, then escalate or change strategy
