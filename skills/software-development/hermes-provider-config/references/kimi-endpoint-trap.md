# Kimi Code Endpoint Trap

## The Problem

Kimi Code (`kimi-coding` provider) speaks the Anthropic Messages API protocol. The
endpoint URL structure is counter-intuitive because the Anthropic SDK internally
appends `/v1/messages` to the base URL.

## Endpoint URL

```
Base URL:  https://api.kimi.com/coding
SDK adds: /v1/messages
Final:    https://api.kimi.com/coding/v1/messages  ✓ CORRECT
```

If you add `/v1` to the config:
```
Config:    https://api.kimi.com/coding/v1
SDK adds:  /v1/messages
Final:     https://api.kimi.com/coding/v1/v1/messages  ✗ 404
```

## Configuration Template

```yaml
model:
  base_url: https://api.kimi.com/coding      # NO /v1 suffix
  default: kimi-for-coding
  provider: kimi-coding
  api_key_env: MOONSHOT_API_KEY              # NOT KIMI_API_KEY

providers:
  kimi-coding:
    api: https://api.kimi.com/coding         # NO /v1 suffix
    api_key_env: MOONSHOT_API_KEY            # Must match env var name
    name: kimi-coding
    models:
      kimi-for-coding:
        context_length: 131072
        supports_reasoning: true
        supports_tools: true
```

## Environment Variable Setup

The `MOONSHOT_API_KEY` must be available to all shells:

```bash
# For zsh (macOS default) — add to ~/.zshenv for universal loading
echo 'export MOONSHOT_API_KEY="sk-kimi-..."' >> ~/.zshenv

# Verify in a NEW terminal window
env | grep MOONSHOT
# Expected: MOONSHOT_API_KEY=sk-kimi-...
```

## Key Prefix Auto-Routing

Hermes auto-detects the endpoint based on key prefix:
- `sk-kimi-*` → `https://api.kimi.com/coding` (Anthropic protocol)
- Other prefixes → `https://api.moonshot.ai/v1` (OpenAI protocol)

If you explicitly set `base_url` or `api` in config, auto-detection is bypassed.

## Diagnostic Commands

```bash
# Test endpoint directly
curl -s -X POST https://api.kimi.com/coding/v1/messages \
  -H "x-api-key: $MOONSHOT_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"kimi-for-coding","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'

# Response codes:
# 404 = wrong endpoint (has extra /v1 in config)
# 401 = correct endpoint, wrong/expired key
# 200 = working
```

## Error Quick Reference

| Error | Cause | Fix |
|-------|-------|-----|
| 404 "resource not found" | Endpoint has `/v1` suffix | Remove `/v1` from base_url and api |
| 401 "invalid API key" | Wrong env var name | Use `MOONSHOT_API_KEY` |
| 401 in new terminal | Env var not in shell profile | Add to `~/.zshenv` |
| "no-key-required" prefix | Key not found in environment | Verify `env \| grep MOONSHOT` |
| "sk-kim...gBzP" in config | Stale hardcoded key | Replace with `api_key_env: MOONSHOT_API_KEY` |

## Session History

- **May 16 2026**: User had `https://api.kimi.com/coding/v1` in config → 404. Fixed by
  removing `/v1`. Then had `api_key_env: KIMI_API_KEY` but env var was `MOONSHOT_API_KEY`
  → 401. Fixed by changing env var name. Then stale hardcoded key in model section →
  replaced with `api_key_env`. Finally added `MOONSHOT_API_KEY` to `~/.zshenv` for
  cross-terminal propagation.
