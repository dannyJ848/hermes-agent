---
name: hermes-vision-provider-setup
description: Wire a new vision model into Hermes Agent's auxiliary vision pipeline. Covers config.yaml setup, auxiliary_client.py provider registration, endpoint resolution debugging, and screenshot-based vision testing.
version: "1.0"
---

# Hermes Vision Provider Setup

Wire a new vision-capable model into Hermes so `vision_analyze` and `browser_vision` use it.

## When to Use

- Adding a new vision model (e.g. GLM-5V-Turbo, Qwen-VL, LLaVA)
- Switching vision providers (e.g. from OpenRouter to direct API)
- Debugging vision 401/429/timeout errors
- After Hermes updates that change auxiliary_client.py

## Step 1: Identify the Correct API Endpoint

**CRITICAL:** Many providers have SEPARATE endpoints for coding vs model API.

| Provider | Coding Endpoint | Model/Chat Endpoint | Vision Endpoint |
|----------|----------------|-------------------|-----------------|
| Z.AI | /api/coding/paas/v4/ | /api/paas/v4/ | /api/paas/v4/ (same as model) |
| OpenAI | api.openai.com (same) | api.openai.com (same) | api.openai.com (same) |
| OpenRouter | openrouter.ai/api/v1/ | openrouter.ai/api/v1/ (same) | openrouter.ai/api/v1/ (same) |
| **Moonshot/Kimi** | **N/A** | **https://api.moonshot.ai/v1** | **https://api.moonshot.ai/v1** |

Vision models typically live on the **model/chat API**, NOT the coding API.
**Exception:** Kimi-for-coding (the coding model) does NOT support vision. Use `kimi-k2.6` on `https://api.moonshot.ai/v1` with `MOONSHOT_API_KEY`.

Check the provider's docs: look for "Chat Completion" or "Vision" endpoint.

## Step 2: Register the Vision Model

### Option A: Config-only (if provider already supported)

Edit `~/.hermes/config.yaml`:

**For Z.AI GLM Vision (legacy):**
```yaml
auxiliary:
  vision:
    provider: custom
    model: glm-5v-turbo
    base_url: https://api.z.ai/api/paas/v4/
    api_key_env: GLM_API_KEY
    timeout: 60
```

**For Moonshot/Kimi K2.6 Vision:**
```yaml
auxiliary:
  vision:
    provider: custom
    model: kimi-k2.6
    base_url: https://api.moonshot.ai/v1
    api_key_env: MOONSHOT_API_KEY
    timeout: 60
```

**IMPORTANT:** `kimi-for-coding` does NOT support vision. Use `kimi-k2.6`.
## GLM-5V-Turbo (Z.AI) Vision Setup

When using GLM-5V-Turbo via Z.AI general API endpoint:

```yaml
auxiliary:
  vision:
    provider: custom
    model: glm-5v-turbo
    base_url: https://api.z.ai/api/paas/v4/
    api_key: <your-key>
    timeout: 60
```

**CRITICAL PITFALL — Reasoning Tokens:**
GLM-5V-Turbo consumes tokens internally for "reasoning" before generating visible output. The API response shows `completion_tokens_details.reasoning_tokens` (often 150-250 tokens) which are NOT part of the visible response. This means:

- A request with `max_tokens=100` may return empty content because all tokens went to reasoning
- You need `max_tokens >= 500` to get any visible output after reasoning
- The visible response may be much shorter than the token count suggests
- If testing vision and getting empty responses, **increase max_tokens first** before debugging the API key or image format

**Verification test:**
```python
from openai import OpenAI
client = OpenAI(base_url="https://api.z.ai/api/paas/v4/", api_key="...")
resp = client.chat.completions.create(
    model="glm-5v-turbo",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What is this image? One word."},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
        ]
    }],
    max_tokens=500  # Must be high enough for reasoning + output
)
print(resp.choices[0].message.content)
print("Reasoning tokens:", resp.usage.completion_tokens_details.reasoning_tokens)
```

## User Preference

User prefers GLM-5V-Turbo for vision when available. Fallback preference: disable vision and wait for Qwen 27B if GLM fails.

### Option B: Provider-level registration (cleaner, survives updates)

Edit `~/hermes-agent/agent/auxiliary_client.py`:

1. Add vision model to `_PROVIDER_VISION_MODELS` (~line 113):
```python
_PROVIDER_VISION_MODELS: Dict[str, str] = {
    "xiaomi": "mimo-v2-omni",
    "zai": "glm-5v-turbo",    # Add your provider
}
```

