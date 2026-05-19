# SSH Background Process Spawning Pattern

**Problem:** Hermes terminal tool rejects shell-level backgrounding (`&`, `nohup`, `setsid`, `disown`) in foreground SSH commands. This makes it impossible to start long-running remote processes and capture their PID in a single command.

**The `necho` Bug:**
```bash
ssh user@host "command &\necho $!"
# Result: bash: line 1: necho: command not found
# The \n before echo gets concatenated with the preceding & → "&echo" → "necho"
```

## Working Pattern: Remote Script File

### Step 1: Write script locally
```bash
cat > /tmp/start_bg.sh << 'EOF'
#!/bin/bash
cd /project && source venv/bin/activate
long_running_command > /tmp/output.log 2>&1 &
echo $! > /tmp/process.pid
EOF
```

### Step 2: Copy to remote and execute
```bash
scp /tmp/start_bg.sh user@host:/tmp/
ssh user@host "bash /tmp/start_bg.sh; sleep 3; cat /tmp/process.pid"
```

### Step 3: Verify in separate call
```bash
ssh user@host "ps aux | grep $(cat /tmp/process.pid) | grep -v grep"
```

## Alternative: Hermes terminal(background=true)

For the entire SSH session to be backgrounded:
```python
terminal(background=true, command="ssh user@host 'bash /tmp/start_bg.sh'")
# Then verify:
terminal(command="ssh user@host 'cat /tmp/process.pid'")
```

## Why This Works

- The script file contains the `&` backgrounding, but it's INSIDE the script
- The SSH command itself is a simple foreground invocation: `bash /tmp/start_bg.sh`
- The script's `echo $!` writes the PID to a file, which we read in a follow-up call
- No shell-level background wrappers in the SSH command itself

## Anti-Patterns to Avoid

| Pattern | Why It Fails |
|---------|-------------|
| `ssh host "cmd &"` | Terminal tool rejects `&` in foreground |
| `ssh host "nohup cmd &"` | Terminal tool rejects `nohup` |
| `ssh host "setsid cmd &"` | Terminal tool rejects `setsid` |
| `ssh host "cmd &\necho \$!"` | `\n` becomes `n` → `necho` command not found |
| `ssh host "cmd >log 2>&1 </dev/null &"` | `&` still rejected |

## Session Reference

**Date:** May 2026  
**Hardware:** DGX Spark (GB10)  
**Use case:** Starting lm-eval-harness benchmarks that run for 10+ hours  
**Process:** PID tracking for health monitoring and restart
