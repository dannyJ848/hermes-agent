# Local Disk Full — Remote Script Writing Workaround

## Problem

When local MacBook disk is near 100% capacity, Hermes `write_file` tool fails because:
1. The tool writes to local temp files first
2. Hermes itself creates snap/cwd temp files in `/var/folders/.../`
3. No space for any file operations

**Error symptoms:**
```
Failed to write file: /bin/bash: line 2: /tmp/start_script.sh: No space left on device
/bin/bash: line 4: /var/folders/6p/.../hermes-snap-XXXX.sh: No space left on device
/bin/bash: line 5: /var/folders/6p/.../hermes-cwd-XXXX.txt: No space left on device
```

## Workaround: Create Files Directly on Remote Host

Instead of writing locally and scp'ing, create the script on the remote machine via SSH:

### Method 1: cat with heredoc (avoid if shell quoting is complex)
```bash
ssh user@host "cat > /tmp/start_task.sh << 'EOF'
#!/bin/bash
cd /project && source venv/bin/activate
lm_eval --tasks bbh ... > /tmp/lm_eval_bbh.log 2>&1 &
echo \$!
EOF"
```

**Caveat:** The `\$!` escape is needed so `$!` is written literally to the remote file, not expanded locally.

### Method 2: printf (cleaner, no heredoc issues)
```bash
ssh user@host "printf '%s\n' '#!/bin/bash' 'cd /project' 'source venv/bin/activate' 'lm_eval --tasks bbh ... > /tmp/lm_eval_bbh.log 2>&1 &' 'echo \$!' > /tmp/start_task.sh"
```

**Advantage:** No heredoc terminator to worry about. Each line is a separate argument to printf.

### Method 3: echo with explicit newlines (simple scripts only)
```bash
ssh user@host "echo '#!/bin/bash
cd /project
source venv/bin/activate
lm_eval --tasks bbh ... > /tmp/lm_eval_bbh.log 2>&1 &
echo \$!' > /tmp/start_task.sh"
```

**Caveat:** `echo` with `\n` may not work on all shells. Use printf for reliability.

## Verification

After creating the script remotely, verify it was written correctly:
```bash
ssh user@host "cat /tmp/start_task.sh"
```

Then execute:
```bash
ssh user@host "bash /tmp/start_task.sh > /tmp/task.pid; cat /tmp/task.pid"
```

## Prevention

Monitor local disk usage proactively:
```bash
df -h | grep -E '/$|/System/Volumes/Data'
```

If usage > 95%, alert the user to clean up before attempting file operations.

**Common MacBook space hogs:**
- `~/datasets` — ML datasets (often 100GB+)
- `~/Downloads` — accumulated downloads
- `~/Library/Caches` — app caches
- `~/Library/Developer/CoreSimulator` — iOS simulator images
- `~/.ollama` — Ollama model files
- `~/.hermes` — Hermes workspace and knowledge files
- `~/.claude-worktrees` — Claude Code worktrees
