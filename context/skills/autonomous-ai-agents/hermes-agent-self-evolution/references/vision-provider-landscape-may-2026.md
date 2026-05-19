# Vision Provider Landscape — May 2026

## Current State: NO reliable cloud vision provider

| Provider | Model | Status | Why |
|----------|-------|--------|-----|
| GLM/Z.AI | `glm-5v-turbo` | ❌ REMOVED | User directive: "remove the glm" |
| Kimi Coding | `kimi-for-coding` | ❌ No vision | Coding endpoint has no image support |
| Moonshot | `kimi-k2.6` | ❌ 401 auth | Requires separate MOONSHOT_API_KEY, not configured |
| Qwen 27B | `Qwen/Qwen2.5-VL-72B-Instruct` | ⏳ Training | Step 5320/10000, ETA ~26h on DGX |

## Working Alternatives RIGHT NOW

1. **browser_vision** — for web pages only (91% success after playwright install)
2. **screencapture + manual user review** — save screenshots, user describes them
3. Wait for Qwen 27B deployment on DGX Spark

## Config When Qwen Is Ready

```yaml
auxiliary:
  vision:
    provider: custom
    model: Qwen/Qwen2.5-VL-72B-Instruct  # or whatever checkpoint is trained
    base_url: http://spark-85e8.local:8000/v1
    api_key_env: NONE  # local vLLM, no key needed
```

## API Key Landscape

```
GLM_API_KEY              = 15e9252c363241a...  (Z.AI/BigModel)
AUXILIARY_VISION_API_KEY = 15e9252c363241a...  (SAME as GLM_API_KEY)
MOONSHOT_API_KEY         = sk-...               (Different provider!)
KIMI_API_KEY             = (empty)              (Not set)
```

## Hands System Without Vision

The `~/subconscious/hermes_hands.py` module provides GUI automation but is **blind** without vision:
- Clicks use approximate coordinates — may miss buttons
- No verification that actions succeeded
- Pattern: `screen()` → save → ask user to verify → act on user's description

When Qwen vision is available, the loop becomes:
```
screen() → vision_analyze() → decision → click/type → screen() → verify
```

## Qwen Training Status

- Current: Step 5320/10000 (53.2%)
- Speed: ~20.2 sec/step
- ETA: ~26 hours
- Loss: 1.2457
- GPU: 62.6GB
- PID: 443609 on DGX Spark

When complete: deploy with vLLM, update hermes config, test vision_analyze.
