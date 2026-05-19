# DGX Hermes Systemd Service Setup (May 16, 2026)

## Problem

Hermes Agent needs to run as a persistent systemd service on DGX, but two issues prevent this:

1. **Module shadowing:** `hermes_cli/gateway.py` shadows the `gateway/` package directory
2. **Tool calling requires vLLM flags:** `--enable-auto-tool-choice` and `--tool-call-parser` must be set

## Solution: Wrapper Script + Systemd Service

### Step 1: Create Module Shadowing Fix Wrapper

```python
#!/usr/bin/env python3
# /data/SpecForge/hermes-agent/run_hermes_dgx_fixed.py
import sys
import os
import importlib.util

project_root = "/data/SpecForge/hermes-agent"

# Step 0: Add project root to path FIRST
sys.path.insert(0, project_root)

# Step 1: Pre-load gateway package
gateway_init = os.path.join(project_root, "gateway", "__init__.py")
if os.path.exists(gateway_init) and "gateway" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "gateway",
        gateway_init,
        submodule_search_locations=[os.path.join(project_root, "gateway")]
    )
    gateway_pkg = importlib.util.module_from_spec(spec)
    sys.modules["gateway"] = gateway_pkg
    spec.loader.exec_module(gateway_pkg)

# Step 2: Pre-load plugins package
plugins_init = os.path.join(project_root, "plugins", "__init__.py")
if os.path.exists(plugins_init) and "plugins" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "plugins",
        plugins_init,
        submodule_search_locations=[os.path.join(project_root, "plugins")]
    )
    plugins_pkg = importlib.util.module_from_spec(spec)
    sys.modules["plugins"] = plugins_pkg
    spec.loader.exec_module(plugins_pkg)

# Step 3: Import and run main
from run_agent import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 2: Create Systemd Service

```ini
# /etc/systemd/system/hermes-dgx.service
[Unit]
Description=Hermes Agent DGX (Qwen3.6-27B-Uncensored + Dynamic LoRA)
After=docker.service
Requires=docker.service
Wants=vllm-base-lora.service

[Service]
Type=simple
User=djg6228
WorkingDirectory=/data/SpecForge/hermes-agent
Environment=PYTHONPATH=/data/SpecForge/hermes-agent
Environment=HOME=/home/djg6228
Environment=VIRTUAL_ENV=/data/SpecForge/hermes-agent/venv
ExecStart=/data/SpecForge/hermes-agent/venv/bin/python /data/SpecForge/hermes-agent/run_hermes_dgx_fixed.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hermes-dgx

[Install]
WantedBy=multi-user.target
```

### Step 3: Install and Start

```bash
sudo cp /tmp/hermes-dgx.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hermes-dgx.service
sudo systemctl start hermes-dgx.service
```

### Step 4: Verify

```bash
sudo systemctl status hermes-dgx.service
sudo journalctl -u hermes-dgx.service -n 20 --no-pager
```

## Critical vLLM Flags for Hermes

The vLLM container MUST include:
```bash
--enable-auto-tool-choice \
--tool-call-parser hermes
```

Without these, Hermes fails with:
```
HTTP 400: "auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set
```

## SSH Timeout During vLLM Initialization

**Expected behavior:** DGX becomes unresponsive to SSH for 5-10 minutes during vLLM startup.

**Cause:** CUDA graph capture consumes all CPU/GPU resources.

**Mitigation:**
- Wait 10+ minutes after `docker run` before attempting SSH
- Use `docker logs` from another terminal to monitor progress
- The vLLM container will be responsive on port 8000 before SSH recovers

## Verification Commands

```bash
# Check vLLM is serving
curl -s http://localhost:8000/v1/models | head -c 50

# Check Hermes is running
ps aux | grep hermes | grep -v grep

# Check logs
sudo journalctl -u hermes-dgx.service -f
```
