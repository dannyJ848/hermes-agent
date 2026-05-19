# Kimi / Moonshot Auth Debugging Guide

## The Five-Layer Kimi Auth Stack

When Kimi auth fails (401/404), check in this order:

### Layer 1: Key Validity
The key itself must be valid and active.

```bash
# Test directly with curl — bypasses Hermes entirely
KEY="$MOONSHOT_API_KEY"
curl -s -X POST https://api.kimi.com/coding/v1/messages \
  -H "x-api-key: $KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model": "kimi-for-coding", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]}'
```

If curl returns 401, the key is **genuinely invalid** — no Hermes config change will fix it. Get a new key from https://kimi.com/code → Settings → API Keys.

### Layer 2: Endpoint URL (The /v1 Trap)

The base URL must be `https://api.kimi.com/coding` — **NO `/v1` suffix**.

Why: The `/coding` endpoint speaks Anthropic Messages protocol. The Anthropic SDK internally appends `/v1/messages`. So:
- Correct: `https://api.kimi.com/coding` → SDK adds `/v1/messages` → `/coding/v1/messages` ✓
- Wrong: `https://api.kimi.com/coding/v1` → SDK adds `/v1/messages` → `/coding/v1/v1/messages` → 404

Check config:
```bash
grep "base_url\|api:" ~/.hermes/config.yaml | grep kimi
```

Fix:
```bash
sed -i '' 's|api.kimi.com/coding/v1|api.kimi.com/coding|g' ~/.hermes/config.yaml
```

### Layer 3: Credential Source (The .env Priority Trap)

Hermes **prefers `~/.hermes/.env` over shell environment variables**. This is hardcoded in `agent/credential_pool.py`:

```python
def _get_env_prefer_dotenv(key: str) -> str:
    env_file = load_env()
    val = env_file.get(key) or os.environ.get(key) or ""
    return val.strip()
```

This means even if `MOONSHOT_API_KEY` is set in your shell, if `KIMI_API_KEY` exists in `~/.hermes/.env`, the `.env` value wins.

**Diagnostic:**
```bash
# Compare the actual keys
python3 -c "
import os
env_key = os.environ.get('MOONSHOT_API_KEY', '')
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        if line.startswith('KIMI_API_KEY='):
            dotenv_key = line.strip().split('=', 1)[1]
            break
print(f'Shell MOONSHOT length: {len(env_key)}')
print(f'.env KIMI length: {len(dotenv_key)}')
print(f'Same key: {env_key == dotenv_key}')
print(f'Shell prefix: {env_key[:20]}')
print(f'.env prefix: {dotenv_key[:20]}')
"
```

**Fix:** Ensure both locations have the SAME key, or remove `KIMI_API_KEY` from `.env` to let the shell env win.

### Layer 4: Auth Cache (The "Exhausted" Trap)

Hermes caches auth results in `~/.hermes/auth.json`. If a key ever failed, it gets marked `"last_status": "exhausted"`. Even after updating the key, Hermes won't retry until you clear the cache.

**Symptom:** Updated key still gets 401, and the token prefix in the error doesn't match what you just set.

**Diagnostic:**
```bash
python3 -c "
import json
with open(os.path.expanduser('~/.hermes/auth.json')) as f:
    data = json.load(f)
for cred in data.get('credential_pool', {}).get('kimi-coding', []):
    print(f'Status: {cred[\"last_status\"]}')
    print(f'Source: {cred[\"source\"]}')
    print(f'Key prefix: {cred[\"access_token\"][:20]}')
"
```

**Fix:**
```bash
rm ~/.hermes/auth.json
# Hermes will recreate it on next run with fresh credentials
```

### Layer 5: Source Code Routing

For `sk-kimi-` prefixed keys, Hermes routes to `https://api.kimi.com/coding` (not `api.moonshot.ai/v1`). This is handled in `hermes_cli/auth.py`:

```python
KIMI_CODE_BASE_URL = "https://api.kimi.com/coding"

def _resolve_kimi_base_url(api_key, default_url, env_override):
    if env_override:
        return env_override
    if api_key.startswith("sk-kimi-"):
        return KIMI_CODE_BASE_URL
    return default_url
```

If the key doesn't start with `sk-kimi-`, it goes to the legacy `api.moonshot.ai/v1` endpoint.

