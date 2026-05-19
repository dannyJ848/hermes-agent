---
name: dgx-infrastructure-topology
description: DGX Spark and MacBook network topology, access methods, and IP mapping
triggers:
  - "connect to DGX"
  - "SSH to DGX"
  - "DGX IP"
  - "spark-85e8"
  - "MacBook IP"
  - "terminal bridge"
  - "DGX access"
  - "infrastructure topology"
---

# DGX ↔ MacBook Infrastructure Topology

## Systems

| System | Hostname | Role | Access Direction |
|--------|----------|------|-----------------|
| DGX Spark | spark-85e8.local | GPU server (8x A100) | MacBook → DGX |
| MacBook Air | MacBook-Air-9.local | Client/workstation | DGX → MacBook |

## Critical Rule

**NEVER guess IPs. Always use hostnames.** The IPs can change after restarts. The hostnames are stable.

## Access Methods

### MacBook → DGX
- Uses NVIDIA Sync SSH config at `~/.ssh/config`
- Key: `/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key`
- Command: `ssh djg6228@spark-85e8.local`
- **DO NOT** use `~/.ssh/id_ed25519` for this direction

### DGX → MacBook
- Uses standard SSH key
- Key: `~/.ssh/id_ed25519` (on DGX)
- Target: `dannygomez@MacBook-Air-9.local` or `dannygomez@10.0.0.125`
- Configured in DGX `~/.ssh/config` as `Host macbook`

## Common Failures

1. **"Connection closed" after DGX restart**: Host key changed. Run:
   ```bash
   ssh-keygen -R spark-85e8.local
   ssh -o StrictHostKeyChecking=accept-new djg6228@spark-85e8.local
   ```

2. **"Permission denied"**: Using wrong key. Check `~/.ssh/config` includes NVIDIA Sync config.

3. **Mixing up IPs**: If you find yourself typing `10.0.0.x`, stop. Use the hostname.

## DGX Hermes Process Topology (May 16 2026)

Two distinct Hermes process types run on DGX. **Killing the wrong one disconnects the user.**

| Process Type | Command | TTY | Purpose | Safe to Kill? |
|-------------|---------|-----|---------|--------------|
| **Background service** | `run_hermes_fixed.py` | `?` (no TTY) | Auto-restart systemd service | Yes |
| **Foreground CLI** | `venv/bin/hermes` | `pts/0` | User's active SSH session | **NO** |

**How to distinguish:**
```bash
# Check TTY column — pts/0 = foreground (DON'T KILL), ? = background
ps aux | grep -E "hermes|run_hermes" | grep -v grep
```

**Example output:**
```
djg6228   94678  0.3  0.1  ...  ?        Ssl  17:23   0:12 python3 /data/SpecForge/hermes-agent/run_hermes_fixed.py
djg6228   98044  0.1  0.0  ...  pts/0    S+   17:30   0:05 /data/SpecForge/hermes-agent/venv/bin/hermes
```
- PID 94678 (`?`) = background service — safe to kill/restart
- PID 98044 (`pts/0`) = foreground CLI — **killing this disconnects the user**

**Duplicate instance cleanup:**
When both service and foreground instances exist with separate gateways, kill only the old foreground:
```bash
# Kill ONLY the foreground instance (has pts/0 TTY)
for pid in $(ps aux | grep "venv/bin/hermes" | grep "pts/" | grep -v grep | awk '{print $2}'); do
    kill -9 $pid
done

# Verify only service remains
ps aux | grep -E "hermes|run_hermes" | grep -v grep
```

**Gateway PID check:**
The foreground instance may spawn its own gateway (PID ~98066). After killing the foreground, verify no duplicate gateway:
```bash
ps aux | grep "gateway" | grep -v grep
# Should show only ONE gateway process (from the service)
```

## Terminal Routing Awareness

When the DGX Hermes systemd service sets `TERMINAL_ENV=ssh` and `TERMINAL_SSH_HOST=macbook`, the `terminal_tool` executes commands on the MacBook, NOT on the DGX. **The agent's Python process runs on DGX; the shell commands run on MacBook.** This creates a split-brain situation where:

- `hostname` returns `MacBook-Air-9.local`
- `whoami` returns `dannygomez`
- File paths like `~/` resolve to `/Users/dannygomez/`
- But the agent's own code, skills, and config files live on DGX at `/data/SpecForge/hermes-agent/`

