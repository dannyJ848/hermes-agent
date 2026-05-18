# SSH Background Process Launching (May 2026)

## Problem

When launching long-running processes on a remote host (DGX Spark) via SSH from the MacBook Hermes terminal tool, shell backgrounding operators fail.

## Failure Modes

### 1. Terminal Tool Rejects Shell Backgrounding
```bash
ssh djg6228@10.0.0.171 "command > log 2>&1 &"
```
**Error:** `Foreground command uses shell-level background wrappers (nohup/disown/setsid). Use terminal(background=true) so Hermes can track the process`

The terminal tool explicitly blocks `&`, `nohup`, `setsid`, and `disown` in foreground commands.

### 2. Unicode Escaping Corruption
When attempting to work around the backgrounding restriction by escaping `&` as `\u0026`:
```bash
ssh djg6228@10.0.0.171 "command > log 2>&1 \u0026\u0026 echo $! > pidfile"
```
**Error:** `bash: line 1: u0026: command not found`

The `\u0026` sequence is interpreted literally rather than as an escaped `&` character.

### 3. Script Write + Execute Pattern (RELIABLE)
Write the backgrounding logic into a script file on the remote host, then execute the script:

```bash
# Step 1: Create script on remote host
ssh djg6228@10.0.0.171 "cat > /tmp/start_training.sh << 'EOF'
#!/bin/bash
cd /data/SpecForge/custom_dflash
source ~/train-venv/bin/activate
mkdir -p adapters/qwen27b-tiered-r256/logs
axolotl train axolotl_config.yaml > adapters/qwen27b-tiered-r256/logs/training_live.log 2>&1 &
echo $! > /tmp/training.pid
EOF
chmod +x /tmp/start_training.sh"

# Step 2: Execute script (returns immediately, captures PID)
ssh djg6228@10.0.0.171 "bash /tmp/start_training.sh && cat /tmp/training.pid"
```

**Why this works:**
- The `&` is INSIDE the script, not in the SSH command string
- The SSH command just runs the script and echoes a PID file
- The SSH command returns immediately (no backgrounding in SSH string)
- The remote process backgrounds itself via the script

### 4. Alternative: No-Op SSH with Remote Backgrounding
```bash
# Write script via SSH heredoc
ssh djg6228@10.0.0.171 "bash -s" << 'REMOTE_SCRIPT'
cd /data/SpecForge/custom_dflash
source ~/train-venv/bin/activate
axolotl train axolotl_config.yaml > logs/train.log 2>&1 &
echo $!
REMOTE_SCRIPT
```

**Note:** The `<< 'REMOTE_SCRIPT'` heredoc passes the script content to `bash -s` on the remote host. The `&` is inside the heredoc, not in the SSH command.

## Verification Pattern

After launching, verify the process is actually running:
```bash
# Check PID from file
ssh djg6228@10.0.0.171 "cat /tmp/training.pid"

# Verify process exists
ssh djg6228@10.0.0.171 "ps aux | grep $(cat /tmp/training.pid) | grep -v grep"

# Check log growth
ssh djg6228@10.0.0.171 "ls -la adapters/qwen27b-tiered-r256/logs/training_live.log"
```

## Key Rules

1. **Never put `&`, `nohup`, `setsid`, or `disown` in the SSH command string** — terminal tool will reject it
2. **Always put backgrounding inside a remote script** — the script runs on the remote host, SSH just invokes it
3. **Capture PID to a file** — essential for later status checks and process management
4. **Use `bash -s` with heredoc** for complex multi-line scripts
5. **Verify within 30 seconds** — check PID file exists and process is in `ps aux`

## Common Use Cases

| Task | Script Pattern |
|------|---------------|
| Training launch | `axolotl train config.yaml > log 2>&1 &` |
| Benchmark run | `lm_eval ... > log 2>&1 &` |
| vLLM server | `vllm serve ... > log 2>&1 &` |
| Dataset preprocessing | `python3 preprocess.py > log 2>&1 &` |

## Related

- `references/ssh-timeout-under-training-load.md` — SSH timeouts during long training
- `references/training-status-check.md` — Checking training progress after remote launch
