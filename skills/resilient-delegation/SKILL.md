---
name: resilient-delegation
version: 1.0
description: Delegate tasks with automatic retry on API failure. Prevents silent single-agent fallback.
category: autonomous-ai-agents
---

# Resilient Delegation Pattern

## Problem
`delegate_task` subagents can fail with "API call failed after 3 retries" or timeout errors. These return `status: "completed"` but with no useful output, silently degrading to single-agent mode.

## Solution: Retry-then-escalate

### Pattern
```
1. delegate_task with 3 parallel tasks
2. Check each result for failure signatures:
   - summary contains "API call failed"
   - summary contains "timed out"  
   - tokens.output < 100
   - exit_reason is "max_iterations" with low output
3. If failed: retry ONCE with a simpler/shorter task description
4. If retry fails: do it manually (but log it)
5. ALWAYS notify Danny via Telegram when agents fail
```

### Failure Detection
Check result.summary for:
- "API call failed after 3 retries"
- "The read operation timed out"
- "timed out"
- tokens.output < 200 (likely failed silently)

### Telegram Notification on Failure
```python
python3 << 'PYEOF'
import sys; sys.path.insert(0, '/tmp')
from soma_notify import send_status
send_status("SUBAGENT DOWN: [task name] failed. Retrying...", "warning")
PYEOF
```

### Retry Strategy (INFINITE)
- Agent fails? -> Respawn it in the NEXT delegate_task call with the same task
- Always batch failed tasks into the next parallel delegation
- Keep the other 2 slots for NEW tasks (don't waste slots on retries)
- Pattern: [failed_task_retry, new_task_1, new_task_2]
- Ping Danny on each failure + respawn cycle

### Loop Pattern
```
while (work_remaining):
    tasks = pick_up_to_3_tasks()  # prioritize retries over new work
    results = delegate_task(tasks)
    for each failed result:
        Telegram: "Agent X down, respawning next round"
        requeue(task)
    for each succeeded result:
        mark_done(task)
```

### Rules
- NEVER silently fall back to solo mode
- ALWAYS ping Danny on Telegram when any agent fails
- Failed tasks get priority in next delegation batch
- If ALL 3 agents fail: wait 60s, then retry (API may be down)
- No max retries - keep respawning until the work is done
