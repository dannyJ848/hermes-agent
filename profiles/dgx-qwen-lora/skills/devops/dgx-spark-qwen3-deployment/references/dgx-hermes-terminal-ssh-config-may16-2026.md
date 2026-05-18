# DGX Hermes Terminal SSH Configuration (May 16, 2026)

## Overview

Configure DGX Hermes to execute terminal commands on MacBook via SSH, enabling the DGX agent to access macOS-specific tools and resources.

## Prerequisites

- DGX Hermes running with working terminal tool
- MacBook accessible from DGX via SSH
- SSH key authentication configured

## Step-by-Step Setup

### 1. Generate SSH Key on DGX

```bash
ssh-keygen -t ed25519 -C 'dgx-to-macbook' -f ~/.ssh/id_ed25519
# No passphrase (for unattended operation)
```

### 2. Add Public Key to MacBook

```bash
# On MacBook
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Enable Remote Login if needed
sudo systemsetup -setremotelogin on
```

### 3. Discover MacBook IP

```bash
# On MacBook
ifconfig | grep "inet " | head -1
# Example: 10.0.0.125

# Or use hostname
hostname -I
```

### 4. Create SSH Config on DGX

```bash
# ~/.ssh/config
Host macbook
    HostName 10.0.0.125
    User dannygomez
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new
```

### 5. Test SSH Connection

```bash
# From DGX
ssh djg6228@spark-85e8.local "ssh macbook 'whoami; hostname'"
# Expected: dannygomez / MacBook-Air-9.local
```

### 6. Configure Hermes Terminal Backend

```yaml
# ~/.hermes/config.yaml
terminal:
  backend: ssh
  ssh:
    host: macbook
    user: dannygomez
    key_file: /home/djg6228/.ssh/id_ed25519
```

### 7. Set Environment Variables

```bash
# ~/.hermes/.env
TERMINAL_ENV=ssh
TERMINAL_SSH_HOST=macbook
TERMINAL_SSH_USER=dannygomez
```

### 8. Update Systemd Service

```ini
# ~/.config/systemd/user/hermes-agent.service
[Unit]
Description=Hermes Agent DGX (Fixed)
After=network.target

[Service]
Type=simple
WorkingDirectory=/data/SpecForge/hermes-agent
Environment=PYTHONPATH=/data/SpecForge/hermes-agent
Environment=HERMES_HOME=/home/djg6228/.hermes
Environment=TERMINAL_ENV=ssh
Environment=TERMINAL_SSH_HOST=macbook
Environment=TERMINAL_SSH_USER=dannygomez
ExecStart=/data/SpecForge/hermes-agent/venv/bin/python3 /data/SpecForge/hermes-agent/run_hermes_fixed.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

### 9. Verify Terminal Works

```python
import sys
sys.path.insert(0, "/data/SpecForge/hermes-agent")
from tools.terminal_tool import terminal_tool
import json

# Test local (DGX)
result = terminal_tool("whoami; hostname")
data = json.loads(result)  # Returns JSON string, not dict
print("Local:", data["output"])
# Expected: djg6228\nspark-85e8

# Test SSH (MacBook)
import os
os.environ['TERMINAL_ENV'] = 'ssh'
result = terminal_tool("whoami; hostname")
data = json.loads(result)
print("SSH:", data["output"])
# Expected: dannygomez\nMacBook-Air-9.local
```

**Important:** `terminal_tool()` returns a JSON string, not a Python dict. Always parse with `json.loads()`:
```python
import json
result = terminal_tool("echo test")
data = json.loads(result)
print(data["output"])   # "test\n"
print(data["exit_code"])  # 0
print(data["error"])   # null
```

## Troubleshooting

**SSH permission denied:**
- Verify key exists: `ls ~/.ssh/id_ed25519`
- Test manual SSH: `ssh macbook 'echo test'`
- Check authorized_keys on MacBook: `cat ~/.ssh/authorized_keys | grep dgx`
- Verify Remote Login is enabled: `sudo systemsetup -getremotelogin`

**Terminal tool returns local output when SSH configured:**
- Check environment: `env | grep TERMINAL`
- Verify config.yaml has terminal section
- Restart Hermes: `systemctl --user restart hermes-agent`

**SSH host not found:**
- Verify SSH config: `cat ~/.ssh/config`
- Test with IP directly: `ssh dannygomez@10.0.0.125 'echo test'`
- Check DNS resolution: `ping macbook`

## Key Files

- `~/.ssh/id_ed25519` — DGX private key
- `~/.ssh/config` — SSH client configuration
- `~/.hermes/config.yaml` — Hermes configuration
- `~/.hermes/.env` — Environment variables
- `~/.config/systemd/user/hermes-agent.service` — Systemd service

## Related

- `references/gateway-module-shadowing-may16-2026.md` — Module shadowing fix
- `references/dgx-hermes-complete-deployment-may14-2026.md` — Full deployment guide
