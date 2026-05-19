---
name: hermes-vps-deploy
version: 1.0
created: 2026-04-10
description: Deploy Hermes Agent to a remote VPS (Hostinger/Hetzner/Contabo) with native install, config sync, systemd service, and Telegram gateway. Also sets up local inference on Mac.
trigger: "Deploy Hermes to VPS, server setup, Hostinger, remote gateway, cloud deployment"
---

# Hermes VPS Deployment

Deploy Hermes Agent to a remote Linux VPS with Telegram gateway running 24/7.

## Prerequisites
- VPS with Ubuntu 24.04 (tested on Hostinger KVM 2: 2vCPU, 8GB RAM, 100GB NVMe)
- SSH access (root)
- Local Hermes Agent already configured with Telegram bot token and LLM API keys

## Step 1: SSH Key Setup

```bash
# Generate key if needed
ls ~/.ssh/id_ed25519.pub || ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N '' -q

# Copy to server (use password once)
sshpass -p 'PASSWORD' ssh-copy-id -o StrictHostKeyChecking=no root@SERVER_IP

# Verify passwordless access
ssh root@SERVER_IP 'echo OK'
```

## Step 2: Install Hermes from Source

DO NOT try `pip install hermes-agent` — it's not on PyPI. Install from GitHub:

```bash
ssh root@SERVER_IP '
apt-get update -qq && apt-get install -y -qq python3 python3-pip python3-venv git sqlite3 curl build-essential
python3 -m venv /opt/hermes-venv
source /opt/hermes-venv/bin/activate
pip install --upgrade pip
cd /opt && git clone https://github.com/NousResearch/hermes-agent.git
cd /opt/hermes-agent && pip install -q -e ".[all]"
hermes --version
'
```

## Step 3: Sync Config (rsync in parts)

The cerebrum DB can be large (10MB+). Sync in two passes to avoid timeout:

```bash
# Pass 1: Everything except large files
rsync -avz \
  --exclude='sessions/' \
  --exclude='audio_cache/' \
  --exclude='__pycache__' \
  --exclude='cerebrum_memory.db*' \
  --exclude='*.gguf' \
  ~/.hermes/ root@SERVER_IP:/root/.hermes/

# Pass 2: The DB separately
rsync -avz --progress ~/.hermes/cerebrum_memory.db root@SERVER_IP:/root/.hermes/

# Pass 3: Subconscious modules
rsync -avz ~/subconscious/ root@SERVER_IP:/root/subconscious/
```

## Step 4: Fix Platform-Specific Paths

```bash
# Fix MCP server paths (Mac paths won't work on Linux)
ssh root@SERVER_IP "
BIOMCP_PATH=\$(which biomcp)
sed -i \"s|/Users/.*/bin/biomcp|\$BIOMCP_PATH|g\" /root/.hermes/config.yaml
"
```

## Step 5: Create Systemd Service

```bash
ssh root@SERVER_IP 'cat > /etc/systemd/system/hermes-gateway.service << EOF
[Unit]
Description=Hermes Agent Telegram Gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Environment=PATH=/opt/hermes-venv/bin:/usr/local/bin:/usr/bin:/bin
WorkingDirectory=/root
ExecStart=/opt/hermes-venv/bin/hermes gateway
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable hermes-gateway
systemctl start hermes-gateway
'
```

## Step 6: Stop Local Gateway (CRITICAL)

Both local and remote CANNOT poll Telegram simultaneously. Stop the local one:

```bash
# Find local gateway PID (NOT the CLI session)
ps aux | grep 'hermes.*gateway' | grep -v grep
# Kill ONLY the gateway process
kill <GATEWAY_PID>

# Then restart the server to pick up polling
ssh root@SERVER_IP 'systemctl restart hermes-gateway'
sleep 15
ssh root@SERVER_IP 'journalctl -u hermes-gateway --no-pager -n 20'
# Should show NO "polling conflict" errors
```

## Step 7: Verify

```bash
ssh root@SERVER_IP '
systemctl status hermes-gateway | head -10
free -h
echo "---"
journalctl -u hermes-gateway --no-pager 2>&1 | grep -c "polling conflict"
echo "conflicts (should be 0 after initial startup)"
'
```

## Local Inference Setup (Mac M2 Air)

### Install llama.cpp with Metal

```bash
cd ~ && git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp && mkdir build && cd build
cmake .. -DGGML_METAL=ON
cmake --build . --config Release -j$(sysctl -n hw.ncpu)
```

### Download Models

```bash
mkdir -p ~/llama.cpp/models && cd ~/llama.cpp/models
# Phi-3 Mini 3.8B Q4 (~2.2GB) — fast classifier
curl -L -o phi-3-mini-q4km.gguf "https://huggingface.co/bartowski/Phi-3-mini-4k-instruct-GGUF/resolve/main/Phi-3-mini-4k-instruct-Q4_K_M.gguf"
# Llama 3.1 8B Q4 (~4.6GB) — judge/reward model
curl -L -o llama-3.1-8b-q4km.gguf "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
```

### Create LaunchAgents (auto-start, auto-restart)

Phi-3 on port 8081:
```xml
<!-- ~/Library/LaunchAgents/com.llama.phi3.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.llama.phi3</string>
    <key>ProgramArguments</key><array>
        <string>/Users/USERNAME/llama.cpp/build/bin/llama-server</string>
        <string>-m</string><string>/Users/USERNAME/llama.cpp/models/phi-3-mini-q4km.gguf</string>
        <string>--port</string><string>8081</string>
        <string>--host</string><string>127.0.0.1</string>
        <string>-ngl</string><string>99</string>
        <string>-c</string><string>2048</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>StandardOutPath</key><string>/tmp/llama-phi3.log</string>
    <key>StandardErrorPath</key><string>/tmp/llama-phi3-err.log</string>
</dict>
</plist>
```

Llama 8B on port 8082 (same structure, change port to 8082, model to llama-3.1-8b-q4km.gguf, context to 4096, label to com.llama.8b).

```bash
launchctl load ~/Library/LaunchAgents/com.llama.phi3.plist
launchctl load ~/Library/LaunchAgents/com.llama.8b.plist
# Test:
curl -s http://127.0.0.1:8081/health  # {"status":"ok"}
curl -s http://127.0.0.1:8082/health  # {"status":"ok"}
```

## Gotchas

1. **pip install hermes-agent fails** — not on PyPI, must install from git clone
2. **rsync timeout on first try** — cerebrum DB is ~10MB, exclude it from first pass and sync separately
3. **Telegram polling conflict** — only ONE instance can poll. Kill local gateway before starting remote
4. **MCP paths hardcoded to Mac** — fix biomcp and any other absolute paths in config.yaml
5. **biomcp "serve" command** — newer versions may use different subcommand, check `biomcp --help`
6. **Permissions** — rsync from Mac may set wrong UID/GID on server files; chown if needed
7. **llama-cli times out** — use llama-server instead for inference; llama-cli hangs without PTY
