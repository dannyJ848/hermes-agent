---
name: hermes-cloud-provider-debug
description: Debug why Hermes browser/cloud tools aren't using their configured cloud provider (Browserbase, etc.)
version: 1.0
tags: [hermes, browserbase, debugging, config]
---

# Debugging Hermes Cloud Provider Issues

## When to Use
- Browser tool ignores Browserbase config and falls back to local mode
- Stealth/proxy warnings persist despite env vars being set
- Cloud provider features (proxies, stealth) not activating

## Diagnostic Steps

### Step 1: Check .env file has the required vars
```bash
grep -i BROWSERBASE ~/.hermes/.env
# Should show: BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID, BROWSERBASE_PROXIES=true
```

### Step 2: Check config.yaml has the cloud_provider key
This is the most commonly missed step. The browser tool resolves the provider from config.yaml, NOT just env vars.
```bash
grep -A5 "^browser:" ~/.hermes/config.yaml
# MUST include: cloud_provider: browserbase
```
If missing, add it:
```yaml
browser:
  cloud_provider: browserbase
  inactivity_timeout: 120
  command_timeout: 30
```

### Step 3: Check for corrupted source in the provider file
```bash
grep "os.env\.\.\." ~/hermes-agent/tools/browser_providers/browserbase.py
```
If found, fix to `os.environ.get("BROWSERBASE_API_KEY")`. This corruption has been seen in the wild.

### Step 4: Understand the caching mechanism
The cloud provider is resolved ONCE and cached (`_cached_cloud_provider`, `_cloud_provider_resolved` in browser_tool.py). This means:
- Config changes require a **gateway restart**
- The provider is chosen by reading `config.yaml -> browser -> cloud_provider`
- If that key is unset, it returns None (local mode) regardless of env vars

### Step 5: Verify env vars reach the tool process
The browser subprocess inherits `os.environ` from the gateway via `{**os.environ}` (browser_tool.py line ~820). The gateway loads `.env` with `override=True` via `load_hermes_dotenv()` at startup (gateway/run.py line ~88).

Check in a running session:
```python
import os
print("BB_KEY:", "YES" if os.environ.get("BROWSERBASE_API_KEY") else "NO")
```
If NO, the gateway needs restart.

### Step 6: Restart gateway properly
```bash
pkill -9 -f "hermes"
sleep 2
cd ~/hermes-agent && source venv/bin/activate && hermes gateway
```

## Common Failure Patterns

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Running WITHOUT residential proxies" | Missing `cloud_provider: browserbase` in config.yaml | Add to browser section |
| Same warning after adding config | Cached provider resolution | Restart gateway |
| API key not found | .env not loaded into os.environ | Restart gateway (loads .env with override=True) |
| Corrupted os.env...EY" in source | File corruption in browserbase.py | Fix to os.environ.get("BROWSERBASE_API_KEY") |
| 402 on session creation | Plan doesn't support requested feature | Check Browserbase plan tier |

## Key Files
- `~/.hermes/config.yaml` - cloud_provider key
- `~/.hermes/.env` - API credentials
- `~/hermes-agent/tools/browser_tool.py` - provider resolution + caching (lines 230-257)
- `~/hermes-agent/tools/browser_providers/browserbase.py` - session creation
- `~/hermes-agent/gateway/run.py` - .env loading (line ~88)
- `~/hermes-agent/hermes_cli/env_loader.py` - dotenv loading logic

## Lessons Learned
- The config.yaml `cloud_provider` key is the PRIMARY selector, not env vars
- Env vars configure HOW the provider works; config.yaml decides IF it's used
- Always check both .env AND config.yaml -- missing either one breaks things
- The provider cache means you can't hot-reload config changes
