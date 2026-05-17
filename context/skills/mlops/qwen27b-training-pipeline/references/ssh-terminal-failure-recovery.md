# SSH Terminal Failure Recovery Pattern

## Context
When SSH connections to DGX fail repeatedly (exit code 255, empty output, connection timeout), the `terminal` tool hits Hermes' same-tool-failure guardrail after 5 consecutive failures and halts. This prevents infinite loops but also blocks progress.

## Symptoms
- `ssh: connect to host ... port 22: Operation timed out`
- Exit code 255 with empty output
- `same_tool_failure_warning` after 3 failures
- `same_tool_failure_halt` after 5 failures
- Process may still be running on DGX despite SSH being unresponsive

## Recovery Strategy

### Option 1: Wait and Retry (Process Still Running)
DGX SSH daemon may be temporarily saturated under training load. Wait 2-5 minutes, then retry with short timeouts:
```bash
ssh -o ConnectTimeout=5 -o ServerAliveInterval=3 djg6228@10.0.0.171 'echo OK'
```

### Option 2: Use DGX-Local Monitoring (No SSH Needed)
If training is already running, rely on DGX-local cron watchdog instead of SSH polling:
- DGX-local script checks process and pushes alerts via ntfy.sh
- No SSH dependency for monitoring

### Option 3: Accept Process Death and Restart
If SSH is completely unresponsive for >5 minutes:
1. DGX likely needs power cycle (user action)
2. After reboot, check if process survived: `ps aux | grep python3`
3. If dead, check log tail for crash reason
4. Relaunch from latest checkpoint

### Option 4: Reduce DGX Load Before SSH
If you MUST SSH during training:
- Lower training process priority: `renice +10 -p <pid>`
- This preserves SSH responsiveness at cost of ~5-10% training speed

## Anti-Pattern: Repeated Identical SSH Calls
Don't execute the same SSH command 5+ times with identical parameters. If it failed twice with the same error, the third attempt won't magically succeed. Change strategy instead.

## Prevention
- Use `nice -n 10` when launching training to preserve SSH headroom
- Deploy DGX-local cron watchdog for monitoring (no SSH needed)
- Use ntfy.sh alerts instead of active SSH polling
- Keep atomic launch scripts that prevent process duplication (reduces load)
