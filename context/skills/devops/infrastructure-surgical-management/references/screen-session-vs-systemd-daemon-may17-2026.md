# Screen Session vs Systemd Daemon Preference (May 17, 2026)

## User Statement

> "eliminate any daemon, I don't want it depending on any daemon. it should be able to go autonomous with tool calling, etc for the whole night."

## Interpretation

User wants autonomous agents that run overnight but **explicitly rejects systemd dependency**. This is a strong architectural preference:
- No systemd unit files
- No systemctl commands
- No service management
- Process persistence through GNU screen or tmux only

## Screen Session Pattern for Autonomous Agents

### Start
```bash
# Kill any existing session first (clean start)
screen -S hermes_auto -X quit 2>/dev/null
sleep 2

# Start new detached session
cd /data/SpecForge/hermes-agent
screen -dmS hermes_auto bash -c '
    export PYTHONPATH=/data/SpecForge/hermes-agent
    venv/bin/python3 /tmp/autonomous_runner_v2.py
'

# Verify
screen -ls | grep hermes_auto
```

### Monitor
```bash
# Attach interactively
screen -r hermes_auto

# Detach without killing (Ctrl+A then D)

# Check logs without attaching
tail -f /tmp/hermes_auto_v2.txt

# Check if running
screen -ls
ps aux | grep autonomous_runner | grep -v grep
```

### Stop
```bash
# Kill the session
screen -S hermes_auto -X quit

# Or from inside the session
# Ctrl+A then K then Y
```

## Why Screen/Tmux Over Systemd

| Aspect | Screen/Tmux | Systemd |
|--------|-------------|---------|
| Dependency | None (user process) | systemd (system service) |
| User control | Full (user owns session) | Requires root/sudo for system units |
| Portability | Any Unix system | Linux-only with systemd |
| Complexity | Single command | Unit file + systemctl + journalctl |
| Recovery | Reattach to existing session | systemctl restart + journalctl debug |
| Logs | File-based, user-controlled | journald, may require root to read |

## Anti-Pattern: Systemd Service

```bash
# NEVER do this for user's autonomous agents:
sudo tee /etc/systemd/system/hermes-dgx.service << 'EOF'
[Unit]
Description=DGX Hermes Agent
[Service]
ExecStart=/path/to/agent
Restart=always
EOF
sudo systemctl enable hermes-dgx
sudo systemctl start hermes-dgx

# User explicitly rejected this pattern
```

## Session Reference

- Date: May 17, 2026
- Context: DGX Hermes autonomous deployment with Qwen3.6-27B-Uncensored
- User rejected systemd daemon after it was created
- Switched to screen session `hermes_auto`
- Log: `/tmp/hermes_auto_v2.txt`
- Autonomous runner: `/tmp/autonomous_runner_v2.py`
