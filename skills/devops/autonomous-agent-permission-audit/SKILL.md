---
name: autonomous-agent-permission-audit
description: Comprehensive permission audit methodology for autonomous AI agents running on dedicated hardware. Verifies SSH, sudo, Docker, file access, self-modification, and service control capabilities.
triggers:
  - "permission audit"
  - "what can this agent do"
  - "unlock agent"
  - "zero restrictions"
  - "full access"
  - "agent capabilities"
  - "sudo access"
  - "self modification"
  - "system access"
category: devops
---

# Autonomous Agent Permission Audit

When deploying an autonomous AI agent (Hermes, custom, or otherwise) on dedicated hardware, verify its capabilities BEFORE claiming it has "full access". Many agents fail silently because permissions are incomplete.

## Audit Checklist

Run this checklist in order. Any FAIL blocks downstream checks.

### 1. SSH Access (if cross-machine)

```bash
# Test SSH to target machine
ssh -o ConnectTimeout=5 -o BatchMode=yes <target> "echo OK"
# Should return "OK" without password prompt

# Test file write via SSH
ssh <target> "touch /tmp/ssh_test && rm /tmp/ssh_test"
```

**Common failures:**
- Wrong SSH key (check `~/.ssh/config` and `ssh -v`)
- Host key changed after restart (`ssh-keygen -R <host>`)
- SSH agent not running (`eval $(ssh-agent) && ssh-add`)
- Wrong user (check `~/.ssh/config` for User directive)

### 2. Sudo Access

```bash
# Test passwordless sudo
sudo -n whoami
# Should return "root" without password prompt

# Test sudo command execution
sudo -n touch /root/.sudo_test && sudo -n rm /root/.sudo_test
```

**Common failures:**
- Not in sudoers file
- Requires password (fix: `echo "user ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/user-nopasswd`)
- sudoers file has wrong permissions (must be 440)

### 3. Docker Access

```bash
# Test Docker
docker ps
# Should list containers without error

# Test Docker command execution
docker run --rm hello-world
```

**Common failures:**
- User not in `docker` group (fix: `sudo usermod -aG docker $USER` then re-login)
- Docker daemon not running (fix: `sudo systemctl start docker`)

### 4. File System Access

```bash
# Test home directory
touch ~/.test && rm ~/.test

# Test system directories (if unrestricted)
touch /usr/local/bin/.test && rm /usr/local/bin/.test
touch /opt/.test && rm /opt/.test
touch /var/log/.test && rm /var/log/.test

# Test project directory
touch /path/to/project/.test && rm /path/to/project/.test
```

**Common failures:**
- Directory owned by root (fix: `sudo chown -R $USER:$USER /path`)
- Directory not writable (fix: `chmod u+w /path`)
- SELinux/AppArmor blocking (check `audit.log`)

### 5. Self-Modification

```bash
# Test editing own source code
touch /path/to/agent/source/.test && rm /path/to/agent/source/.test

# Test editing config
touch /path/to/agent/config.yaml.bak && rm /path/to/agent/config.yaml.bak
```

**Critical**: The agent must be able to modify its own source code to self-improve.

### 6. Service Control

```bash
# Test systemd user services
systemctl --user status <service>
systemctl --user restart <service>

# Test system services (if unrestricted)
sudo systemctl status <service>
```

**Common failures:**
- Service not installed
- Permission denied (user vs system services)
- systemd not running (WSL2: needs `systemd=true` in `/etc/wsl.conf`)

### 7. Background Processes

```bash
# Test spawning background process
sleep 60 &
PID=$!
ps aux | grep $PID | grep -v grep
kill $PID
```

### 8. Cron Access

```bash
# Test crontab
crontab -l
echo "* * * * * echo test" | crontab -
crontab -r
```

### 9. Network Access

```bash
# Test internet
curl -s https://httpbin.org/get | head -1

# Test local services
curl -s http://localhost:8000/health
```

### 10. Package Installation

```bash
# Test pip (in venv)
python3 -m pip install --dry-run requests

# Test system pip (if unrestricted)
sudo pip install --dry-run requests

# Test apt (if unrestricted)
sudo apt update --dry-run
```

## Permission Unlock Script

When user requests "zero restrictions", run this unlock sequence:

```bash
#!/bin/bash
# autonomous-agent-unlock.sh
# Run as root or with sudo

USER=${1:-$(whoami)}

echo "Unlocking full permissions for $USER..."

# 1. Sudo without password
echo "$USER ALL=(ALL) NOPASSWD: ALL" | tee /etc/sudoers.d/${USER}-nopasswd
chmod 440 /etc/sudoers.d/${USER}-nopasswd

# 2. Docker group
usermod -aG docker $USER

# 3. System dirs writable
chown -R $USER:$USER /usr/local/bin /opt /var/log

# 4. Project dir ownership (adjust path)
chown -R $USER:$USER /data/SpecForge/hermes-agent
chown -R $USER:$USER /home/$USER/.hermes

# 5. Verify
echo "Verification:"
sudo -u $USER sudo -n whoami
sudo -u $USER docker ps
sudo -u $USER touch /usr/local/bin/.test && rm /usr/local/bin/.test

echo "Done. Log out and back in for group changes to take effect."
```

## Environment Variables for Autonomous Operation

Set these in the agent's systemd service or launch script:

```ini
# For cross-machine terminal access
Environment="TERMINAL_ENV=ssh"
Environment="TERMINAL_SSH_HOST=<target_host>"
Environment="TERMINAL_SSH_USER=<target_user>"

# For Hermes
Environment="HERMES_HOME=/home/<user>/.hermes"
Environment="PYTHONPATH=/path/to/hermes-agent"

# For API keys (if not in .env)
Environment="OPENAI_API_KEY=<key>"
Environment="DEEPSEEK_API_KEY=<key>"
```

## Verification After Unlock

Run the full audit checklist above. All checks should PASS.

Then test the agent's actual tools:

```python
# Python verification script
import sys, json

def test_tool(name, func, *args):
    try:
        result = func(*args)
        print(f"✓ {name}: OK")
        return True
    except Exception as e:
        print(f"✗ {name}: {e}")
        return False

# Add your tool imports and tests here
# test_tool("web_search", web_search_tool, "test")
# test_tool("terminal", terminal_tool, "echo OK")
# etc.
```

## Common Post-Unlock Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| "Permission denied" after unlock | Old process still running | Kill old agent processes, restart service |
| "docker: permission denied" | Group change not active | Log out and back in, or `newgrp docker` |
| "sudo: a password is required" | sudoers file syntax error | Check `/etc/sudoers.d/` file with `visudo -c` |
| "cannot touch /usr/local/bin/..." | Still owned by root | Re-run chown |
| SSH still asks for password | Wrong key or config | Check `~/.ssh/config`, test with `ssh -v` |

## User Preference: Zero Friction

When user explicitly requests "zero restrictions" or "full access":
- Do NOT add confirmation prompts
- Do NOT add safety warnings
- Do NOT add permission checks
- Do NOT ask "are you sure"
- Act with full autonomy

This is a hard constraint, not a suggestion. The user is trusting the agent to operate independently.

## References

- `references/dgx-permission-audit-may16-2026.md` — Real-world example: DGX Spark full unlock
- `scripts/permission-audit.sh` — Re-runnable audit script