2. If provider is new, add to `hermes_cli/providers.py` with auth env vars:
```python
"myprovider": HermesOverlay(
    transport="openai_chat",
    extra_env_vars=("MYPROVIDER_API_KEY",),
    base_url_env_var="MYPROVIDER_BASE_URL",
),
```

## Step 3: Handle API Key Resolution

The `_resolve_task_provider_model()` function (~line 2031) has this priority:
1. Explicit args (function params)
2. Config file (auxiliary.vision.provider/model/base_url/api_key)
3. "auto" detection

**Key gotcha:** When `cfg_base_url` is set, it forces provider="custom" and uses `cfg_api_key`.
If `api_key: ''` in config, cfg_api_key becomes None, and "custom" provider tries `OPENAI_API_KEY` env var.

**Solutions:**
- **Best:** Use provider-level registration (Option B) — provider resolves its own key from env vars
- **Fallback:** Put the actual API key in config.yaml `api_key` field
- **Hack:** Set `OPENAI_API_KEY` env var to the provider's key (conflicts with real OpenAI)

## Step 4: Clear Cache and Test

```bash
# Clear Python cache
find ~/hermes-agent -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# Test with local screenshot
screencapture -x /tmp/test_vision.png
```

Then in session:
```
vision_analyze(image_url="/tmp/test_vision.png", question="What do you see?")
```

### Common Error Codes

| Error | Cause | Fix |
|-------|-------|-----|
| 401 token expired | Wrong API key or wrong endpoint | Check key + verify base_url is model API not coding API |
| 429 subscription plan | Model not available on your plan | Upgrade plan or use different model |
| 404 not found | Wrong endpoint URL | Check provider docs for correct chat completions URL |
| Timeout | Model too slow or image too large | Increase timeout in config, resize image |

## Step 5: Verify Provider Resolution

Debug which provider/model actually resolved:
```python
# In a test script
from agent.auxiliary_client import resolve_vision_provider_client
provider, client, model = resolve_vision_provider_client()
print(f"Provider: {provider}, Model: {model}")
print(f"Base URL: {client.base_url if client else 'None'}")
```

## GLM-5V-Turbo Vision Setup

See `references/glm-5v-turbo-setup.md` for:
- Correct config (general Z.AI endpoint, not coding endpoint)
- Reasoning token pitfall (max_tokens must be >= 500)
- Verification test script
- API key format

## Screenshot-Based Vision Pipeline

For local diagram/visual analysis:

```bash
# 1. Open file in browser
open -a "Google Chrome" ~/Desktop/diagram.html

# 2. Wait for render, then screenshot
sleep 3 && screencapture -x /tmp/screenshot.png

# 3. Analyze with vision
vision_analyze(image_url="/tmp/screenshot.png", question="Describe what you see")
```

**Note:** `browser_navigate` blocks localhost URLs. The screenshot pipeline is the only reliable way to view local files.

## Kimi/Moonshot Vision Details

See `references/kimi-moonshot-vision-api.md` for:
- Correct endpoint (`https://api.moonshot.ai/v1` vs coding endpoint)
- Vision-capable models (`kimi-k2.6`, not `kimi-for-coding`)
- Request format (JSON array content, not string)
- Authentication (MOONSHOT_API_KEY vs AUXILIARY_VISION_API_KEY)
- Error codes and fixes

## Pitfalls

- **Coding API vs Model API:** Z.AI has two separate endpoints. Vision models are on Model API (/api/paas/v4/), NOT Coding API (/api/coding/paas/v4/). GLM_BASE_URL env var points to Coding API.
- **Kimi-for-coding ≠ vision:** The Kimi coding endpoint (`https://api.kimi.com/coding/v1`) does NOT support vision. Use `kimi-k2.6` on `https://api.moonshot.ai/v1`.
- **AUXILIARY_VISION_API_KEY is NOT a separate key:** This env var contains the same Z.AI key as GLM_API_KEY (starts with `15e9252c363241a`). It is NOT a Moonshot key.
- **Guardrail blocks repeated failures:** `vision_analyze` gets blocked after 3 identical failures with `repeated_exact_failure_block`. Change strategy (different model, different image, different question) instead of retrying.
- **api_key: '' is NOT the same as omitting it:** Empty string gets stripped to None, which means "no key" for custom provider.
- **__pycache__ must be cleared** after any changes to auxiliary_client.py or config.yaml.
- **Upstream updates will overwrite** provider-level changes. Re-apply after `git pull`.
- **browser_navigate blocks file:/// and localhost** — always use screencapture + vision_analyze instead.
- **vision_analyze needs a URL or local file path**, not raw image data.
