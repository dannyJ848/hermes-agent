# DGX Native Hermes Gateway Deployment

## Overview

Deploy Hermes Agent natively on DGX (or GPU server) as an independent cognitive instance, not just an inference endpoint.

## Discovery Phase — Check Existing Installations

**Always check before installing:**
```bash
# Check common installation paths
ls -la /data/SpecForge/hermes-agent/ 2>/dev/null
ls -la ~/hermes-agent/ 2>/dev/null
ls -la /opt/hermes-agent/ 2>/dev/null

# Check for CLI
find / -name "hermes" -type f 2>/dev/null | grep -v proc | head -5

# Check for config
ls -la ~/.hermes/config.yaml 2>/dev/null
ls -la /data/SpecForge/hermes-agent/config.yaml 2>/dev/null
```

## The Cron Import Conflict

**Symptom:**
```
Exception in thread cron-ticker:
ModuleNotFoundError: No module named 'cron.scheduler'; 'cron' is not a package
```

**Root cause:** `hermes_cli/cron.py` shadows the `cron/` package directory.

**Fix:**
```bash
mv hermes_cli/cron.py hermes_cli/cron_cmd.py
sed -i 's/from hermes_cli.cron import/from hermes_cli.cron_cmd import/g' hermes_cli/main.py
sed -i 's/import hermes_cli.cron/import hermes_cli.cron_cmd/g' hermes_cli/main.py
```

## Systemd Service Template

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
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## Qdrant Setup

```bash
docker run -d --name qdrant -p 6333:6333 \
  -v ~/.hermes/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```

## Verification Checklist

- [ ] vLLM container running (`docker ps | grep vllm`)
- [ ] Qdrant container running (`docker ps | grep qdrant`)
- [ ] Hermes gateway active (`systemctl is-active hermes-dgx-gateway`)
- [ ] 40+ plugins enabled (`hermes plugins list | grep enabled | wc -l`)
- [ ] Local model responding (`curl http://localhost:8000/v1/models`)
- [ ] Cognitive systems loaded (check `hermes status`)
- [ ] **Cognitive orchestrator initialized** (`grep 'Cognitive orchestrator ready' /var/log/hermes/gateway.log`)
