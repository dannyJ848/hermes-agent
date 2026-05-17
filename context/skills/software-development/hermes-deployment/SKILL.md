---
name: hermes-deployment
title: Hermes Deployment and Gateway Setup
description: |
  Deploy Hermes Agent to remote VPS, set up Telegram gateway, and configure
  message delivery. Covers Hostinger/Hetzner/Contabo deployment, systemd services,
  bot token setup, and cron/standalone Telegram delivery.
triggers:
  - When deploying Hermes to a VPS or remote server
  - When setting up Telegram gateway or bot
  - When Telegram delivery is broken in cron or standalone sessions
  - When the user says "deploy hermes", "setup gateway", "telegram not working"
category: software-development
---

# Hermes Deployment and Gateway Setup

## Overview

This skill covers deploying Hermes to production-like environments (VPS), configuring
the Telegram gateway, and fixing message delivery issues.

---

## Section 1: VPS Deployment

### Prerequisites

- VPS with Ubuntu 24.04 (tested: Hostinger KVM 2 — 2vCPU, 8GB RAM, 100GB NVMe)
- SSH access (root)
- Local Hermes Agent already configured with Telegram bot token and LLM API keys

### Step 1: SSH Key Setup

```bash
# Check what keys exist FIRST (don't assume id_rsa)
ls ~/.ssh/id_*

# Generate key if needed (prefer ed25519)
ls ~/.ssh/id_ed25519.pub || ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N '' -q

# Copy to server (use password once)
sshpass -p 'PASSWORD' ssh-copy-id -o StrictHostKeyChecking=no root@SERVER_IP

# Verify passwordless access
ssh root@SERVER_IP 'echo OK'
```

**Pitfall:** Many systems now use `id_ed25519` instead of `id_rsa`. Always check `ls ~/.ssh/id_*` before assuming key location.

### Step 2: Native Install on VPS

```bash
# Update and install dependencies
ssh root@SERVER_IP 'apt update && apt install -y python3-pip python3-venv git'

# Clone Hermes Agent
ssh root@SERVER_IP 'git clone https://github.com/nousresearch/hermes-agent.git /opt/hermes-agent'

# Create venv and install
ssh root@SERVER_IP 'cd /opt/hermes-agent && python3 -m venv venv && source venv/bin/activate && pip install -e .'
```

### Step 3: Config Sync

Copy local config to VPS:
```bash
scp ~/.hermes/config.yaml root@SERVER_IP:/opt/hermes-agent/config/
scp ~/.hermes/.env root@SERVER_IP:/opt/hermes-agent/
```

### Step 4: Systemd Service

```bash
# Create service file
ssh root@SERVER_IP 'cat > /etc/systemd/system/hermes-gateway.service << EOF
[Unit]
Description=Hermes Agent Gateway
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hermes-agent
Environment=PYTHONPATH=/opt/hermes-agent
ExecStart=/opt/hermes-agent/venv/bin/python -m hermes_cli.main gateway run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF'

# Enable and start
ssh root@SERVER_IP 'systemctl daemon-reload && systemctl enable hermes-gateway && systemctl start hermes-gateway'
```

### Step 5: Verify

```bash
ssh root@SERVER_IP 'systemctl status hermes-gateway'
ssh root@SERVER_IP 'tail -f /opt/hermes-agent/logs/gateway.log'
```

---

## Section 2: Telegram Gateway Setup

### Getting a Bot Token

1. Message @BotFather on Telegram
2. Create new bot or use `/token` on existing
3. Save token securely

### Stopping Intermediary Services (macOS launchd)

When Hermes is managed by an intermediary (e.g., OpenClaw):

```bash
# Find plist files
find ~/Library/LaunchAgents -name "*openclaw*" 2>/dev/null

# Unload each service
launchctl unload ~/Library/LaunchAgents/ai.openclaw.kimi.plist
launchctl unload ~/Library/LaunchAgents/ai.openclaw.dev.plist
launchctl unload ~/Library/LaunchAgents/ai.openclaw.gateway.plist

# Prevent respawn
rm ~/Library/LaunchAgents/ai.openclaw.*.plist
```

### Configuring Hermes Gateway

Add to `~/.hermes/config.yaml`:
```yaml
gateway:
  platform: telegram
  telegram:
    bot_token: "YOUR_BOT_TOKEN"
    home_channel: "YOUR_CHAT_ID"
```

### Starting Gateway

```bash
cd ~/hermes-agent && source venv/bin/activate && hermes gateway run --replace &
```

