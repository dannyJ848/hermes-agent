# Access Troubleshooting & Factory Recovery

## When You Cannot SSH Into the Spark

### Network Discovery

The Spark is headless. Find it on your network:

```bash
# Try mDNS hostname from the manual first
ping -c 1 spark-XXXX.local

# If unknown, sweep your subnet (MacBook)
for i in $(seq 1 254); do ping -c 1 -W 1 10.0.0.$i >/dev/null 2>&1 && echo "10.0.0.$i UP"; done
```

Pattern: ping sweep → mDNS `.local` hostname → DNS resolution.

### SSH Troubleshooting Ladder

When SSH fails, diagnose systematically:

**Step 1: Verify host is alive**
```bash
ping -c 1 <SPARK_IP>
```

**Step 2: Scan for available services**
```bash
for port in 22 80 443 8080 8443 8888 8000 8001; do
  (echo > /dev/tcp/<SPARK_IP>/$port) 2>/dev/null && echo "Port $port open" || echo "Port $port closed"
done
```

**Step 3: Try provided credentials**
```bash
sshpass -p 'PASSWORD' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null USER@<SPARK_IP> 'whoami'
```

**Step 4: Try common defaults if auth fails**
- Usernames: root, ubuntu, nvidia, admin, danny, djg6228
- Passwords: device serial, 6228, nvidia, empty, 8182579928

**Step 5: Check for PasswordAuthentication catch-22**
If you recently set a custom hostname, Spark may have disabled password auth:
- Symptom: `Permission denied (publickey,password)` on ALL usernames/passwords
- Root cause: `/etc/ssh/sshd_config` has `PasswordAuthentication no` after hostname setup
- This is a **catch-22**: you can't SSH in to fix it because SSH requires a password

**Fix requires physical access:**
1. Plug wired keyboard + monitor into Spark
2. Log in locally with your password
3. Run: `sudo nano /etc/ssh/sshd_config` → set `PasswordAuthentication yes`
4. Run: `sudo systemctl restart ssh`
5. Reboot Spark, then retry remote SSH

Forum reference: NVIDIA DGX Spark community — SSH lockout after custom hostname setup.

**Step 6: If ALL credentials fail and only port 22 is open**
You are locked out. Options:
1. Physical console access (keyboard + monitor) — log in locally and reset password with `sudo passwd <user>`
2. Factory recovery (below) — wipes SSD, restores OS to factory state

## Remote Administration Without TTY

When SSHing into the Spark from a MacBook, `sudo` may fail with:
```
sudo: a terminal is required to read the password; either use the -S option
```

**Fix:** Pipe the password to `sudo -S` over SSH:
```bash
sshpass -p 'PASSWORD' ssh user@SPARK_IP 'echo "PASSWORD" | sudo -S usermod -aG docker user'
```

This avoids the TTY requirement and lets you run privileged commands remotely.

## Preflight Script Gotchas

The `spark-preflight.sh` script is designed to run **from the MacBook**, not the Spark itself. If copied to and run on the Spark, it produces false failures:
- "SSH to Spark FAILED" — script tries to SSH to itself from localhost
- "nvidia-smi FAILED" / "Docker not installed" — PATH/group issues when run in non-interactive shell
- Line 80 unbound variable error — `set -u` flag interacting with script logic

**Fix:** Run preflight from the MacBook (or just verify manually with the commands below).

## Manual State Verification (Run These Instead)

When preflight gives false positives, verify the Spark state directly:
```bash
# OS and GPU
sshpass -p 'PASSWORD' ssh user@SPARK_IP 'cat /etc/os-release | head -5 && nvidia-smi | head -10'

# Docker and permissions
sshpass -p 'PASSWORD' ssh user@SPARK_IP 'docker --version && groups && docker run --rm hello-world'

# Disk space
sshpass -p 'PASSWORD' ssh user@SPARK_IP 'df -h /'
```

## Docker Group Fix (Remote)

If Docker commands fail with `permission denied while trying to connect to the docker API`, the user is not in the `docker` group:

```bash
# Check groups
sshpass -p 'PASSWORD' ssh user@SPARK_IP 'groups'

# Fix remotely (requires sudo -S trick above)
sshpass -p 'PASSWORD' ssh user@SPARK_IP 'echo "PASSWORD" | sudo -S usermod -aG docker user'

# Re-login for group change to take effect
sshpass -p 'PASSWORD' ssh user@SPARK_IP 'docker run --rm hello-world'
```

## SCP: Don't Copy Training Data

The `~/dgx-spark-prep/` directory may contain 300GB+ of `training-data/`. When copying scripts to the Spark:

```bash
# WRONG — copies 300GB+, will timeout
scp -r ~/dgx-spark-prep/ user@SPARK_IP:~/

# RIGHT — copy only scripts and configs
scp ~/dgx-spark-prep/*.sh ~/dgx-spark-prep/*.yaml user@SPARK_IP:~/dgx-spark-prep/
```

Training data should either be transferred separately (rsync over USB-C/WiFi) or downloaded directly on the Spark.

## Factory Recovery (Founders Edition Only)

When the OS is corrupted, passwords are lost, or the system won't boot:

**Requirements:**
- USB flash drive (16GB+)
- Keyboard and display connected directly to the Spark
- Download recovery media from developer.nvidia.com

**Process:**
1. **Download:** `dgx-spark-recovery-image-1.120.38.tar.gz` from `developer.nvidia.com`
2. **Create USB:** Extract archive, run `CreateUSBKey.sh` (Linux), `CreateUSBKey.cmd` (Windows), or `CreateUSBKeyMacOS.sh` (macOS). Erases the USB drive.
3. **Boot to UEFI:** Power on Spark, immediately hold `Esc` or `Del`. Use a WIRED keyboard plugged directly into Spark (Bluetooth may not work).
4. **Restore Defaults:** Save & Exit → Restore Defaults → Yes → Save Changes and Reset.
5. **Re-enter UEFI** (hold Esc/Del during reboot), go to Security → Enable Secure Boot → Restore Factory Keys → Save Changes and Reset.
6. **Re-enter UEFI a third time**, Save & Exit → Boot Override → select USB drive.
7. **Recovery:** Follow on-screen prompts. `[START RECOVERY]` completely erases the internal SSD and reflashes it.
8. **Post-recovery:** Spark restarts to factory state. Re-run network config, user creation, and `spark-day1.sh` from scratch.

**Quick Reference:**
| Step | Key/Action |
|------|------------|
| Enter UEFI | Hold `Esc` or `Del` during boot |
| Restore Defaults | Save & Exit → Restore Defaults → Yes |
| Secure Boot | Security → Enable → Restore Factory Keys |
| Boot Override | Save & Exit → Boot Override → Select USB |
| Recovery Start | `Enter` (or `Esc` to cancel) |

Source: https://docs.nvidia.com/dgx/dgx-spark/system-recovery.html
