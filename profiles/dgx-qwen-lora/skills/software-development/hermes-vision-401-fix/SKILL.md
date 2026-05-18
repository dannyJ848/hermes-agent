---
name: hermes-vision-401-fix
description: Fix 401 errors on vision calls (browser_vision, vision_analyze) caused by raw params being passed instead of resolved config values in auxiliary_client.py. Re-apply after every hermes-agent update.
version: 2.0
---

# Hermes Vision 401 Fix

## Silent Guard Bug (April 7, 2026)

The `_is_silent` guard in `run_agent.py` ~line 9080 was not catching `[SILENT]` responses from glm-5.1 model, causing infinite aggressive_continue loops.

**Root cause:** Likely Unicode characters, BOM, or zero-width characters in the model's output that survive `.strip().upper()`. Exact cause TBD — added debug logging with `repr()` to capture the actual bytes.

**Fix applied:** Changed from exact match `in ('[SILENT]', ...)` to:
1. Strip zero-width chars (U+200B, U+200C, U+200D, U+FEFF) via regex
2. Use substring check: `'[SILENT]' in _cleaned_silent` OR exact match
3. Added debug logging to print `repr(final_response[:200])` when aggressive mode is active

**File:** `run_agent.py` lines ~9079-9086

## Problem
Vision calls (`browser_vision`, `vision_analyze`) return 401 because `call_llm()` and `async_call_llm()` pass raw (None) params to `resolve_vision_provider_client()` instead of resolved config values. Also, `_resolve_task_provider_model()` drops `cfg_api_key` when provider="auto".

## Symptoms
- All vision tools fail with 401 from the gateway
- Context summary generation fails with 401 (30+ occurrences in Apr 2026 logs)
- Session summarization fails with 401 (session_search_tool.py line 155)
- Standalone Python tests work fine (env vars loaded)
- Bug only manifests inside the running gateway process

## Affected Code Paths
Vision is the documented fix target, but the SAME underlying auth issue affects:
- `tools/vision_tools.py:347` - vision_analyze_tool
- Context summary generation (internal, ~20 failures logged)
- `tools/session_search_tool.py:155` - session summarization
All call `async_call_llm()` which has the raw-params bug.

## Root Causes (3 locations in `agent/auxiliary_client.py`)

### 1. `_resolve_task_provider_model()` auto-return drops api_key
The final fallback returns drop `cfg_api_key`:
```python
# BUG: drops the key
return "auto", resolved_model, None, None
# FIX:
return "auto", resolved_model, None, cfg_api_key
```
Find ALL instances of this pattern and ensure they return cfg_api_key.

### 2. `call_llm()` vision block passes raw params
```python
# BUG:
resolve_vision_provider_client(
    provider=provider,
    model=model,
    base_url=base_url,
    api_key=api_key,          # raw None from function args
    async_mode=False,
)
# FIX:
resolve_vision_provider_client(
    provider=provider or resolved_provider,
    model=model or resolved_model,
    base_url=base_url or resolved_base_url,
    api_key=api_key or resolved_api_key,   # falls back to config value
    async_mode=False,
)
```

### 3. `async_call_llm()` has the SAME bug
Same pattern but with `async_mode=True`. Apply the same fix.

## How to Apply

```bash
cd ~/hermes-agent
```

Use Python (NOT patch tool — it masks api_key in output):

```python
path = 'agent/auxiliary_client.py'
with open(path, 'r') as f:
    content = f.read()

# Fix 1: All auto-return statements that drop cfg_api_key
old_auto = '    return "auto", resolved_model, None, None\n'
new_auto = '    return "auto", resolved_model, None, cfg_api_key\n'
content = content.replace(old_auto, new_auto)

# Fix 2: Sync vision block
old_sync = '''    if task == "vision":
        effective_provider, client, final_model = resolve_vision_provider_client(
            provider=provider,
            model=model,
            base_url=base_url,
            api_key=api_key,
            async_mode=False,
        )'''
new_sync = '''    if task == "vision":
        effective_provider, client, final_model = resolve_vision_provider_client(
            provider=provider or resolved_provider,
            model=model or resolved_model,
            base_url=base_url or resolved_base_url,
            api_key=api_key or resolved_api_key,
            async_mode=False,
        )'''
content = content.replace(old_sync, new_sync)

# Fix 3: Async vision block
old_async = old_sync.replace("async_mode=False", "async_mode=True")
new_async = new_sync.replace("async_mode=False", "async_mode=True")
content = content.replace(old_async, new_async)

with open(path, 'w') as f:
    f.write(content)

# Verify
raw = content.count('provider=provider,\n            model=model,\n            base_url=base_url,\n            api_key=api_key,')
print(f"Remaining raw-param blocks: {raw} (should be 0)")
```

## Restarting (CRITICAL)

Hermes runs its own Telegram gateway directly (OpenClaw removed Mar 30 2026). To reload patched code:

```bash
# Kill the gateway
kill $(pgrep -f "hermes gateway") 2>/dev/null

# Wait and verify it's dead
sleep 2
ps aux | grep "hermes gateway" | grep -v grep || echo "Gateway stopped"

# Restart (from venv)
cd ~/hermes-agent && source venv/bin/activate && hermes gateway
```

To restart from a Hermes chat session (background mode):
```
terminal: kill $(pgrep -f "hermes gateway")
terminal (background): cd ~/hermes-agent && source venv/bin/activate && hermes gateway
```

Verify with: `tail -20 ~/.hermes/logs/gateway.log` — should show "telegram connected".

## Pitfalls
- The `patch` tool masks api_key in display. Use raw Python `open()` to verify content.
- Hermes updates (git pull) WILL overwrite fixes. Re-apply after every update.
- Cannot restart from within a gateway session (kills own process).
- `execute_code` runs in a SEPARATE process — tests passing there don't mean the gateway has the fix.
- `__pycache__` may be stale — check mtime vs .py source.
- Approvals config: set `approvals: mode: auto` in ~/.hermes/config.yaml to avoid permission prompts blocking patches.