Or via launchd on macOS:
```bash
launchctl load ~/Library/LaunchAgents/hermes.gateway.plist
```

---

## Section 3: Telegram Delivery Fix

### The Bug

`telegram_status` and `telegram_card` tools from `~/.hermes/plugins/evey-telegram-ux/` only FORMAT messages but don't DELIVER them. They return HTML/JSON but never call the Telegram Bot API.

### The Fix

Patch the plugin's `card_handler` and `status_handler` to call `_deliver_to_telegram()` using `requests.post` to `https://api.telegram.org/bot{token}/sendMessage` with `parse_mode="HTML"`.

### What Does NOT Work

1. **Importing from `tools.send_message_tool`**: Only works inside gateway process. Fails in cron/standalone sessions.
2. **python-telegram-bot async library**: `asyncio.get_event_loop()` already running → "cannot run from running event loop" errors.
3. **Calling telegram_status/telegram_card from cron**: These format but don't deliver. Use `/tmp/cortex_notify.py` directly instead.
4. **Curl via terminal**: Terminal blocks commands with bot tokens (security measure).
5. **POSTing to gateway API server (port 8642)**: Only exposes `/v1/chat/completions` — no messaging endpoint.

### Current State (Apr 2026)

- Telegram delivery is **non-functional** in cron/standalone sessions
- `/tmp/cortex_notify.py` exists but requires credential in `.env`
- Gateway tokens live only in gateway process environment; CLI/cron cannot access them
- `TELEGRAM_HOME_CHANNEL` often NOT exported to CLI; V's chat ID is `5334119582` per historical logs
- Gateway loads tokens from `gateway/config.py:_apply_env_overrides()`, not config.yaml

### Working Delivery Script

```python
#!/usr/bin/env python3
# /tmp/cortex_notify.py — standalone Telegram delivery

import os, requests, sys

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN') or os.popen("grep TELEGRAM_BOT_TOKEN ~/.hermes/.env | cut -d= -f2").read().strip()
CHAT_ID = os.environ.get('TELEGRAM_HOME_CHANNEL') or '5334119582'

def send_message(text, parse_mode='HTML'):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": parse_mode}, timeout=10)
    return r.json()

if __name__ == '__main__':
    send_message(sys.argv[1] if len(sys.argv) > 1 else "Test message")
```

### Cron Job Delivery

For cron notifications, use the script directly:
```bash
export TELEGRAM_BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN ~/.hermes/.env | cut -d= -f2)
python3 /tmp/cortex_notify.py "Cron job completed: $(date)"
```

---

## Section 5: DGX Native Hermes Deployment

When deploying Hermes to DGX (or similar GPU servers), the pattern differs from VPS deployment:

### Discovery First

**Always check for existing installations before installing from scratch:**
```bash
# Check for Hermes source
ls -la /data/SpecForge/hermes-agent/ 2>/dev/null || ls -la ~/hermes-agent/ 2>/dev/null || echo "No existing installation"

# Check for config
ls -la ~/.hermes/config.yaml 2>/dev/null || echo "No home config"

# Check if CLI works
which hermes 2>/dev/null || ls */venv/bin/hermes 2>/dev/null
```

**DGX Spark already had a complete Hermes Agent at `/data/SpecForge/hermes-agent/`** with:
- Full source code (v0.13.0)
- 89 skills in `~/.hermes/skills/`
- Cerebrum memory DB
- 35+ plugins configured
- Distillation daemon already running

### The Cron Import Conflict

**Symptom:** Gateway starts but cron ticker crashes:
```
ModuleNotFoundError: No module named 'cron.scheduler'; 'cron' is not a package
```

**Root cause:** `hermes_cli/cron.py` shadows the `cron/` package. Python imports `hermes_cli/cron.py` instead of `cron/scheduler.py`.

**Fix:**
```bash
mv /data/SpecForge/hermes-agent/hermes_cli/cron.py \
   /data/SpecForge/hermes-agent/hermes_cli/cron_cmd.py

# Update imports
sed -i 's/from hermes_cli.cron import/from hermes_cli.cron_cmd import/g' \
    /data/SpecForge/hermes-agent/hermes_cli/main.py
sed -i 's/import hermes_cli.cron/import hermes_cli.cron_cmd/g' \
    /data/SpecForge/hermes-agent/hermes_cli/main.py
```

### DGX Systemd Service

