# Vision Provider Landscape — May 2026

## Working Configurations

### Browser Vision (Web Pages Only)
```yaml
browser:
  cloud_provider: browserbase  # or local
```
- **Success rate**: 91%
- **Requires**: `npx playwright install chromium` (v1217)
- **Limitation**: Only works for HTTP/HTTPS URLs, not local files

### GLM-5V-turbo (REMOVED per user directive)
```yaml
# DO NOT USE — reference only
auxiliary:
  vision:
    provider: custom
    model: glm-5v-turbo
    base_url: https://api.z.ai/api/paas/v4
    api_key_env: GLM_API_KEY
```
- Was working but user said: "no remove the glm"
- `GLM_API_KEY` = `AUXILIARY_VISION_API_KEY` (same Z.AI/BigModel key)

## Failed Configurations

### Kimi-for-coding
```yaml
auxiliary:
  vision:
    provider: kimi-coding
    model: kimi-for-coding
    base_url: https://api.kimi.com/coding/v1
```
- **Error**: 404 "resource not found"
- **Root cause**: Coding endpoint has no vision support

### Kimi-k2.6 (Moonshot)
```yaml
auxiliary:
  vision:
    provider: custom
    model: kimi-k2.6
    base_url: https://api.moonshot.ai/v1
    api_key_env: MOONSHOT_API_KEY
```
- **Error**: 401 "Invalid Authentication"
- **Root cause**: `MOONSHOT_API_KEY` is different from `GLM_API_KEY`. The env var starts with `sk-` but may not be valid for moonshot.ai endpoint. `AUXILIARY_VISION_API_KEY` is the Z.AI key, not moonshot.

## API Key Landscape

```
GLM_API_KEY              = 15e9252c363241a...  (Z.AI/BigModel)
AUXILIARY_VISION_API_KEY = 15e9252c363241a...  (SAME as GLM_API_KEY)
MOONSHOT_API_KEY         = sk-...               (Different provider!)
KIMI_API_KEY             = (empty)              (Not set)
```

## Future: Qwen 27B Local Vision

When training completes (~26h from May 9):
```yaml
auxiliary:
  vision:
    provider: custom
    model: Qwen/Qwen2.5-VL-72B-Instruct
    base_url: http://spark-85e8.local:8000/v1
    api_key_env: NONE  # local vLLM
```

## Decision Rule

| Need | Provider | Config |
|------|----------|--------|
| Web page analysis | browser_vision | Built-in tool |
| Local screenshot + user describes | screencapture | Manual review |
| Local screenshot + AI describes | ⏳ Wait for Qwen | None available now |
