# Sparse Status Monitoring Pattern

**Learned:** Apr-May 2026 from user directive "NO unsolicited status" + "Keep status checks sparse"
**Context:** Training jobs, long-running processes, background tasks

## User Preference (First-Class Constraint)

User explicitly said:
- "NO unsolicited status"
- "Keep status checks sparse"
- "can you make a fix or skill update or tracker to alert and break when you fall into a loop?"

This is NOT a suggestion — it's a hard constraint. Violating it wastes tokens AND annoys the user.

## The Wrong Way (Loop-Prone)

```
User: start training, monitor it
Agent: [starts training]
Agent: [2 min later] still running...
Agent: [2 min later] still running...
Agent: [2 min later] still running...
[User returns to 6 status updates and 0 actual progress]
```

This is a status-check loop — same tool call, same result, no state change.

## The Right Way (Sparse, Cron-Based)

1. **Initial check** (one comprehensive call):
   ```bash
   ps aux | grep process | grep -v grep; echo "---"; tail -20 logfile; echo "---"; du -sh output_dir
   ```

2. **Set up cron** to monitor every 10-30 minutes:
   - Check if process is still running
   - If NOT running, check log for error → ALERT user with error details
   - If running normally → SILENT (no message)

3. **Stay silent** in conversation thread until:
   - Cron fires with crash alert
   - User asks "status?"
   - Training completes

## Token-Conscious Rule

After confirming a process started successfully:
- Do NOT check again manually
- Do NOT report "still running"
- Do NOT poll in a conversation loop
- Let cron handle it. Be silent.

## Integration with Loop Detection

Status-check loops are a SUBTYPE of repetitive tool-call loop:
- Same tool: terminal/SSH
- Same args: checking process status
- Same result: "still running"
- No state change between calls

**Detection:** If you've checked the same process status 2+ times in one session → STOP and set up cron instead.
