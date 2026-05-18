---
name: hermes-provider-config
title: Hermes Provider and Endpoint Configuration
description: |
  Configure, debug, and migrate Hermes API providers and endpoints. Covers endpoint
  migration (Z.AI, OpenRouter, GLM), cloud provider debugging (Browserbase), and
  auxiliary task routing (compression, titles, vision). The three-layer cache
  problem and protocol mismatch fixes.
triggers:
  - When switching API endpoints or providers
  - When auxiliary tasks (compression, titles, vision) fail with 404/401
  - When Browserbase or cloud features don't activate
  - When the user says "migration", "endpoint", "provider", "404", "auxiliary"
category: software-development
---

# Hermes Provider and Endpoint Configuration

## Overview

Hermes has multiple API surfaces that can misalign: main agent loop, auxiliary client
(compression, titles, vision), and cloud providers (Browserbase). This skill covers
all provider configuration scenarios.

---

## Section 1: Endpoint Migration

### The Three-Layer Cache (ALL must be updated)

Hermes resolves endpoints in priority order. If ANY layer has the old URL, the change
won't take effect.

**Layer 1: config.yaml**
```bash
# Per-profile config
sed -i '' 's|old-endpoint|new-endpoint|g' ~/.hermes/config.yaml
# For squad profiles:
for p in soma-coder soma-researcher soma-tester; do
  sed -i '' 's|old-endpoint|new-endpoint|g' ~/.hermes/profiles/$p/config.yaml
done
```

**Layer 2: auth.json (credential pool cache)**
```bash
# Edit ~/.hermes/auth.json — update base_url for the provider
python3 -c "
import json
with open('~/.hermes/auth.json') as f: data = json.load(f)
# Update provider entry
with open('~/.hermes/auth.json', 'w') as f: json.dump(data, f, indent=2)
"
```

**Layer 3: Environment variables**
```bash
# Update .env
sed -i '' 's|old-endpoint|new-endpoint|g' ~/.hermes/.env
# Export for current session
export ZAI_API_BASE_URL="https://api.z.ai/api/paas/v4/"
```

### Common Migrations

**Z.AI coding → general LLM:**
- Old: `https://api.z.ai/api/coding/paas/v4/`
- New: `https://api.z.ai/api/paas/v4/`

**OpenRouter → direct provider:**
- Update `base_url` in auth.json
- Update model mapping in config.yaml

---

## Section 2: Auxiliary Provider Routing

### The Problem

Main agent works, but side-tasks (compression, titles, web extract, vision) fail with 404.

**Root cause:** Auxiliary client (`agent/auxiliary_client.py`) always speaks OpenAI Chat
Completions (`POST /v1/chat/completions`). When main provider is "coding-only" (Kimi-coding,
Z.AI coding, GLM-coding), the auxiliary client routes to an endpoint that doesn't speak
OpenAI protocol.

### Symptoms

- "Compaction is not working" / context keeps growing
- Sessions have no titles or default "untitled"
- `Auxiliary <task> failed: HTTP 404` in logs
- `_last_summary_error` set on compressor but main API calls succeed
- Compressor test runs fine standalone but fails in live loop

### Fix: Per-Task Provider Routing in config.yaml

```yaml
auxiliary:
  provider: openai          # Dedicated auxiliary provider
  model: gpt-4o-mini        # Cheap, fast, speaks OpenAI protocol
  api_key: sk-...           # Or reference env var
```

Or use environment-specific overrides:
```yaml
profiles:
  default:
    auxiliary:
      provider: deepseek
      model: deepseek-chat
```

### Verification

```bash
# Test auxiliary client directly
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
from agent.auxiliary_client import AuxiliaryClient
client = AuxiliaryClient()
result = client.compress('test message')
print('Compression OK:', result is not None)
"
```

---

## Section 3: Cloud Provider Debug (Browserbase)

### Symptoms

- Browser tool ignores Browserbase config and falls back to local mode
- Stealth/proxy warnings persist despite env vars
- Cloud features (proxies, stealth) not activating

### Diagnostic Steps

**Step 1: Check .env**
```bash
grep -i BROWSERBASE ~/.hermes/.env
# Should show: BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID, BROWSERBASE_PROXIES=true
```

**Step 2: Check config.yaml**
```bash
grep -A5 "^browser:" ~/.hermes/config.yaml
# MUST include: cloud_provider: browserbase
```

**Step 3: Verify API key works**
```bash
curl -s https://www.browserbase.com/v1/sessions \
  -H "X-BB-API-Key: $BROWSERBASE_API_KEY" | head -1
```

### Common Fixes

**Missing cloud_provider key:**
```yaml
browser:
  cloud_provider: browserbase
  stealth: true
  proxies: true
```

