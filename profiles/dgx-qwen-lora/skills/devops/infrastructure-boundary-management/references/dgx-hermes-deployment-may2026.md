# DGX Hermes Full Deployment — May 14 2026

Session: Deployed Hermes Agent to DGX Spark with full plugin/tool parity to MacBook.

## Problem

DGX Hermes had only 21 tools vs 103 on MacBook. Root causes:
1. Only 7 plugins enabled (vs 38 on MacBook)
2. No web search API keys
3. No browser automation (missing Node.js + agent-browser)
4. Config file location mismatch
5. Missing agent modules (10 files created May 13, not synced)

## Solution — Step by Step

### 1. Plugin Configuration (The Gotcha)

Hermes reads `plugins.enabled` from `~/.hermes/config.yaml`, NOT from the repo `config.yaml`.

```bash
# WRONG — editing repo config
vim /data/SpecForge/hermes-agent/config.yaml

# RIGHT — editing home config
vim /home/djg6228/.hermes/config.yaml
```

Verify which config is active:
```python
from hermes_cli.config import get_config_path
print(get_config_path())  # → /home/djg6228/.hermes/config.yaml
```

Plugin format must be dict-style:
```yaml
plugins:
  disabled:
    - evey-eyes
    - evey-moltbook
  enabled:
    - cognitive-systems
    - distillation
    - evey-autonomy
    - evey-bridge
    # ... 35 total plugins
```

NOT the old list-style:
```yaml
plugins:
  - hermes_cli.plugins.memory   # ← WRONG, won't work
```

### 2. Tool Count Diagnosis

```bash
cd /data/SpecForge/hermes-agent
venv/bin/python -c "
from model_tools import get_tool_definitions
tools = get_tool_definitions(quiet_mode=True)
print(f'Total tools: {len(tools)}')
"
```

Expected progression:
| Stage | Count | Notes |
|-------|-------|-------|
| Baseline | 21 | Core only |
| + Plugins enabled | 84 | Evey plugins loaded |
| + Web APIs | 87 | Brave + Firecrawl keys added |
| + Browser | 97 | Node.js + agent-browser installed |

### 3. Browser Automation Setup on DGX

DGX is ARM64 (aarch64), not x86_64. Standard Node.js binaries fail.

```bash
# WRONG — x86_64 binary on ARM64
curl -fsSL https://nodejs.org/dist/v20.12.2/node-v20.12.2-linux-x64.tar.xz
# → "cannot execute binary file"

# RIGHT — ARM64 binary
cd /tmp
curl -fsSL https://nodejs.org/dist/v20.12.2/node-v20.12.2-linux-arm64.tar.xz -o node.tar.xz
tar -xf node.tar.xz
mv node-v20.12.2-linux-arm64 ~/node
~/node/bin/node --version  # → v20.12.2
```

Install agent-browser:
```bash
export PATH=/home/djg6228/node/bin:$PATH
npm install -g agent-browser
agent-browser --version  # → 0.27.0
```

Add to PATH permanently:
```bash
echo 'export PATH=/home/djg6228/node/bin:$PATH' >> ~/.bashrc
```

For systemd services, add to service file:
```ini
[Service]
Environment=PATH=/home/djg6228/node/bin:/usr/local/bin:/usr/bin:/bin
```

### 4. API Key Sync

Copy `.env` from MacBook to DGX:
```bash
scp ~/.hermes/.env djg6228@10.0.0.171:/home/djg6228/.hermes/.env
```

Keys that matter for tool count:
- `BRAVE_API_KEY` → enables `web_search`
- `FIRECRAWL_API_KEY` → enables `web_extract`
- `BROWSERBASE_API_KEY` + `BROWSERBASE_PROJECT_ID` → enables browser tools

### 5. File Sync Verification

After syncing, verify critical files match:

```bash
# Count core Python files (excluding venv, node_modules, .git, __pycache__)
find ~/hermes-agent -type f -name '*.py' \
  -not -path '*/venv/*' \
  -not -path '*/node_modules/*' \
  -not -path '*/.git/*' \
  -not -path '*/__pycache__/*' | wc -l
# MacBook: 1756, DGX: 1766 (+10 DGX-specific files)

# Check specific missing files
for f in agent/adaptive_context_sculptor.py agent/cognitive_orchestrator.py agent/self_evaluation_gate.py; do
    ssh djg6228@10.0.0.171 "test -f /data/SpecForge/hermes-agent/$f && echo OK || echo MISSING"
done
```

### 6. Browser Config in Hermes

Add to `~/.hermes/config.yaml`:
```yaml
browser:
  inactivity_timeout: 3600
  command_timeout: 30
  record_sessions: false
  allow_private_urls: false
  engine: auto
  auto_local_for_private_urls: true
  cdp_url: ''
  dialog_policy: must_respond
  dialog_timeout_s: 300
  camofox: {}
  cloud_provider: browserbase
```

## Verification Commands

```bash
# Full tool count with all env vars set
export PATH=/home/djg6228/node/bin:$PATH
export BROWSERBASE_API_KEY=***
export BROWSERBASE_PROJECT_ID=eda78810-ea93-43b2-ae25-f1e2096ca5c8
cd /data/SpecForge/hermes-agent
venv/bin/python -c "
from model_tools import get_tool_definitions
tools = get_tool_definitions(quiet_mode=True)
print(f'Total: {len(tools)}')
for t in sorted(tools, key=lambda x: x['function']['name']):
    print(f'  {t[\"function\"][\"name\"]}')
"
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "agent-browser CLI not found" | PATH missing Node.js | `export PATH=/home/djg6228/node/bin:$PATH` |
| "Skipping 'foo' (not in plugins.enabled)" | Plugin not in home config | Edit `~/.hermes/config.yaml`, not repo config |
| "Tool registration REJECTED: web_extract" | Shadowing between toolsets | Expected — evey_research vs web toolset conflict |
| "No module named 'plugins.spotify'" | Missing Python dep for plugin | Add to `plugins.disabled` or install dep |
| "cannot execute binary file" | Wrong Node.js architecture | Use `linux-arm64`, not `linux-x64` |

## Result

- **Before:** 21 tools
- **After:** 97 tools (94% of MacBook's 103)
- Missing 6: cronjob, feishu_doc_read, feishu_drive_* (4), video_analyze — all API-dependent
