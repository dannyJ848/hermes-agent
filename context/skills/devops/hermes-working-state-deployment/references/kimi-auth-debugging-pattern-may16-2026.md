# Kimi Auth Debugging Pattern (May 16, 2026)

## Symptom

One Hermes CLI works with Kimi provider, another doesn't. Both have:
- Same provider name (`kimi-coding`)
- Same API key (exported in shell)
- Same base URL

But one gets 401 "Invalid API key" while the other works fine.

## Root Cause: Model Name Drift

The Kimi provider has THREE locations where the model name must match:

1. `model.default` — the default model for new chats
2. `providers.kimi-coding.models` — the model name as a dictionary key
3. `fallback_model.model` — fallback when primary fails

**Common drift:**
```yaml
model:
  default: kimi-k2.6          # Location 1

providers:
  kimi-coding:
    api: https://api.kimi.com/coding
    api_key: ${KIMI_API_KEY}
    models:
      kimi-for-coding:        # Location 2 — DIFFERENT!
        context_length: 131072

# ... later in file ...
fallback_model:
  provider: kimi-coding
  model: kimi-k2.6            # Location 3 — matches 1 but not 2!
```

When you request `model: kimi-k2.6`, the provider looks up `kimi-k2.6` in its `models` dict. If the dict key is `kimi-for-coding`, lookup fails → 401.

## Fix

All three must match exactly:
```yaml
model:
  default: kimi-for-coding    # ← matches dict key

providers:
  kimi-coding:
    models:
      kimi-for-coding:        # ← dict key matches default
        context_length: 131072

fallback_model:
  model: kimi-for-coding      # ← matches both above
```

## Verification

```bash
# Check all three locations
grep -n "default:\|kimi-coding:\|fallback_model:" ~/.hermes/config.yaml

# Should show consistent model names
```

## Related: Base URL /v1 Pitfall

The Kimi `/coding` endpoint speaks Anthropic Messages protocol. The Anthropic SDK internally appends `/v1/messages`.

- **Correct:** `https://api.kimi.com/coding` → SDK adds `/v1/messages` → `/coding/v1/messages` ✓
- **Wrong:** `https://api.kimi.com/coding/v1` → SDK adds `/v1/messages` → `/coding/v1/v1/messages` ✗ 404

## Credential Pool Preference

Hermes credential pool reads API keys in this order:
1. `~/.hermes/.env` (highest priority)
2. Shell environment variables (`$KIMI_API_KEY`)
3. `~/.hermes/auth.json` cache

**Critical:** Even if `KIMI_API_KEY` is exported in your shell, if `~/.hermes/.env` contains a different/stale key, Hermes uses the `.env` key.

**Fix:** Always update `~/.hermes/.env`, not just shell exports:
```bash
echo "KIMI_API_KEY=your-new-key" >> ~/.hermes/.env
```

## Complete Auth Checklist

| Check | Command | Expected |
|-------|---------|----------|
| Base URL | `grep api.kimi.com ~/.hermes/config.yaml` | `https://api.kimi.com/coding` (no /v1) |
| Model name consistency | `grep -n "default:\|kimi-coding:\|fallback_model:" ~/.hermes/config.yaml` | All same name |
| API key in .env | `grep KIMI_API_KEY ~/.hermes/.env` | Present and valid |
| Auth cache | `ls ~/.hermes/auth.json` | File exists (auto-created) |
| Provider config | `grep -A10 "kimi-coding:" ~/.hermes/config.yaml` | Full provider block |

## Quick Fix Script

```bash
# Fix model name drift
sed -i 's/kimi-k2.6/kimi-for-coding/g' ~/.hermes/config.yaml

# Fix base URL
sed -i 's|api.kimi.com/coding/v1|api.kimi.com/coding|g' ~/.hermes/config.yaml

# Verify
hermes config get model.default
hermes config get providers.kimi-coding.models
```
