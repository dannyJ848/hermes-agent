# GLM-5V-Turbo Vision Setup

## Config

```yaml
auxiliary:
  vision:
    provider: custom
    model: glm-5v-turbo
    base_url: https://api.z.ai/api/paas/v4/
    api_key: <your-key>
    timeout: 60
    extra_body: {}
    download_timeout: 30
```

## Critical Pitfall: Reasoning Tokens

GLM-5V-Turbo consumes tokens internally for reasoning before generating visible output. The API response shows `completion_tokens_details.reasoning_tokens` (often 150-250 tokens) which are NOT part of the visible response.

This means:
- `max_tokens=100` may return empty content because all tokens went to reasoning
- You need `max_tokens >= 500` to get visible output after reasoning
- The visible response may be much shorter than the token count suggests
- Empty responses with `finish_reason="length"` usually means reasoning consumed all tokens

## Verification Test

```python
from openai import OpenAI
import base64

client = OpenAI(
    base_url="https://api.z.ai/api/paas/v4/",
    api_key="..."
)

with open("image.png", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

resp = client.chat.completions.create(
    model="glm-5v-turbo",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What is this image? One word."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
        ]
    }],
    max_tokens=500,  # Must be high enough for reasoning + output
    temperature=0.1
)

print("Content:", resp.choices[0].message.content)
print("Reasoning tokens:", resp.usage.completion_tokens_details.reasoning_tokens)
print("Completion tokens:", resp.usage.completion_tokens)
```

## Endpoint Note

GLM-5V-Turbo uses the **general Z.AI API endpoint** (`/api/paas/v4/`), NOT the coding endpoint (`/api/coding/paas/v4/`). The coding endpoint is for code generation models and does not support vision.
