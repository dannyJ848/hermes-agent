# Git Commit Timeout Loop Incident — May 3, 2026

## Incident

During a Qwen 27B training session checkpoint, `git add -A` on the remote machine hung for 180+ seconds. The agent then made repeated SSH calls to "fix" the issue, each timing out.

## Sequence of Events

1. `git add -A` timed out (180s) — likely due to large untracked directories
2. Agent tried `git status --short | wc -l` — also timed out
3. Agent tried `rm -f index.lock` — timed out
4. Agent tried `git add -A -- ':!hidden_states'` — timed out
5. Agent tried `ps aux | grep git` — timed out
6. User said "stuck in a loop" — agent finally stopped

## Root Cause

The `git add -A` process was still running on the remote machine, consuming CPU and holding the index.lock. Each new SSH command tried to acquire the same lock, causing cascading timeouts.

## Resolution

1. Wait for SSH to recover (remote process eventually completed or was killed)
2. Clear index.lock: `rm -f /data/SpecForge/.git/index.lock`
3. Kill stuck git processes: `kill -9 <pid>`
4. Use targeted `git add` excluding large directories: `git add -A -- ':!hidden_states' ':!checkpoints'`
5. Commit with reasonable timeout

## Prevention

- **Never use `git add -A` on repos with large data directories** — always exclude them
- **After first timeout, STOP** — don't make more SSH calls
- **Use `-- ':!dir'` pattern** to exclude known-large directories
- **Set shorter timeouts** (15-30s) for git operations to fail fast
- **If timeout occurs, escalate to user** rather than retrying

## User Preference

User explicitly said: "commit everything, I need to ensure every CLI in the future knows every detail"

This means:
- Exclude only large data directories (hidden_states, checkpoints, teacher_outputs)
- Commit ALL scripts, configs, audit reports, and artifacts
- Document the commit hash in checkpoint files and memory
