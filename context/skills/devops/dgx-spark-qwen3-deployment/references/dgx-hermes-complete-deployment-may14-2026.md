# DGX Hermes Complete Deployment — May 14, 2026

## Overview

Full deployment of Hermes Agent to DGX Spark with complete tool parity (97 tools), iteration pipeline fix, and source code verification.

## Deployment Steps

### 1. Source Code Sync

```bash
# MacBook → DGX one-shot rsync
rsync -avz --exclude='.git' --exclude='node_modules' --exclude='__pycache__' \
  --exclude='*.pyc' --exclude='.pytest_cache' --exclude='venv' --exclude='.venv' \
  --exclude='datasets' --exclude='temp_vision_images' \
  ~/hermes-agent/ djg6228@spark-85e8.local:/data/SpecForge/hermes-agent/
```

### 2. Plugin Configuration

**CRITICAL**: Hermes reads config from `~/.hermes/config.yaml`, NOT the repo directory.

```yaml
# /home/djg6228/.hermes/config.yaml
plugins:
  enabled:
    - learning-brain
    - adaptive-cortex
    - distillation-bridge
    # ... 35 total plugins
  disabled: []
```

**Pitfall**: Using list format (`- learning-brain`) instead of dict format causes plugin load errors. Use dict format with `enabled:` and `disabled:` keys.

### 3. API Credential Sync

Sync `.env` from MacBook → DGX:
- Brave API Key (web search)
- Firecrawl API Key (web extraction)
- Browserbase credentials (browser automation)

### 4. Node.js Installation (ARM64)

```bash
cd /tmp
curl -fsSL https://nodejs.org/dist/v20.12.2/node-v20.12.2-linux-arm64.tar.xz -o node.tar.xz
tar -xf node.tar.xz
mv node-v20.12.2-linux-arm64 ~/node
export PATH=$HOME/node/bin:$PATH
npm install -g agent-browser
```

**Pitfall**: x86_64 binary fails with "cannot execute binary file" on aarch64. Always use `-linux-arm64`.

### 5. Tool Count Verification

```bash
cd /data/SpecForge/hermes-agent
venv/bin/python -c "from model_tools import get_tool_definitions; print(len(get_tool_definitions(quiet_mode=True)))"
# Expected: 97 (was 21 before plugin config fix)
```

### 6. Iteration Pipeline Fix

**Problem**: Distillation daemon stuck — 238/247 experiences had empty lessons.

**Root cause**: Learning system only extracted lessons from failures. 97% of experiences were successes.

**Fix**: Rewrite daemon to:
1. Extract lessons from BOTH successes and failures
2. Backfill all existing experiences on startup
3. Lower frequency threshold from 3 to 2

**Result**: 247 experiences with lessons → 59 distilled tips (was 7).

### 7. Systemd Services

```ini
# /etc/systemd/system/hermes-dgx.service
[Unit]
Description=DGX Hermes Chat Agent
After=network.target

[Service]
Type=simple
User=djg6228
WorkingDirectory=/data/SpecForge/hermes-agent
Environment=PATH=/home/djg6228/node/bin:/data/SpecForge/hermes-agent/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/data/SpecForge/hermes-agent
EnvironmentFile=/home/djg6228/.hermes/.env
ExecStart=/data/SpecForge/hermes-agent/venv/bin/python -m hermes_cli chat
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/dgx-learning.service
[Unit]
Description=DGX Hermes Learning Daemon
After=network.target

[Service]
Type=simple
User=djg6228
WorkingDirectory=/data/SpecForge/hermes-agent
Environment=PATH=/home/djg6228/node/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/data/SpecForge/hermes-agent
ExecStart=/usr/bin/python3 /data/SpecForge/hermes-agent/scripts/dgx_distillation_daemon.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

## File Sync Verification

After deployment, verify all files are present:

```bash
# On DGX
cd /data/SpecForge/hermes-agent
echo "Core CLI: $(ls hermes_cli/*.py | wc -l)"
echo "Agent: $(ls agent/*.py | wc -l)"
echo "Tools: $(ls tools/*.py | wc -l)"
echo "Gateway: $(ls gateway/*.py | wc -l)"
echo "Plugins: $(find plugins -name '*.py' | wc -l)"
```

Expected: ~82 CLI, ~178 agent, ~85 tools, ~18 gateway, ~95 plugins.

## Key Paths

- **Hermes source**: `/data/SpecForge/hermes-agent/`
- **Active config**: `/home/djg6228/.hermes/config.yaml`
- **Environment**: `/home/djg6228/.hermes/.env`
- **Memory DB**: `~/.hermes/cerebrum_memory.db`
- **Skills**: `~/.hermes/skills/`
- **Knowledge**: `~/.hermes/knowledge/`
- **Node.js**: `~/node/bin/`
- **Training data**: `/data/SpecForge/custom_dflash/datasets/`
- **Checkpoints**: `/data/SpecForge/custom_dflash/checkpoints/`

## Usage

```bash
# Interactive
ssh djg6228@10.0.0.171
cd /data/SpecForge/hermes-agent
export PATH=/home/djg6228/node/bin:$PATH
venv/bin/hermes chat

# Or via alias
alias hermes-dgx='cd /data/SpecForge/hermes-agent && export PATH=/home/djg6228/node/bin:$PATH && venv/bin/hermes'
```