## Diagnostic Script

Save as `~/diagnose-kimi-auth.sh`:

```bash
#!/bin/bash
set -e

echo "=== Kimi Auth Diagnostic ==="
echo ""

# 1. Check shell env
echo "[1] Shell environment:"
if [ -n "$MOONSHOT_API_KEY" ]; then
    echo "  MOONSHOT_API_KEY: ${MOONSHOT_API_KEY:0:15}... (length: ${#MOONSHOT_API_KEY})"
else
    echo "  MOONSHOT_API_KEY: NOT SET"
fi
echo ""

# 2. Check .env
echo "[2] ~/.hermes/.env:"
if [ -f ~/.hermes/.env ]; then
    if grep -q "KIMI_API_KEY" ~/.hermes/.env; then
        KEY=$(grep "KIMI_API_KEY" ~/.hermes/.env | cut -d= -f2)
        echo "  KIMI_API_KEY: ${KEY:0:15}... (length: ${#KEY})"
    else
        echo "  KIMI_API_KEY: NOT FOUND"
    fi
else
    echo "  ~/.hermes/.env: DOES NOT EXIST"
fi
echo ""

# 3. Check config
echo "[3] config.yaml base URL:"
grep -i "kimi" ~/.hermes/config.yaml | grep "api:" || echo "  No kimi API line found"
echo ""

# 4. Check auth cache
echo "[4] auth.json cache:"
if [ -f ~/.hermes/auth.json ]; then
    python3 -c "
import json, os
with open(os.path.expanduser('~/.hermes/auth.json')) as f:
    data = json.load(f)
creds = data.get('credential_pool', {}).get('kimi-coding', [])
if creds:
    c = creds[0]
    print(f'  Status: {c[\"last_status\"]}')
    print(f'  Source: {c[\"source\"]}')
    print(f'  Key prefix: {c[\"access_token\"][:20]}')
else:
    print('  No kimi-coding credentials cached')
"
else
    echo "  auth.json: NOT FOUND (will be created on first run)"
fi
echo ""

# 5. Test key with curl
echo "[5] Direct API test (curl):"
KEY="${MOONSHOT_API_KEY:-}"
if [ -z "$KEY" ]; then
    KEY=$(grep "KIMI_API_KEY" ~/.hermes/.env 2>/dev/null | cut -d= -f2)
fi
if [ -n "$KEY" ]; then
    RESULT=$(curl -s -X POST https://api.kimi.com/coding/v1/messages \
      -H "x-api-key: $KEY" \
      -H "anthropic-version: 2023-06-01" \
      -H "content-type: application/json" \
      -d '{"model": "kimi-for-coding", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}]}')
    if echo "$RESULT" | grep -q "authentication_error"; then
        echo "  FAIL: Key rejected by API (401)"
        echo "  → Get new key from https://kimi.com/code"
    elif echo "$RESULT" | grep -q "content"; then
        echo "  PASS: Key works!"
    else
        echo "  UNKNOWN: $RESULT"
    fi
else
    echo "  SKIP: No key available to test"
fi
echo ""

echo "=== Recommendations ==="
if [ -f ~/.hermes/auth.json ]; then
    python3 -c "
import json, os
with open(os.path.expanduser('~/.hermes/auth.json')) as f:
    data = json.load(f)
creds = data.get('credential_pool', {}).get('kimi-coding', [])
if creds and creds[0].get('last_status') == 'exhausted':
    print('• Remove auth cache: rm ~/.hermes/auth.json')
"
fi
echo "• Ensure KIMI_API_KEY in ~/.hermes/.env matches MOONSHOT_API_KEY in shell"
echo "• Verify base URL has NO /v1 suffix: grep api.kimi.com ~/.hermes/config.yaml"
```

## Quick Fixes

| Problem | Fix |
|---------|-----|
| 401 — key invalid | Get new key from https://kimi.com/code |
| 404 — wrong endpoint | `sed -i '' 's|coding/v1|coding|g' ~/.hermes/config.yaml` |
| 401 — exhausted cache | `rm ~/.hermes/auth.json` |
| Key mismatch (.env vs shell) | Update both to same key, or remove KIMI_API_KEY from .env |
| New terminal, no env | Add to `~/.zshenv`: `export MOONSHOT_API_KEY="..."` |