**Pitfall:** The agent may incorrectly assume it's running locally on the machine where commands execute. Always verify which machine you're operating on by checking `hostname` AND `echo $SSH_CLIENT` (empty = local, set = SSH). When editing config files, know whether the target file lives on DGX (`/data/SpecForge/hermes-agent/`) or MacBook (`/Users/dannygomez/.hermes/`).

## DGX Hermes Permission Audit Results

| Permission | Status | Details |
|------------|--------|---------|
| SSH to MacBook | GRANTED | Uses `~/.ssh/id_ed25519`, config in `~/.ssh/config` |
| Sudo on DGX | PASSWORDLESS | `sudo -n whoami` returns `root` |
| Docker | GRANTED | User in `docker` group, can manage containers |
| File Access | FULL | Owns `/data/SpecForge/hermes-agent`, `~/.hermes`, `~/.ssh` |
| Systemd | FULL | Can manage user services |
| Terminal (SSH) | FULL | Can execute any command on MacBook via `terminal_tool` |
| Terminal (Local) | FULL | Can execute any command on DGX |

## Environment Variables (in systemd service)

```
TERMINAL_ENV=ssh
TERMINAL_SSH_HOST=macbook
TERMINAL_SSH_USER=dannygomez
HERMES_HOME=/home/djg6228/.hermes
PYTHONPATH=/data/SpecForge/hermes-agent
```

## Verified Operations

The DGX Hermes can successfully:
- Execute commands on MacBook as `dannygomez`
- Read/write files on MacBook (`/tmp/`, `~/`)
- Check processes on MacBook
- Run network commands from MacBook
- Use sudo without password on DGX
- Manage Docker containers on DGX
- Manage systemd user services on DGX

## Service Configuration

File: `~/.config/systemd/user/hermes-agent.service`

```ini
[Unit]
Description=Hermes Agent DGX (Fixed)
After=network.target

[Service]
Type=simple
Environment="PYTHONPATH=/data/SpecForge/hermes-agent"
Environment="TERMINAL_ENV=ssh"
Environment="TERMINAL_SSH_HOST=macbook"
Environment="TERMINAL_SSH_USER=dannygomez"
Environment="HERMES_HOME=/home/djg6228/.hermes"
WorkingDirectory=/data/SpecForge/hermes-agent
ExecStart=/data/SpecForge/hermes-agent/venv/bin/python3 /data/SpecForge/hermes-agent/run_hermes_fixed.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

## User Preference: No Restrictions

The user explicitly wants **zero friction** for the DGX Hermes. Do NOT add permission checks, confirmation prompts, or safety warnings when operating on DGX. The model should have unrestricted access to:
- All system directories (`/usr/local/bin`, `/opt`, `/var/log`, etc.)
- Passwordless sudo for ALL commands
- Docker without restrictions
- File read/write anywhere
- Service management without confirmation

## DGX Spark Remote Access Lost After Restart (May 16 2026)

**Symptom:** After restarting DGX, cannot connect via network shell. DGX responds to ping but closes connection immediately during SSH authentication.

**Root cause:** `~/.ssh/authorized_keys` file was reset during restart, removing the MacBook's public key.

**Fix:** Requires physical console access (keyboard/monitor connected to DGX):
1. Log in locally at the DGX console
2. Re-add the SSH public key to `~/.ssh/authorized_keys`:
   ```bash
   echo "ssh-ed25519 AAAAC3NzaC... dannygomez@MacBook-Air-9.local" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```
3. Verify from MacBook: `ssh djg6228@spark-85e8.local`

**Prevention:** Backup authorized_keys to a persistent location:
```bash
# On DGX
cp ~/.ssh/authorized_keys /data/backup/authorized_keys.backup
# Add to crontab to auto-restore on boot
```

**DGX IP:** 10.0.0.125 (static, but use hostname `spark-85e8.local` when possible)

## Session-Specific References

- `references/may16-2026-permission-audit.md` — Full permission audit results, fixes applied, and verification checklist from the May 16 2026 session where unrestricted access was enabled.
- `scripts/permission-audit.sh` — Re-runnable script to verify all permissions are still intact.

```bash
# From MacBook — verify DGX access
ssh djg6228@spark-85e8.local 'echo DGX_OK'

# From DGX — verify MacBook access  
ssh macbook 'echo MACBOOK_OK'

# Run full permission audit
bash ~/.hermes/skills/devops/dgx-infrastructure-topology/scripts/permission-audit.sh
```