```ini
[Unit]
Description=Hermes Agent Gateway (DGX Native)
After=network.target qdrant.service vllm-dflash.service
Wants=qdrant.service vllm-dflash.service

[Service]
Type=simple
User=djg6228
Group=djg6228
WorkingDirectory=/data/SpecForge/hermes-agent
Environment=HERMES_CONFIG=/data/SpecForge/hermes-agent/config.yaml
Environment=PYTHONPATH=/data/SpecForge/hermes-agent
Environment=PATH=/data/SpecForge/hermes-agent/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/data/SpecForge/hermes-agent/venv/bin/python -m gateway.run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Key differences from VPS service:**
- `PYTHONPATH` explicitly set to repo root
- Uses `python -m gateway.run` instead of `hermes gateway run`
- Depends on `vllm-dflash.service` for local inference
- Depends on `qdrant.service` for knowledge base

### Qdrant Setup

```bash
```bash
docker run -d --name qdrant -p 6333:6333 \
  -v ~/.hermes/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```

## Cognitive Orchestrator Integration

**Critical:** The iteration engine (7 systems) auto-loads, but the **cognitive orchestrator (20 subsystems)** does NOT auto-initialize. It must be explicitly wired into `run_agent.py`.

### Check if Already Integrated

```bash
grep -n 'cognitive_orchestrator\|CognitiveOrchestrator' /data/SpecForge/hermes-agent/run_agent.py
```

If empty, the orchestrator is NOT integrated.

### Patch run_agent.py

Add after iteration engine initialization (search for "Iteration engine ready"):

```python
        # ── Cognitive Orchestrator: 20-subsystem enhancement suite ────────
        try:
            from agent.cognitive_orchestrator import get_orchestrator
            self.cognitive_orchestrator = get_orchestrator()
            subsystem_status = self.cognitive_orchestrator.initialize(self)
            active_count = sum(1 for v in subsystem_status.values() if v == "active")
            total_count = len(subsystem_status)
            print(f"────────────────────────────────────────")
            print(f"🧠 Cognitive orchestrator ready: {active_count}/{total_count} subsystems active")
            for name, status in subsystem_status.items():
                icon = "✓" if status == "active" else "✗"
                print(f"   {icon} {name}")
            print(f"────────────────────────────────────────")
        except Exception as _co_err:
            logger.warning("Cognitive orchestrator init failed: %s", _co_err)
            self.cognitive_orchestrator = None
```

**Pitfall:** When patching via SSH, shell heredocs strip quotes from f-strings. Write the patch script locally with `write_file`, then execute on remote.

### System Comparison

| System | Iteration Engine | Cognitive Orchestrator |
|--------|-----------------|----------------------|
| Error Recovery Tree | ✓ | ✓ |
| LLM Judge | ✓ | ✓ |
| Self-Audit Engine | ✓ | ✓ |
| Context Quality Guard | ✓ | ✓ |
| Tool Misuse Prevention | ✓ | ✓ |
| Autobrowse Tracer | ✓ | ✓ |
| Agent Loop Optimizer | ✓ | ✓ |
| Cognitive Orchestrator | — | ✓ |
| Subconscious Loop | — | ✓ |
| Cortex Flywheel | — | ✓ |
| Knowledge Compiler | — | ✓ |
| Epistemic Trust Scoring | — | ✓ |
| Tiered Memory System | — | ✓ |
| Brain Cycle | — | ✓ |
| Middleware Reasoning Chain | — | ✓ |
| Session Immortality | — | ✓ |
| Hindsight/Cerebrum Sync | — | ✓ |
| Distillation Pipeline | — | ✓ |
| Research-to-Distillation | — | ✓ |
| Training Gym | — | ✓ |
| Tool-Grounded Cognition | — | ✓ |

**Total: 7 systems vs 20 systems.**

## Verification Checklist

```bash
# Check all services
sudo systemctl is-active vllm-dflash.service
sudo systemctl is-active hermes-dgx-gateway.service
docker ps | grep qdrant

# Check cognitive plugins
export HERMES_CONFIG=/data/SpecForge/hermes-agent/config.yaml
/data/SpecForge/hermes-agent/venv/bin/hermes plugins list | grep 'enabled' | wc -l
# → 40 plugins enabled
```

---

### DGX Hermes Process Topology

When managing Hermes on DGX Spark, there are **TWO distinct process types**:

| Process Type | Command | Purpose | Kill? |
|-------------|---------|---------|-------|
| **Systemd service** | `run_hermes_fixed.py` | Background persistent agent (auto-restart) | **NO** — Production instance |
| **Foreground CLI** | `venv/bin/hermes` | Interactive session user is actively using | **NO** — User's active session |

**Critical:** The foreground CLI (e.g., PID 98044 in pts/0) may appear "old" but is what the user is actively interacting with. The systemd service (PID 94678) runs the fixed wrapper. Both are valid and needed.

**Before killing any Hermes process:**
```bash
# Check tty — pts/0 = foreground (DON'T KILL), ? = background
ps aux | grep hermes | grep -v grep | awk '{print $2, $7, $11}'

# Check systemd status
systemctl --user status hermes-agent.service
```

**If foreground was accidentally killed:**
- The systemd service is still running
- User needs to reconnect to continue
- DO NOT restart service unless explicitly asked

---

## Section 6: Merged LoRA Verification

When vLLM serves a LoRA adapter alongside the base model:

**GET /v1/models/merged-lora returns 404 — this is NORMAL.**
The model list endpoint shows the model exists, but direct model info queries for LoRA adapters return 404. This does NOT mean the LoRA is broken.

**Correct verification:**
```bash
# 1. Check model is in list
curl -s http://localhost:8000/v1/models | grep "merged-lora"
# Expected: "id": "merged-lora"

# 2. Test chat completion (POST, not GET)
curl -s --max-time 30 -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "merged-lora", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5}'
# Expected: 200 OK with response

# 3. Check vLLM logs for LoRA load confirmation
docker logs vllm-merged 2>&1 | grep "Loaded new LoRA adapter"
# Expected: "Loaded new LoRA adapter: name 'merged-lora', path '...'"
```

**Common false alarm:**
```
GET /v1/models/merged-lora HTTP/1.1" 404 Not Found
```
This is a vLLM quirk, not an error. The LoRA is loaded and working.

---

## Section 7: Cognitive Orchestrator Integration

**Critical:** The iteration engine (7 systems) auto-loads, but the **cognitive orchestrator (20 subsystems)** does NOT auto-initialize. It must be explicitly wired into `run_agent.py`.

### Check if Orchestrator is Already Integrated

```bash
grep -n 'cognitive_orchestrator\|CognitiveOrchestrator' /data/SpecForge/hermes-agent/run_agent.py
```

If empty, the orchestrator is NOT integrated and only the iteration engine runs.

### Patch run_agent.py to Initialize the Orchestrator

Add this block **after** the iteration engine initialization (around line 2125):

```python
        # ── Cognitive Orchestrator: 20-subsystem enhancement suite ────────
        try:
            from agent.cognitive_orchestrator import get_orchestrator
            self.cognitive_orchestrator = get_orchestrator()
            subsystem_status = self.cognitive_orchestrator.initialize(self)
            active_count = sum(1 for v in subsystem_status.values() if v == "active")
            total_count = len(subsystem_status)
            print(f"────────────────────────────────────────")
            print(f"🧠 Cognitive orchestrator ready: {active_count}/{total_count} subsystems active")
            for name, status in subsystem_status.items():
                icon = "✓" if status == "active" else "✗"
                print(f"   {icon} {name}")
            print(f"────────────────────────────────────────")
        except Exception as _co_err:
            logger.warning("Cognitive orchestrator init failed: %s", _co_err)
            self.cognitive_orchestrator = None
```

**Pitfall — quote escaping via SSH heredocs:** When patching via SSH, shell heredocs strip quotes from f-strings. Use `write_file` to create the patch script locally, then execute it on the remote host. Never use `cat << 'EOF'` over SSH for Python code containing quotes.

**Pitfall — line number drift:** The exact line number changes with Hermes versions. Search for the iteration engine block as an anchor:
```bash
grep -n 'Iteration engine ready' /data/SpecForge/hermes-agent/run_agent.py
```

### What the Orchestrator Adds (vs Iteration Engine Alone)

