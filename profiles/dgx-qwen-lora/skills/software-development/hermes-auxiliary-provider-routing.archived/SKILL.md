---
name: hermes-auxiliary-provider-routing
description: Diagnose and fix Hermes auxiliary tasks (compression, title generation, web extract, session summary) silently failing because the configured provider's API endpoint doesn't speak OpenAI Chat Completions. Use when compaction, titles, or other side-tasks "appear broken" but the main agent works fine. Covers protocol mismatch detection, per-task provider routing in config.yaml, and verification.
version: 1.0
created: 2026-04-27
tags: [hermes, auxiliary, compression, title-generation, provider-routing, 404, kimi-coding, deepseek]
---

# Hermes Auxiliary Provider Routing

## Trigger

Use this skill when ANY of these symptoms appear:
- "Compaction is not working" / context keeps growing past threshold
- Sessions have no titles or default titles like "untitled"
- `Auxiliary <task> failed: HTTP 404` in logs
- `_last_summary_error` set on the compressor but main API calls succeed
- User just switched their main provider to Kimi-coding, Z.AI coding, GLM-coding, or another "agent-mode-only" endpoint
- Compressor test runs fine standalone but fails in live agent loop
- Vision/title/compression all 404 simultaneously after a config change

The pattern: **main agent works, side-tasks 404 silently**. This means the auxiliary client is routing to an endpoint that doesn't speak OpenAI Chat Completions.

## Why This Happens

Hermes has two API surfaces:
1. **Main agent loop** — uses provider-specific adapters (Anthropic, OpenAI, Codex Responses, etc.). Speaks whatever protocol the configured provider needs.
2. **Auxiliary client** (`agent/auxiliary_client.py`) — used by compression, title generation, web extract, vision, session summary. **Always speaks OpenAI Chat Completions** (`POST /v1/chat/completions`).

When you set your main provider to a "coding-only" endpoint:
- `api.kimi.com/coding` — speaks Anthropic Messages, requires `User-Agent: claude-code/0.1.0`
- `api.z.ai/api/coding/paas/v4` — coding-mode-only, restricted
- Some GLM coding endpoints — Anthropic-style

…and your auxiliary tasks default to the same provider, the auxiliary client tries to POST OpenAI-shaped requests to an Anthropic endpoint and gets **404 Not Found** (or 405, or empty 200s).

The logs show one warning per task per turn, easy to miss. The user-facing symptom is "compaction stopped working."

## Diagnosis (run in order)

### 1. Check what each auxiliary task is configured to use
```bash
grep -A 5 "^auxiliary:" ~/.hermes/config.yaml
```
Look at: `compression`, `title_generation`, `web_extract`, `vision`, `session_search`.
If any has `provider: kimi-coding`, `provider: zai-coding`, or any "/coding" endpoint, that task will 404.

### 2. Verify which protocol the suspect endpoint speaks
```bash
# Look for the endpoint detector in the codebase
grep -rn "_is_kimi_coding_endpoint\|_is_zai_coding\|_is_anthropic_endpoint" ~/hermes-agent/agent/
```
If the endpoint is matched in `_is_kimi_coding_endpoint()` or `_is_*_anthropic_endpoint()`, it does NOT speak OpenAI. Auxiliary calls will fail.

### 3. Reproduce the 404 directly
```python
import os
from pathlib import Path
# Load .env
for line in (Path.home() / '.hermes/.env').read_text().splitlines():
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        os.environ[k.strip()] = v.strip()

from openai import OpenAI
# Use the suspect base_url + key
client = OpenAI(base_url='https://api.kimi.com/coding', api_key=os.environ['KIMI_API_KEY'])
try:
    r = client.chat.completions.create(
        model='kimi-for-coding',
        messages=[{'role': 'user', 'content': 'hi'}],
        max_tokens=10,
    )
    print('OK')
except Exception as e:
    print(f'404 expected: {type(e).__name__}: {e}')
```
404 = confirmed protocol mismatch. The endpoint exists but doesn't have `/chat/completions`.

### 4. Test compression with a forced large conversation
```python
from agent.context_compressor import ContextCompressor
from agent.model_metadata import estimate_messages_tokens_rough

messages = [{'role': 'system', 'content': 'You are an agent.'}]
long_text = 'A' * 4000
for i in range(120):
    messages.append({'role': 'user', 'content': f'msg {i}: ' + long_text})
    messages.append({'role': 'assistant', 'content': f'resp {i}: ' + long_text})

tokens = estimate_messages_tokens_rough(messages)
comp = ContextCompressor(model='kimi-for-coding', threshold_percent=0.4,
                         protect_first_n=3, protect_last_n=20,
                         summary_target_ratio=0.25, quiet_mode=False)
print(f'should_compress: {comp.should_compress(tokens)}')
compressed = comp.compress(messages, current_tokens=tokens)
print(f'{len(messages)} -> {len(compressed)} messages')
print(f'_last_summary_error: {getattr(comp, "_last_summary_error", None)}')
```
If `_last_summary_error` contains "404" or "HTTP 4", the compression provider is wrong.

