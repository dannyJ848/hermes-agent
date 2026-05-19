# DGX Hermes Service Setup - May 16, 2026

## Problem

After power-cycling the DGX, Hermes Agent needs to be automatically restarted as a systemd service that:
1. Connects to the local vLLM endpoint
2. Uses the module shadowing fix (pre-import gateway/plugins packages)
3. Handles the `asyncio.run(main())` coroutine issue properly

## Module Shadowing Fix Wrapper Script

The `run_agent.py` `main()` function returns `None` instead of a coroutine when run in certain contexts. The wrapper script must handle this:

```python
#!/usr/bin/env python3
# /data/SpecForge/hermes-agent/run_hermes_dgx_fixed.py
import sys
import os
import importlib.util

project_root = "/data/SpecForge/hermes-agent"
sys.path.insert(0, project_root)

# Pre-load gateway package
gateway_init = os.path.join(project_root, "gateway", "__init__.py")
if os.path.exists(gateway_init) and "gateway" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "gateway", gateway_init,
        submodule_search_locations=[os.path.join(project_root, "gateway")]
    )
    gateway_pkg = importlib.util.module_from_spec(spec)
    sys.modules["gateway"] = gateway_pkg
    spec.loader.exec_module(gateway_pkg)

# Pre-load plugins package
plugins_init = os.path.join(project_root, "plugins", "__init__.py")
if os.path.exists(plugins_init) and "plugins" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "plugins", plugins_init,
        submodule_search_locations=[os.path.join(project_root, "plugins")]
    )
    plugins_pkg = importlib.util.module_from_spec(spec)
    sys.modules["plugins"] = plugins_pkg
    spec.loader.exec_module(plugins_pkg)

# Import and run main
from run_agent import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
```

## systemd Service Configuration

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

## Installation Commands

```bash
# Copy wrapper script
chmod +x /data/SpecForge/hermes-agent/run_hermes_dgx_fixed.py

# Install service
sudo systemctl daemon-reload
sudo systemctl enable hermes-dgx.service
sudo systemctl start hermes-dgx.service

# Check status
sudo systemctl status hermes-dgx.service
sudo journalctl -u hermes-dgx.service -f
```

## Key Configuration Files

### vLLM Config (config.yaml)
```yaml
model:
  api_key: not-needed
  chat_template_kwargs:
    enable_thinking: true
  default: Qwen3.6-27B-Uncensored
  provider: local-dgx
  base_url: http://localhost:8000/v1
```

### vLLM Docker Launch
```bash
docker run -d \
  --name vllm-base-lora \
  --runtime nvidia --gpus all \
  -p 8000:8000 \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints:/data/SpecForge/custom_dflash/checkpoints \
  -e CUDA_VISIBLE_DEVICES=0 \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --max-model-len 131072 \
  --enable-lora \
  --max-lora-rank 256 \
  --lora-modules custom-model=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --speculative-config '{"method": "dflash", "model": "/data/models/Qwen3.5-27B-DFlash", "num_speculative_tokens": 5}' \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 256 \
  --gpu-memory-utilization 0.95 \
  --dtype bfloat16 \
  --trust-remote-code \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

## Verification

```bash
# Check vLLM
curl -s http://localhost:8000/v1/models | head -c 100

# Check Hermes
sudo systemctl status hermes-dgx.service
sudo journalctl -u hermes-dgx.service -n 20

# Test Hermes processing
# Look for: "✅ Completed: True" in logs
```

## Post-Power-Cycle Recovery

After DGX power cycle:
1. vLLM container auto-restarts via docker restart policy
2. Hermes service auto-restarts via systemd
3. Both come up automatically within ~5 minutes

If Hermes fails with "Connection error", vLLM is still loading. Wait 2-3 minutes and check again.

## Session Reference

- Date: May 16, 2026
- Context: DGX power cycle recovery, Hermes service setup
- Key issue: `run_agent.main()` returns None, causing `asyncio.run()` to fail
- Fix: Wrapper script handles module shadowing + coroutine issue
- vLLM flags added: `--enable-auto-tool-choice --tool-call-parser hermes`
