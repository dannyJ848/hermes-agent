# Kimi/Moonshot Vision API Reference

Extracted from session May 9, 2026. Research on configuring Kimi vision for Hermes Agent.

## Endpoint

- **Base URL:** `https://api.moonshot.ai/v1`
- **NOT** `https://api.kimi.com/coding/v1` (coding endpoint, no vision)

## Vision-Capable Models

| Model | Vision | Video | Notes |
|-------|--------|-------|-------|
| `kimi-k2.6` | ✅ | ✅ | Latest, 256K context |
| `moonshot-v1-8k-vision-preview` | ✅ | ❌ | Legacy preview |
| `moonshot-v1-32k-vision-preview` | ✅ | ❌ | Legacy preview |
| `moonshot-v1-128k-vision-preview` | ✅ | ❌ | Legacy preview |
| `kimi-for-coding` | ❌ | ❌ | Coding model, no vision support |

## Authentication

- **Env var:** `MOONSHOT_API_KEY`
- **Key format:** `sk-kimi-...` (starts with `sk-`)
- **NOT** the same as `AUXILIARY_VISION_API_KEY` (that is the Z.AI/GLM key)

## Request Format

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.ai/v1"
)

# Encode image to base64
with open("image.png", "rb") as f:
    image_data = f.read()
image_url = f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}"

# Send request
completion = client.chat.completions.create(
    model="kimi-k2.6",
    messages=[
        {"role": "system", "content": "You are Kimi."},
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": "Describe the content of the image."}
            ]
        }
    ]
)
```

**CRITICAL:** `message.content` must be a JSON array (list of objects), NOT a serialized string.

## Error Codes

| Code | Meaning | Fix |
|------|---------|-----|
| 401 Invalid Authentication | Wrong key or key not set | Verify `MOONSHOT_API_KEY` env var |
| 404 Not Found | Wrong endpoint | Use `https://api.moonshot.ai/v1`, not coding endpoint |
| "exceeded model token limit" | Content serialized as string | Ensure `content` is array, not string |

## Hermes Config

```yaml
auxiliary:
  vision:
    provider: custom
    model: kimi-k2.6
    base_url: https://api.moonshot.ai/v1
    api_key_env: MOONSHOT_API_KEY
    timeout: 60
    extra_body: {}
    download_timeout: 30
```

## User Preference

**Do NOT use GLM for vision.** If Kimi doesn't work, disable vision and wait for Qwen 27B vision capability.

## Related

- `AUXILIARY_VISION_API_KEY` = Z.AI/GLM key (not Moonshot)
- `GLM_API_KEY` = same Z.AI key
- `MOONSHOT_API_KEY` = separate Kimi key (starts with `sk-`)