## Fix: Per-Task Provider Routing

Hermes supports per-task auxiliary overrides in `config.yaml`. Set each side-task to a provider that DOES speak OpenAI Chat Completions.

### Choosing an auxiliary provider

Pick one that:
- Speaks standard OpenAI `/v1/chat/completions`
- Has its API key in `~/.hermes/.env`
- Is fast/cheap (these tasks fire frequently)
- Can handle ~5K-50K input tokens (compression summaries)

Verified working as of Apr 2026:
- **DeepSeek** (`deepseek-v4-pro`, `deepseek-v4-flash`) — best balance, cheap, 256K context
- **OpenRouter free tier** (`google/gemma-4-26b-a4b-it:free`, `meta-llama/llama-3.3-70b-instruct:free`) — zero cost
- **Moonshot** (`api.moonshot.ai`, NOT `api.kimi.com/coding`) — different endpoint, speaks OpenAI
- **GLM standard** (`glm-4.6` via standard `api.z.ai/api/paas/v4`, NOT the coding endpoint)

### Patch config.yaml

```yaml
auxiliary:
  compression:
    provider: deepseek
    model: deepseek-v4-pro
    base_url: ''     # let provider registry resolve
    api_key: ''      # let provider registry resolve
    timeout: 120
  title_generation:
    provider: deepseek
    model: deepseek-v4-pro
    base_url: ''
    api_key: ''
    timeout: 30
  vision:
    provider: custom    # or your preferred vision provider
    model: glm-5v-turbo
  web_extract:
    provider: auto      # auto chain handles fallback
  session_search:
    provider: auto
```

**Rule of thumb:** main provider stays as-is (whatever you want for actual work). Side-tasks delegate to the cheapest OpenAI-compatible provider you have credentials for. Only override what the main provider CAN'T do.

### Verify each task end-to-end

```python
from agent.auxiliary_client import call_llm

# Title generation
r = call_llm(task='title_generation',
             messages=[{'role': 'system', 'content': 'Generate a short title.'},
                       {'role': 'user', 'content': 'debug compression'}],
             max_tokens=50, temperature=0.3, timeout=15)
print(f'title: {r.choices[0].message.content!r}')

# Compression summary
r = call_llm(task='compression',
             messages=[{'role': 'system', 'content': 'Summarize the conversation.'},
                       {'role': 'user', 'content': 'User asked X. Assistant did Y.'}],
             max_tokens=500, temperature=0.3, timeout=30)
print(f'summary: {r.choices[0].message.content[:80]}')
```

Both should return non-empty content. Empty strings = silent failure (the call succeeded but the model returned nothing — happens with certain models on simple prompts; switch to a different model).

### Verify in live agent

```python
from agent.title_generator import generate_title
title = generate_title(
    user_message='debug franken v8 model on DGX Spark',
    assistant_response='Checking the training pipeline...',
    timeout=15,
)
assert title and 'franken' in title.lower(), f'broken: {title!r}'
```

## Pitfalls

- **Don't set the auxiliary provider to your main "coding-only" provider** even if it has a fancy model. The auxiliary client speaks OpenAI; coding endpoints speak Anthropic. Will silently 404.
- **`provider: auto` falls back through a chain.** Useful for `web_extract` and `session_search`, but risky for `compression` and `title_generation` because the fallback chain might also include the broken provider. Set those explicitly.
- **Empty content !== success.** A 200 OK with empty `choices[0].message.content` means the model declined to respond — common with tiny models on `title_generation`. Verify content is non-empty, not just that the call didn't throw.
- **Compression latency matters.** DeepSeek v4-pro is accurate but takes ~15s for 100K-token compressions. For high-frequency sessions, switch to `deepseek-v4-flash` or an OpenRouter free model.
- **Restart Hermes after changing auxiliary config.** The auxiliary client caches resolved providers per-process. Kill gateway, kill current session, reopen.
- **Test in the actual gateway, not just standalone Python.** `auxiliary_client._resolve_task_provider_model()` reads from a different config object inside the gateway process. Standalone tests pass while gateway 404s.
- **Don't conflate this with LCM bloat.** If the LCM SQLite is also bloated (>20K messages, >100MB), fix that first — see `lcm-database-bloat-recovery`. The two failure modes look identical from the user's perspective ("compaction not working") but have different root causes.
- **Don't conflate this with the `current_tokens` bypass bug.** There's a third failure mode where the preflight check computes accurate tokens and passes them to `compress()`, but `compress()` ignores `current_tokens` and uses `self.last_prompt_tokens` instead. If `last_prompt_tokens` is 0 (no API usage yet, or usage not reported), `should_compress()` returns `False` and compression is skipped. The fix is in `agent/context_compressor.py` — ensure `compress()` passes `current_tokens` to `should_compress()`. See the code fix below.

