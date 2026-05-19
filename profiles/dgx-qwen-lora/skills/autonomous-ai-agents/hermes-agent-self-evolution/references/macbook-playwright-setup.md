# MacBook Playwright Setup — Version Mismatch Fix

## Problem

Hermes Agent browser tools (`browser_navigate`, `browser_vision`, `browser_click`) require a specific Playwright Chromium build. The system `playwright` binary (e.g., from conda at `/Users/dannygomez/opt/anaconda3/bin/playwright`) installs `chromium-1140`, but Hermes expects `chromium_headless_shell-1217`.

Error pattern:
```
browserType.launch: Executable doesn't exist at
/Users/dannygomez/Library/Caches/ms-playwright/chromium_headless_shell-1217/...
```

## Fix

Always use `npx playwright install chromium` (not bare `playwright install`):

```bash
# WRONG — installs wrong build for Hermes
playwright install chromium

# CORRECT — installs chromium_headless_shell-1217
npx playwright install chromium
```

`npx` ensures the Playwright version matching Hermes's Node dependency is used, which downloads the correct `chromium_headless_shell` build.

## Verification

```bash
ls ~/Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-mac-arm64
# Should exist after npx install
```

## Serving Local HTML Files

Hermes blocks `file://` URLs. Must serve via HTTP:

```bash
cd /path/to/html && python3 -m http.server 8765
# Then browser_navigate to http://localhost:8765/filename.html
```

## Headless WebGL Compatibility

Headless Chromium has limited WebGL support. Three.js `MeshPhysicalMaterial` crashes with:
```
TypeError: Failed to execute 'uniform3fv' on 'WebGL2RenderingContext'
```

**Fix:** Use `MeshPhongMaterial` or `MeshLambertMaterial` instead. Avoid `clearcoat`, `sheen`, `transmission` — these require full WebGL2 features unavailable in headless mode.

## Related
- `references/threejs-headless-compatibility.md` — Full material compatibility matrix
