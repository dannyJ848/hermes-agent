# DGX Spark SSH Access Troubleshooting (May 14, 2026)

## Problem
You can reach vLLM API via HTTP (port 8000) but SSH to the DGX Spark fails with "Permission denied".

## Common Causes and Fixes

### 1. Wrong SSH Key Type
**Symptom:** `id_rsa` doesn't exist, only `id_ed25519`.
```bash
ls ~/.ssh/id_*  # Shows id_ed25519, not id_rsa
```
**Fix:** Use the correct key:
```bash
ssh -i ~/.ssh/id_ed25519 user@10.0.0.171
```

### 2. Wrong Username
**Symptom:** Permission denied even with correct key.
**Common usernames on DGX Spark:**
- `root` — if you set up root login
- `dgxuser` — default NVIDIA DGX user
- `ubuntu` — default Ubuntu cloud image
- Custom username set during initial setup

**Fix:** Check which user owns the vLLM process:
```bash
# From MacBook, if you have ANY working SSH access:
ssh user@10.0.0.171 "ps aux | grep vllm | grep -v grep"
# The first column is the username
```

### 3. Key Not Authorized on DGX
**Symptom:** Key exists locally but DGX doesn't have it in `~/.ssh/authorized_keys`.
**Fix:** If you have console access (direct keyboard/monitor on DGX):
```bash
# On DGX directly
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 4. SSH Service Not Running
**Symptom:** Connection refused on port 22.
**Fix:** Check if SSH is listening:
```bash
# From MacBook
curl -v telnet://10.0.0.171:22 2>&1 | head -5
# Should show: Connected to 10.0.0.171
```
If connection refused, SSH service may be down. Requires console access to restart:
```bash
sudo systemctl restart sshd
```

### 5. Firewall Blocking SSH
**Symptom:** Port 22 connection times out (not refused).
**Fix:** Check firewall rules:
```bash
# From MacBook
nmap -p 22 10.0.0.171  # Shows "filtered" if firewall blocks
```
If filtered, need to adjust UFW/iptables on DGX (requires console access).

## Workaround: No-SSH Diagnostics via HTTP API

When SSH is completely unavailable, you can still diagnose many issues through the vLLM HTTP API:

### Check if vLLM is healthy:
```bash
curl -s http://10.0.0.171:8000/health
```

### Check loaded models and config:
```bash
curl -s http://10.0.0.171:8000/v1/models | python3 -m json.tool
```

### Check if tool calling works:
```bash
curl -s http://10.0.0.171:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"merged-lora","messages":[{"role":"user","content":"test"}],"tools":[{"type":"function","function":{"name":"web_search","description":"search","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}}],"tool_choice":"auto","max_tokens":50}'
```

### Check GPU utilization (indirectly):
If vLLM responds to chat completions with reasonable latency, GPU is working.
If responses are extremely slow or timeout, GPU may be stuck or OOM.

## Recovery: Regaining SSH Access

If SSH is completely lost and you need shell access:

1. **Physical console access:** Connect keyboard + monitor to DGX Spark directly
2. **IPMI/BMC:** If DGX has BMC (Baseboard Management Controller), use IPMI over network
3. **Serial console:** Some DGX systems have serial console access via USB
4. **Reboot:** As last resort, power cycle the DGX (requires physical access)

## Prevention

After regaining SSH access, set up redundant access methods:
```bash
# On DGX — add multiple authorized keys
cat >> ~/.ssh/authorized_keys << 'EOF'
# MacBook key 1
ssh-ed25519 AAAAC3... dannygomez@macbook
# MacBook key 2 (backup)
ssh-ed25519 AAAAC3... dannygomez@macbook-backup
# Mobile/remote access key
ssh-ed25519 AAAAC3... dannygomez@remote
EOF

# Ensure SSH starts on boot
sudo systemctl enable sshd
sudo systemctl restart sshd

# Check SSH is listening on all interfaces
sudo ss -tlnp | grep :22
# Should show: 0.0.0.0:22 (LISTEN)
```

### 6. SSH Connection Closed Immediately After Restart

**Symptom:** After restarting DGX, SSH connects but immediately closes:
```
Connection closed by 10.0.0.125 port 22
```

**Root cause:** The `~/.ssh/authorized_keys` file may have been reset, or `PasswordAuthentication` is disabled and the key is no longer authorized.

**Diagnosis:**
```bash
# Check if SSH port is open
nc -zv 10.0.0.125 22  # Should succeed

# Try verbose connection
ssh -vvv djg6228@10.0.0.125 'echo test' 2>&1 | tail -20
# Look for: "Authentications that can continue: publickey,password,keyboard-interactive"
# Then: "Connection closed" before password prompt
```

**Fix requires console access** (keyboard/monitor on DGX):
```bash
# On DGX directly — check authorized_keys
ls -la ~/.ssh/authorized_keys
cat ~/.ssh/authorized_keys | wc -l  # Should be > 0

# If empty or missing, re-add key
cat >> ~/.ssh/authorized_keys << 'EOF'
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAID... dannygomez@MacBook-Air-9.local
EOF
chmod 600 ~/.ssh/authorized_keys

# Check SSH config
sudo grep -E "PasswordAuthentication|PubkeyAuthentication" /etc/ssh/sshd_config
# Ensure: PubkeyAuthentication yes

# Restart SSH
sudo systemctl restart sshd
```

**Prevention:** After any system update or restart, verify SSH access immediately:
```bash
ssh djg6228@10.0.0.125 'echo SSH_OK'
```

### 7. Host Key Verification Failure After IP Change

**Symptom:**
```
Host key verification failed.
Offending ECDSA key in /Users/dannygomez/.ssh/known_hosts:15
```

**Root cause:** DGX got a new IP or SSH host key changed. The old key in `known_hosts` conflicts.

**Fix:**
```bash
# Remove old key for this IP
ssh-keygen -R 10.0.0.125
ssh-keygen -R spark-85e8.local

# Accept new key on next connection
ssh -o StrictHostKeyChecking=accept-new djg6228@10.0.0.125 'echo SSH_OK'
```

**Note:** `StrictHostKeyChecking=accept-new` is safer than `no` — it accepts unknown keys but still rejects changed keys.

## Session-Specific Notes (May 14, 2026)

- DGX Spark IP: 10.0.0.171
- vLLM API: http://10.0.0.171:8000/v1 (working)
- SSH: Permission denied with ed25519 key
- Cannot verify cerebrum DB status due to SSH block
- Knowledge base (hindsight) also unreachable — may be same network issue or service down

## Session-Specific Notes (May 16, 2026)

- DGX Spark IP: 10.0.0.125 (changed from 10.0.0.171)
- Hostname: spark-85e8.local
- SSH broken after DGX restart — connection closed immediately after key auth attempt
- Old Hermes processes (PID 242054) were running alongside new fixed wrapper (PID 247019)
- Killed old processes, but SSH still broken — needs console access to fix authorized_keys
- Terminal backend: TERMINAL_ENV=ssh, TERMINAL_SSH_HOST=macbook, TERMINAL_SSH_USER=dannygomez