## Third Failure Mode: `current_tokens` Ignored by `should_compress()`

Even when the preflight check and provider routing are correct, compression can still fail silently due to a parameter-passing bug in `ContextCompressor.compress()`.

### Symptom
- Preflight check prints `~148K tokens >= 104K threshold` — looks correct
- `_compress_context()` is called with `approx_tokens=148000`
- But compression returns immediately with no summary generated
- Context keeps growing despite being way past threshold

### Root Cause
`ContextCompressor.compress()` has a `current_tokens` parameter (the accurate preflight estimate), but the old code path called `should_compress()` with no arguments, which defaulted to `self.last_prompt_tokens`. If the API hadn't returned usage data yet (first turn, or provider doesn't report usage), `last_prompt_tokens` was 0, so `should_compress()` returned `False`.

The `current_tokens` parameter was passed into `compress()` but never used for the threshold check.

### Fix
In `agent/context_compressor.py`, modify `compress()` to use `current_tokens` for the `should_compress()` check:

```python
def compress(self, messages, current_tokens=None, focus_topic=None):
    n_messages = len(messages)
    # Use current_tokens (accurate preflight estimate) if provided,
    # otherwise fall back to last_prompt_tokens from API usage.
    _effective_tokens = current_tokens if current_tokens is not None else self.last_prompt_tokens

    # Check if compression is needed using the effective token count
    _needs_compress = self.should_compress(_effective_tokens)

    # Hard limit: if we have too many messages, force compression regardless of token count
    _HARD_MESSAGE_LIMIT = 500
    if n_messages > _HARD_MESSAGE_LIMIT and not _needs_compress:
        if not self.quiet_mode:
            logger.warning("Forcing compression: %d messages exceeds hard limit of %d", n_messages, _HARD_MESSAGE_LIMIT)
        _needs_compress = True

    if not _needs_compress:
        return messages

    return self._do_compress(messages, current_tokens, focus_topic)
```

**Key change:** `_effective_tokens = current_tokens if current_tokens is not None else self.last_prompt_tokens` — this ensures the accurate preflight estimate takes priority over the API usage fallback.

### How to Verify This Is Your Bug

```python
from agent.context_compressor import ContextCompressor

comp = ContextCompressor(model='kimi-for-coding', config_context_length=262144, threshold_percent=0.4, quiet_mode=True)
print(f'Threshold: {comp.threshold_tokens:,}')
print(f'last_prompt_tokens (uninitialized): {comp.last_prompt_tokens}')

messages = [{'role': 'user', 'content': f'Message {i}'} for i in range(50)]

# Test 1: Without fix behavior — current_tokens ignored, falls back to last_prompt_tokens=0
result1 = comp.compress(messages, current_tokens=148000)
print(f'With current_tokens=148000: {len(result1)} messages (should be < 50 if compression triggered)')

# Test 2: With last_prompt_tokens set above threshold
comp.last_prompt_tokens = 150000
result2 = comp.compress(messages, current_tokens=None)
print(f'With last_prompt_tokens=150000: {len(result2)} messages (should be < 50)')
```

If Test 1 returns 50 messages (no compression) but Test 2 compresses, you have the `current_tokens` bypass bug.

### When This Re-Triggers
- After `git pull` on hermes-agent (the fix may be reverted if upstream hasn't merged it)
- When switching to a provider that doesn't report `usage.prompt_tokens` in responses (some custom endpoints omit usage data)
- On the first turn of a new session (before any API call has returned usage data)

## When This Re-Triggers

Re-apply the fix after:
- Switching main provider (especially TO any `/coding` endpoint)
- `git pull` on hermes-agent (config.yaml may get reset by some updates)
- `hermes setup` re-run (overwrites auxiliary section)
- New auxiliary task added (vision, embedding, etc. — verify each one independently)

## Related Skills

- `lcm-database-bloat-recovery` — sister skill for the OTHER common compression failure (substrate bloat, not provider mismatch). Always check that first if symptoms include "database is locked".
- `hermes-vision-401-fix` — specifically about raw-params bug in auxiliary_client.py, different failure mode but same file.
- `hermes-endpoint-migration` — switching main endpoints generally; may surface this issue as a side effect.
- `hermes-provider-wiring` — adding NEW providers (this skill is about routing existing providers correctly).
