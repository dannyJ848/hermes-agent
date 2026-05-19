# Kimi API Endpoint Configuration Fix

**Date:** May 16, 2026
**Issue:** Kimi Code API returns 404 when config has `/v1` suffix on endpoint URL
**Root cause:** Hermes SDK adds `/v1/messages` internally for Anthropic-protocol endpoints. Double `/v1` produces 404.

## Symptoms

```
API call failed (attempt 1/3): NotFoundError [HTTP 404]
Provider: kimi-coding  Model: kimi-for-coding
Endpoint: https://api.kimi.com/coding/v1
Error: HTTP 404: The requested resource was not found
```

## Root Cause

The Kimi Code endpoint (`api.kimi.com/coding`) speaks the Anthropic Messages protocol. The Hermes SDK (and anthropic SDK) appends `/v1/messages` internally:

- Config has: `https://api.kimi.com/coding/v1`
- SDK appends: `/v1/messages`
- Result: `https://api.kimi.com/coding/v1/v1/messages` → 404

The correct base URL is `https://api.kimi.com/coding` (no `/v1` suffix). The SDK handles the `/v1/messages` path.

## Fix

In `~/.hermes/config.yaml`, change BOTH occurrences:

```yaml
# WRONG — causes 404
model:
  base_url: https://api.kimi.com/coding/v1
  provider: kimi-coding

providers:
  kimi-coding:
    api: https://api.kimi.com/coding/v1
```

```yaml
# CORRECT
model:
  base_url: https://api.kimi.com/coding
  provider: kimi-coding

providers:
  kimi-coding:
    api: https://api.kimi.com/coding
```

## Code Reference

From `hermes_cli/auth.py`:
```python
# Note: the base URL intentionally has NO /v1 suffix.  The /coding endpoint
# speaks the Anthropic Messages protocol, and the anthropic SDK appends
# "/v1/messages" internally — so "/coding" + SDK suffix → "/coding/v1/messages"
# (the correct target). Using "/coding/v1" here would produce
# "/coding/v1/v1/messages" (a 404).
KIMI_CODE_BASE_URL = "https://api.kimi.com/coding"
```

## Verification

After fixing config, test with:
```bash
hermes config get model.base_url
# Should show: https://api.kimi.com/coding (no /v1)
```

## Related

- `hermes_cli/providers.py` — URL heuristic detection for `api.kimi.com/coding`
- `hermes_cli/auth.py` — `_resolve_kimi_base_url()` auto-routes `sk-kimi-*` keys to coding endpoint
