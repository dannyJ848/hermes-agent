# DGX Hermes Screen Session Preference (No Systemd Daemons)

## User Preference

User explicitly and emphatically rejected systemd daemon services for persistent Hermes processes on DGX:

> "eliminate any daemon, I don't want it depending on any daemon. it should be able to go autonomous with tool calling, etc for the whole night."

## Rationale

- User wants autonomous agents that run overnight without systemd dependency
- Screen/tmux sessions survive user logout and run independently
- No systemd unit files, no systemctl, no service management
- Process persistence through GNU screen or tmux only

## Pattern

### Start Autonomous Hermes in Screen

```bash
# Kill any existing session
screen -S hermes_auto -X quit 2>/dev/null
sleep 2

# Start new detached session
cd /data/SpecForge/hermes-agent
screen -dmS hermes_auto bash -c "
    export PYTHONPATH=/data/SpecForge/hermes-agent
    /data/SpecForge/hermes-agent/venv/bin/python3 /tmp/autonomous_runner_v2.py
"

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
ps aux | grep autonomous_runner
```

### Never Use

```bash
# DO NOT create systemd services
sudo systemctl enable hermes-dgx  # NO
sudo systemctl start hermes-dgx   # NO

# DO NOT use /etc/systemd/system/
# DO NOT use systemctl restart/status/stop
```

## Session Reference

- Date: May 17, 2026
- Context: DGX Hermes autonomous deployment
- User explicitly rejected daemon approach after systemd service was created
- Fix: Killed all systemd services, switched to screen session
- Screen session: `hermes_auto`
- Log: `/tmp/hermes_auto_v2.txt`
