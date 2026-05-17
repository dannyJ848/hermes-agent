# kimi-hermes-auth-configuration

*Researched: 2026-05-16 15:11 CDT*

# Kimi Auth Configuration for Hermes Agent

## Endpoint Structure

The Kimi `/coding` endpoint uses the **Anthropic Messages API protocol**, not standard OpenAI chat completions.

### Base URL
- **Correct**: `https://api.kimi.com/coding`
- **Wrong**: `https://api.kimi.com/coding/v1` → produces 404

The Anthropic SDK internally appends `/v1/messages` to the base URL. So:
- `https://api.kimi.com/coding` + `/v1/messages` = `/coding/v1/messages` ✓
- `https://api.kimi.com/coding/v1` + `/v1/messages` = `/coding/v1/v1/messages` ✗ 404

## API Key Placement

Hermes **credential pool prefers `~/.hermes/.env` over shell environment variables**.

```bash
# This works:
# ~/.hermes/.env
KIMI_API_KEY=sk-kimi-...

# This may be ignored if .env has a different key:
export MOONSHOT_API_KEY=sk-kimi-...
```

## Model Name Consistency

The model name must match in **three locations** in `config.yaml`:

```yaml
model:
  default: kimi-for-coding          # Location 1

providers:
  kimi-coding:
    models:
      kimi-for-coding:              # Location 2 (key name)
        context_length: 262144

fallback_model:
  provider: kimi-coding
  model: kimi-for-coding            # Location 3
```

Drift between these (e.g., `kimi-k2.6` vs `kimi-for-coding`) causes silent auth failures even when the API key is valid.

## Auth Cache

`~/.hermes/auth.json` stores credential state including `last_status: exhausted`. If a key was previously rejected, Hermes marks it exhausted and may not retry. Clear the cache to force re-auth:

```bash
rm ~/.hermes/auth.json
```

## Key Prefix Routing

- `sk-kimi-*` → routes to `https://api.kimi.com/coding` (Kimi Code plan)
- Other prefixes → routes to `https://api.moonshot.ai/v1` (legacy)

The routing is automatic based on key prefix in `hermes_cli/auth.py`.

## Troubleshooting Checklist

1. Check base URL has no `/v1` suffix
2. Verify `KIMI_API_KEY` is in `~/.hermes/.env` (not just shell env)
3. Check all three model name locations match
4. Clear `~/.hermes/auth.json` if key was previously marked exhausted
5. Verify key is valid with direct curl test

## Working State Snapshot

Complete working state captured at:
- `~/.hermes/snapshots/working-20260516-144642/`
- Git commit: `b6fa8f918`
- Deployment script: `~/.hermes/snapshots/deploy-hermes-working-state.sh`


## Sources

- hermes_cli/auth.py
- agent/credential_pool.py
- ~/.hermes/config.yaml
