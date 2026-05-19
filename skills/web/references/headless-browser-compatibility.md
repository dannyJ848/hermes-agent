# Headless Browser Compatibility Notes

## Playwright Version Pinning (May 2026)

Hermes expects `chromium_headless_shell-1217`. The bare `playwright install chromium` may install a different version (e.g., `chromium-1140`).

**Correct command:**
```bash
npx playwright install chromium
```

This installs the version matching hermes's playwright dependency. Verify:
```bash
ls ~/Library/Caches/ms-playwright/chromium_headless_shell-1217/
```

## WebGL Material Compatibility in Headless Chromium (May 2026)

`MeshPhysicalMaterial` (three.js r128) crashes headless chromium with:
```
TypeError: Failed to execute 'uniform3fv' on 'WebGL2RenderingContext'
```

**Fix:** Use `MeshPhongMaterial` or `MeshLambertMaterial` instead.

Migration:
- Remove `roughness`, `metalness`, `clearcoat`, `sheen` properties
- Add `shininess` and `specular` equivalents
- Apply to all materials: myocardium, septum, blood, valves, vessels

This affects any 3D web content being captured via `browser_vision` or `browser_navigate`.

## file:// URL Limitations

Headless chromium blocks `file://` URLs for security. **Always serve files via HTTP:**
```bash
cd ~ && python3 -m http.server 8765 &
```
Then access via `http://localhost:8765/filename.html`.

## Vision API Configuration

The auxiliary vision provider in `~/.hermes/config.yaml`:
```yaml
auxiliary:
  vision:
    provider: custom
    model: glm-5v-turbo
    base_url: https://api.z.ai/api/paas/v4
    api_key_env: GLM_API_KEY
```

**Do NOT use kimi-for-coding for vision** — it doesn't support image input. The `AUXILIARY_VISION_API_KEY` is the same value as `GLM_API_KEY` (Z.AI key).

## Tool-Call Guardrail

After 3 identical failures on the same tool with same arguments, hermes blocks further calls. **Change strategy immediately** — do not retry unchanged. Inspect the error, try different parameters, or use an alternative tool.
