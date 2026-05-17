# DGX Hermes Daemon Service Setup - May 16 2026

## Problem

Running Hermes Agent interactively under systemd fails because stdin is not a TTY. The agent starts, gets EOF immediately, and exits. This creates a restart loop.

## Solution: Queue-Based Daemon

Instead of interactive mode, run Hermes as a daemon that:
1. Reads requests from a JSONL queue file (`/tmp/hermes_dgx_requests.jsonl`)
2. Processes them asynchronously
3. Writes responses to a response directory (`/tmp/hermes_dgx_responses/`)

## Daemon Script

File: `/data/SpecForge/hermes-agent/run_hermes_daemon.py`

```python
#!/usr/bin/env python3
import sys
import os
import importlib.util
import asyncio
import json
from datetime import datetime

project_root = "/data/SpecForge/hermes-agent"
sys.path.insert(0, project_root)

# Pre-load gateway and plugins packages to prevent module shadowing
gateway_init = os.path.join(project_root, "gateway", "__init__.py")
if os.path.exists(gateway_init) and "gateway" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "gateway", gateway_init,
        submodule_search_locations=[os.path.join(project_root, "gateway")]
    )
    gateway_pkg = importlib.util.module_from_spec(spec)
    sys.modules["gateway"] = gateway_pkg
    spec.loader.exec_module(gateway_pkg)

plugins_init = os.path.join(project_root, "plugins", "__init__.py")
if os.path.exists(plugins_init) and "plugins" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "plugins", plugins_init,
        submodule_search_locations=[os.path.join(project_root, "plugins")]
    )
    plugins_pkg = importlib.util.module_from_spec(spec)
    sys.modules["plugins"] = plugins_pkg
    spec.loader.exec_module(plugins_pkg)

from run_agent import main

async def daemon_loop():
    request_queue = "/tmp/hermes_dgx_requests.jsonl"
    response_dir = "/tmp/hermes_dgx_responses"
    os.makedirs(response_dir, exist_ok=True)
    
    while True:
        try:
            if os.path.exists(request_queue):
                with open(request_queue, 'r') as f:
                    lines = f.readlines()
                
                if lines:
                    request = json.loads(lines[0])
                    request_id = request.get('id', 'unknown')
                    query = request.get('query', '')
                    
                    # main() is already async - just await it directly
                    # DO NOT wrap in asyncio.run() - that causes TypeError
                    await main(
                        query=query,
                        model="/data/models/Qwen3.6-27B-Uncensored",
                        api_key="not-needed",
                        base_url="http://localhost:8000/v1",
                        max_turns=10,
                        verbose=True
                    )
                    
                    response_file = os.path.join(response_dir, f"{request_id}.json")
                    with open(response_file, 'w') as f:
                        json.dump({'id': request_id, 'status': 'completed'}, f)
                    
                    with open(request_queue, 'w') as f:
                        f.writelines(lines[1:])
            
            await asyncio.sleep(5)
        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(daemon_loop())
```

## Systemd Service

File: `/etc/systemd/system/hermes-dgx-daemon.service`

```ini
[Unit]
Description=Hermes Agent DGX Daemon (Qwen3.6-27B-Uncensored + Dynamic LoRA)
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
ExecStart=/data/SpecForge/hermes-agent/venv/bin/python /data/SpecForge/hermes-agent/run_hermes_daemon.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hermes-dgx-daemon

[Install]
WantedBy=multi-user.target
```

## Commands

```bash
# Deploy service
sudo systemctl daemon-reload
sudo systemctl enable hermes-dgx-daemon.service
sudo systemctl start hermes-dgx-daemon.service

# Check status
sudo systemctl status hermes-dgx-daemon.service
sudo journalctl -u hermes-dgx-daemon.service -f

# Submit request
echo '{"id": "req-001", "query": "What is 2+2?"}' >> /tmp/hermes_dgx_requests.jsonl

# Check response
cat /tmp/hermes_dgx_responses/req-001.json
```

## Key Findings

1. **Model name must be full path**: vLLM expects `/data/models/Qwen3.6-27B-Uncensored`, not just `Qwen3.6-27B-Uncensored`
2. **Module shadowing fix required**: Pre-import gateway and plugins via importlib.util
3. **Restart=always**: Essential for daemon resilience
4. **Wants=vllm-base-lora.service**: Ensures vLLM starts before Hermes
5. **Use `await main(...)` not `asyncio.run()`**: `main()` is already async; wrapping it in `asyncio.run()` inside an async function causes `TypeError: object NoneType can't be used in 'await' expression`
6. **Use `asyncio.sleep()` not `time.sleep()`**: In async daemon loop, always use `await asyncio.sleep()`
7. **SSH host key verification after power cycle**: After DGX power cycle, SSH to MacBook may fail with `Host key verification failed`. Use `-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null` for automated scripts.
8. **Terminal edit access is fully available**: DGX Hermes has complete file editing capabilities - see `references/dgx-hermes-terminal-edit-access-may16-2026.md` for full verification details.
9. **Full capabilities verified**: All 10 capability tests passed - see `references/dgx-hermes-full-capabilities-verification.md` for details.

## Verification

Check all services:
```bash
ps aux | grep -E 'vllm|hermes' | grep -v grep
```

Expected output:
- vLLM process (port 8000)
- Hermes daemon (run_hermes_daemon.py)
- Gateway process (gateway.run)
- Distillation daemon (dgx_distillation_daemon.py)
