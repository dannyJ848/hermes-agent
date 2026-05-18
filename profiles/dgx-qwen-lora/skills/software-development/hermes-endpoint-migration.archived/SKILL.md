---
name: hermes-endpoint-migration
description: Switch Hermes Agent's API endpoint (e.g., Z.AI coding API to general LLM API). Covers the three-layer cache that must all be updated.
version: 1.0
tags: [hermes, zai, endpoint, config, migration]
---

# Migrating Hermes API Endpoints

## When to Use
- Switching from Z.AI coding API (`/api/coding/paas/v4/`) to general LLM API (`/api/paas/v4/`)
- Changing any provider's base URL (GLM, OpenRouter, etc.)
- A model works via curl but Hermes keeps hitting the old endpoint
- After buying API credits or upgrading plans and the new models still fail

## The Three-Layer Cache (ALL must be updated)

Hermes resolves the API endpoint in priority order. If ANY layer still has the old URL, the change won't take effect. Update ALL three:

### Layer 1: config.yaml
```bash
# Per-profile config
sed -i '' 's|old-endpoint|new-endpoint|g' ~/.hermes/config.yaml
# For squad profiles:
for p in soma-coder soma-researcher soma-tester; do
  sed -i '' 's|old-endpoint|new-endpoint|g' ~/.hermes/profiles/$p/config.yaml
done
```

### Layer 2: auth.json (credential pool cache)
Hermes caches the base_url per provider in auth.json. This overrides config.yaml.
```bash
# Fix all profiles
for f in ~/.hermes/auth.json ~/.hermes/profiles/*/auth.json; do
  [ -f "$f" ] && sed -i '' 's|old-endpoint|new-endpoint|g' "$f"
done
```
Verify: `grep base_url ~/.hermes/auth.json`

### Layer 3: .env (HIGHEST PRIORITY)
The provider's `base_url_env_var` (e.g., `GLM_BASE_URL` for provider "zai") takes precedence over everything.
```bash
# Fix all .env files
for f in ~/.hermes/.env ~/.hermes/profiles/*/.env; do
  [ -f "$f" ] && sed -i '' 's|old-endpoint|new-endpoint|g' "$f"
done
```
Verify: `grep GLM_BASE_URL ~/.hermes/.env`

### Priority Order (from hermes_cli/auth.py)
```
.env (GLM_BASE_URL env var) > auth.json (credential pool) > config.yaml > ProviderConfig.inference_base_url
```

## Verification

### Quick curl test first
Before restarting Hermes, verify the new endpoint works directly:
```bash
source ~/.hermes/.env
curl -s -w "\nHTTP: %{http_code}" \
  "https://api.z.ai/api/paas/v4/chat/completions" \
  -H "Authorization: Bearer $GLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "glm-5v-turbo", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10}'
```
HTTP 200 = endpoint works. HTTP 429 with code 1311 = plan gating issue.

### Check available models
```bash
curl -s "https://api.z.ai/api/paas/v4/models" \
  -H "Authorization: Bearer $GLM_API_KEY" | python3 -m json.tool
```

### After restart, confirm in logs
Watch for the endpoint in error messages -- if you see the OLD endpoint, a cache layer was missed.

## Restart Required
All changes require killing and respawning agents. Config is loaded at startup.
```bash
# For tmux-based squad agents
tmux send-keys -t soma-researcher C-c
sleep 1
tmux send-keys -t soma-researcher "cd ~/hermes-agent && source venv/bin/activate && soma-researcher chat" Enter
```

## Mixed-Endpoint Squad Setup

When some models need the general API (finite credits) and others use the coding API (unlimited), configure per-profile:

```
default (orchestrator) → coding API + glm-5.1 (unlimited)
soma-coder             → coding API + glm-5.1 (unlimited)
soma-tester            → coding API + glm-5.1 (unlimited)
soma-researcher        → general API + glm-5v-turbo (paid credits)
```

**Why:** Coding plan gives unlimited tokens for text models (glm-5.1). Vision models (glm-5v-turbo) require the general API which burns prepaid credits. Only the agent doing vision work should be on the general endpoint.

**Pattern:** Update ONLY the vision agent's three cache layers to the general endpoint. Leave all others on coding.

## Known Endpoint Mappings (Z.AI)

| Product | Endpoint | Access |
|---------|----------|--------|
| Coding API | `https://api.z.ai/api/coding/paas/v4/` | Coding plan subscription (unlimited for text models) |
| General LLM API | `https://api.z.ai/api/paas/v4/` | API credits (pay-per-use, finite) |
| China | `https://open.bigmodel.cn/api/coding/paas/v4` | China region |

Some models (like GLM-5V-Turbo at launch) may only be available on the general LLM API, not the coding API, even with a max coding plan.

## Diagnostic Checklist

1. `grep -rl "old-endpoint" ~/.hermes/ ~/.hermes/profiles/*/` -- find ALL files with old URL
2. Check `.env`, `auth.json`, `config.yaml` in that priority order
3. Verify with curl before restarting
4. After restart, check error logs show the NEW endpoint
5. If still wrong, search for `__pycache__` dirs and delete them

## Pitfalls
- auth.json caches the endpoint per-credential and is NOT updated by config.yaml changes
- The .env var (`GLM_BASE_URL`) is the highest priority -- always check it first
- `grep -rl` is your friend: search recursively for the old endpoint string
- Squad profiles each have independent .env, auth.json, AND config.yaml (3 layers x N profiles)
- Model "not in plan" (error 1311) vs "unknown model" (error 1211) -- 1311 means the ID is correct but plan-gated, 1211 means wrong model ID