**Env vars not loaded:**
```bash
# Ensure vars are in ~/.hermes/.env (not just shell environment)
echo "BROWSERBASE_API_KEY=your_key" >> ~/.hermes/.env
echo "BROWSERBASE_PROJECT_ID=your_project" >> ~/.hermes/.env
```

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| Main agent loop | Provider-specific adapters (Anthropic, OpenAI, Codex) |
| Auxiliary client | Always OpenAI Chat Completions protocol |
| Cloud provider | Browserbase, etc. — configured in config.yaml + .env |
| Three-layer cache | config.yaml → auth.json → env vars |
| Protocol mismatch | Coding-only endpoint can't serve OpenAI Chat Completions |
| Kimi endpoint | NO `/v1` suffix — SDK adds it internally |
| Kimi env var | `MOONSHOT_API_KEY` (not `KIMI_API_KEY`) |

## Pitfalls

- **Layer 1 only updated:** Forgetting auth.json or env vars → old endpoint still used
- **Auxiliary ≠ main:** Main provider can be Kimi-coding while auxiliary must be OpenAI-compatible
- **Config.yaml key missing:** `cloud_provider: browserbase` is required, not just env vars
- **.env vs shell env:** Hermes loads from `~/.hermes/.env`, not current shell environment
- **Squad profiles:** Each profile has its own config.yaml — update all of them
- **Kimi endpoint:** NO `/v1` suffix — SDK adds it internally
- **Kimi env var:** `MOONSHOT_API_KEY` (not `KIMI_API_KEY`)
- **New terminal, no env:** Shell profile not sourced → key not found → "no-key-required" prefix
- **auth.json exhaust cache:** Hermes caches failed auth in `~/.hermes/auth.json` with `last_status: "exhausted"`. Even after updating the key, it won't retry until you delete `auth.json`. Symptom: updated key still gets 401 with a different token prefix than expected.
- **Stale .env overrides shell:** `~/.hermes/.env` takes priority over shell environment variables. If `.env` has an old `KIMI_API_KEY`, it wins over `MOONSHOT_API_KEY` in the shell. Fix: update `.env` or remove the conflicting key.
- **Fallback 404 after 401:** When primary auth fails, Hermes falls back to same provider but may drop the base_url or model name, causing 404. Fix the primary auth first — don't chase the 404.
- **Redaction hides key differences:** `sk-kim...RTxu` and `sk-kim...6fDw` look identical when redacted. Always extract the actual prefix with `echo "${VAR:0:20}"` or Python — don't trust redacted output for comparison.
- **Source code over speculation:** When auth behavior seems wrong, read `agent/credential_pool.py` and `hermes_cli/auth.py` rather than guessing. The `_get_env_prefer_dotenv()` function explicitly prefers `~/.hermes/.env` over `os.environ` — this is documented in code, not config.
- **Model name ≠ provider endpoint:** A provider like `kimi-coding` can serve multiple models (`kimi-k2.6`, `kimi-k1.5`, `kimi-for-coding`). The `default:` model field in config.yaml determines WHICH model the gateway requests, NOT the provider endpoint. If the user says "I should be on kimi-coding" they may mean either (a) the provider endpoint or (b) a specific model served by that endpoint. Always check BOTH `provider:` and `default:` fields. Changing only the provider without updating the model name leaves the old model in use. Check the `models:` section under the provider too — the model definition (context_length, supports_tools, etc.) is tied to the model name.
- **Gateway session model is sticky:** Changing `config.yaml` only affects FUTURE sessions. The current running session uses whatever model the gateway resolved at startup. To verify the current session's model, check the gateway logs or restart the agent — don't assume the config change took effect immediately.
- **User frustration on over-debug:** When user says "stop" or "this is wrong", immediately halt the current debugging path and ask for clarification. Don't continue down a rabbit hole. The user's "holy shit you're back" signals that losing working state is catastrophic — prioritize capturing and preserving working state over fixing broken state.
- **Working state capture first:** Before attempting any fix that might break the current working session, create a complete snapshot (config, .env, auth.json, git commit). The restore script should be the FIRST artifact, not an afterthought.
- **Fallback 404 after 401 is a secondary error:** When the primary auth fails (401), Hermes tries fallback which may drop the base_url or model, causing 404. Don't chase the 404 — fix the 401 first. The 404 is a symptom, not the root cause.
- **Multiple Hermes CLIs share state:** If one CLI works and another doesn't, they're reading the same `~/.hermes/config.yaml` and `~/.hermes/.env`. The difference is usually (a) shell env vars inherited at startup, (b) auth.json cache state, or (c) git commit of source code. Check `ps` to see which process is which, and `lsof` to see what files each has open.

## References

- `references/three-layer-cache-diagram.md` — Visual diagram of endpoint resolution
- `references/auxiliary-protocol-matrix.md` — Which providers speak OpenAI protocol
- `references/browserbase-config-template.md` — Complete Browserbase configuration
- `references/kimi-endpoint-trap.md` — Kimi Code endpoint and auth specifics
- `references/kimi-auth-debug.md` — **Complete Kimi auth debugging guide with 5-layer diagnostic and diagnostic script**
- `references/kimi-env-priority-source.md` — **Source code excerpt showing `.env` priority over shell env, with practical impact table**
- `references/kimi-auth-debug.md` — Complete Kimi auth debugging guide with diagnostic script
- `references/kimi-env-priority-source.md` — Source code excerpt showing `.env` priority over shell env