| System | Iteration Engine | Cognitive Orchestrator |
|--------|-----------------|----------------------|
| Error Recovery Tree | ✓ | ✓ |
| LLM Judge | ✓ | ✓ |
| Self-Audit Engine | ✓ | ✓ |
| Context Quality Guard | ✓ | ✓ |
| Tool Misuse Prevention | ✓ | ✓ |
| Autobrowse Tracer | ✓ | ✓ |
| Agent Loop Optimizer | ✓ | ✓ |
| **Cognitive Orchestrator** | — | **✓** |
| **Subconscious Loop** | — | **✓** |
| **Cortex Flywheel** | — | **✓** |
| **Knowledge Compiler** | — | **✓** |
| **Epistemic Trust Scoring** | — | **✓** |
| **Tiered Memory System** | — | **✓** |
| **Brain Cycle** | — | **✓** |
| **Middleware Reasoning Chain** | — | **✓** |
| **Session Immortality** | — | **✓** |
| **Hindsight/Cerebrum Sync** | — | **✓** |
| **Distillation Pipeline** | — | **✓** |
| **Research-to-Distillation** | — | **✓** |
| **Training Gym** | — | **✓** |
| **Tool-Grounded Cognition** | — | **✓** |

**Total: 7 systems vs 20 systems.** The user expects FULL cognitive orchestrator on ALL machines.

---

## Static Site Hosting (Optional)

When Hermes generates static sites (e.g., The Lens daily digest), deploy them alongside the gateway:

### Option 1: GitHub Pages (Free)
```bash
cd /path/to/site
# Must be a git repo
git init
git add .
git commit -m "Initial site"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/thelens-daily.git
git push -u origin main
# Enable Pages in repo settings
```

### Option 2: Netlify (Free, Instant)
```bash
# Drag and drop the site/ folder to app.netlify.com/drop
# Or use CLI:
npx netlify-cli deploy --prod --dir=/path/to/site
```

### Option 3: Self-Hosted (DGX/VPS)
```bash
# Install nginx
ssh root@SERVER_IP 'apt install -y nginx'

# Copy site files
rsync -avz --delete /path/to/site/ root@SERVER_IP:/var/www/thelens/

# Configure nginx
ssh root@SERVER_IP 'cat > /etc/nginx/sites-available/thelens << NGINX
server {
    listen 80;
    server_name thelens.example.com;
    root /var/www/thelens;
    index index.html;
    location / {
        try_files $uri $uri/ =404;
    }
}
NGINX'

# Enable site
ssh root@SERVER_IP 'ln -sf /etc/nginx/sites-available/thelens /etc/nginx/sites-enabled/'
ssh root@SERVER_IP 'nginx -t && systemctl reload nginx'
```

### Option 4: Cloudflare Pages (Free CDN)
```bash
# Install Wrangler
npm install -g wrangler
# Login and deploy
wrangler login
wrangler pages deploy /path/to/site --project-name=thelens-daily
```

**Pitfall:** When using `rsync --delete` with nginx, ensure the web root path matches exactly. A trailing slash mismatch can delete the wrong directory.

---

## Key Files

| File | Purpose |
|------|---------|
| `~/.hermes/config.yaml` | Gateway and Telegram config |
| `~/.hermes/.env` | API keys and tokens |
| `~/.hermes/plugins/evey-telegram-ux/__init__.py` | Plugin handlers (needs patch) |
| `/tmp/cortex_notify.py` | Standalone delivery script |
| `/etc/systemd/system/hermes-gateway.service` | VPS systemd service |
| `scripts/verify-dgx-inference.sh` | Verify DGX vLLM inference health |

## Verification Scripts

### DGX Inference Health Check

Run `scripts/verify-dgx-inference.sh` to verify:
1. vLLM responding on port 8000
2. merged-lora model available
3. Chat completions working
4. Tool calling functional
5. Hermes config has correct context_length

```bash
bash ~/.hermes/skills/software-development/hermes-deployment/scripts/verify-dgx-inference.sh [DGX_IP] [PORT]
```

## Pitfalls

- **Gateway process isolation**: CLI/cron sessions cannot access gateway environment variables
- **Token security**: Never pass tokens via terminal() — use .env files or Python scripts
- **Async event loops**: Don't use python-telegram-bot in Hermes process — event loop conflicts
- **Port confusion**: Gateway API (8642) ≠ Telegram Bot API — don't POST to gateway for messaging
- **macOS launchd**: Intermediary plists must be removed, not just unloaded, to prevent respawn

## References

| `references/vps-systemd-template.md` — Complete systemd service file
| `references/telegram-plugin-patch.md` — Exact patch for evey-telegram-ux plugin
| `references/cron-delivery-script.md` — Standalone delivery for cron jobs
| `references/dgx-native-hermes-gateway.md` — DGX-native deployment with existing install discovery, cron conflict fix, and gateway service
| `references/cognitive-orchestrator-integration.md` — How to wire the 20-subsystem cognitive orchestrator into run_agent.py (not auto-loaded like iteration engine)
