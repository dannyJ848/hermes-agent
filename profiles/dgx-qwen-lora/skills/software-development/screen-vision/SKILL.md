---
name: screen-vision
description: Full pipeline for seeing and understanding the user's screen. Screenshot + OCR + Vision AI analysis.
version: 1.0
---

# Screen Vision Pipeline

## When to Use
- User asks "what's on my screen", "can you see this", "what am I looking at"
- Need to verify what's displayed, check for UI issues, or read visible text
- Debugging UI problems, checking app state, or monitoring for changes

## The Pipeline (3 Steps)

### Step 1: Capture
```bash
# Option A: Direct (fastest)
screencapture -x /tmp/screen_vision_last.png

# Option B: Via screen_vision script
cd ~/subconscious/capabilities
/Users/dannygomez/hermes-agent/venv/bin/python3 screen_vision.py capture
```

### Step 2: See (Vision Analysis)
Use the `vision_analyze` tool with the screenshot path:
- image_url: `/tmp/screen_vision_last.png` (or path returned by capture)
- question: Be specific about what you want to know

Example:
```
vision_analyze(
  image_url="/tmp/screen_vision_last.png",
  question="Describe all open windows, visible text, and what the user is doing"
)
```

### Step 3: OCR (Optional — for text extraction)
```bash
# Via script
cd ~/subconscious/capabilities
/Users/dannygomez/hermes-agent/venv/bin/python3 screen_vision.py ocr

# Or direct
tesseract /tmp/screen_vision_last.png stdout -l eng
```

## Quick Reference

| Need | Action |
|------|--------|
| See what's on screen | screencapture + vision_analyze |
| Read text on screen | screencapture + tesseract OCR |
| Find specific text | screen_vision.py find "search term" |
| Monitor for changes | screen_vision.py monitor <seconds> |
| Screenshot a region | screencapture -x -R x,y,w,h /tmp/out.png |

## Critical Pitfalls (LEARNED THE HARD WAY)

### Tesseract/Leptonica CANNOT read from /tmp on macOS
`/tmp` is a symlink to `/private/tmp`. Leptonica's `fopenReadStream` fails on symlinked paths.
Fix: ALWAYS use `Path(path).resolve()` before passing to tesseract.

### Leptonica CANNOT read PNG files
The homebrew leptonica build has a broken libpng integration. PNG files will silently fail.
Fix: Convert to TIFF via Pillow before OCR:
```python
from PIL import Image
from pathlib import Path
img = Image.open(Path(png_path).resolve()).convert("RGB")
img = img.resize((1280, 720))  # downscale Retina for speed
tiff_path = str(Path("/tmp/output.tiff").resolve())
img.save(tiff_path)
# Then: tesseract <tiff_path> stdout -l eng
```
Both fixes are required. Without EITHER one, tesseract returns empty output with no error message.

### vision_analyze FAILS on Local Files (CRITICAL)
The built-in `vision_analyze` tool CANNOT read local file paths reliably. It returns "Invalid image source" or "I don't see any image" for `/tmp/*.png`, desktop screenshots, and downloaded files — even when the file exists and is valid. DO NOT waste calls trying different paths or workarounds.

**For local files, ALWAYS use `local_vision.py` as the primary path:**
```bash
python3 ~/subconscious/local_vision.py analyze /path/to/image.png "Describe this"
```
GLM-5V-turbo is reliable (~12s/call) and handles all local image formats.

Only use `vision_analyze` for HTTP/HTTPS URLs that are publicly accessible.

### OCR vs Vision
- `local_vision.py` (GLM-5V-turbo) — PRIMARY path for ALL local images. Reliable, fast, no conversion needed.
- `vision_analyze` — ONLY for public HTTP/HTTPS URLs. Fails on local paths.
- `tesseract` OCR — SECONDARY path for raw text extraction. Always requires TIFF conversion.
- When someone asks "what's on my screen", prefer screencapture + local_vision.py.

## AXUIElement — Getting UI Elements Without Vision

Apple's Accessibility API gives you element labels, roles, and (sometimes) coordinates for FREE — no vision model needed. This is the OmniParser approach but zero-cost.

### Setup
```bash
/Users/dannygomez/hermes-agent/venv/bin/python3 -m pip install pyobjc-framework-ApplicationServices
```

### Critical: 3-Argument Signature
`AXUIElementCopyAttributeValue` requires **3 arguments** in pyobjc, not 2:
```python
from ApplicationServices import *

# WRONG — TypeError: argument 2 must be None or objc.NULL
err, val = AXUIElementCopyAttributeValue(elem, kAXTitleAttribute)

# CORRECT — third arg is None (output pointer placeholder)
err, val = AXUIElementCopyAttributeValue(elem, kAXTitleAttribute, None)
```
Every call to this function needs `, None)` as the third arg. No exceptions.

### Getting the Frontmost App
```python
import subprocess
r = subprocess.run(['osascript', '-e',
    'tell application "System Events" to get unix id of first application process whose frontmost is true'],
    capture_output=True, text=True, timeout=5)
pid = int(r.stdout.strip().split(',')[0].strip())
app = AXUIElementCreateApplication(pid)
```

### Safari/WebKit Limitation
Safari's AX tree returns elements (buttons, text fields, links) with correct roles and labels, but **positions are all (0,0)**. WebKit doesn't expose pixel positions via accessibility. Solution: use AXUIElement for element discovery (what's on screen) + `vision_analyze` with `annotate=true` for coordinates (where things are).

### Correct Architecture: AX + Vision Hybrid
1. `AXUIElement` → discover what elements exist (labels, roles, values)
2. `vision_analyze` with `annotate=true` → get numbered coordinate overlays
3. Cross-reference: match AX labels to annotated coordinates
4. Click using the coordinates from vision

### Sanitizing AX Output
AX element strings can contain invalid Unicode that breaks JSON serialization:
```python
def safe_str(s):
    try:
        return str(s).encode('utf-8', errors='replace').decode('utf-8')[:100]
    except:
        return ""
```

### Useful AX Roles
`AXButton`, `AXTextField`, `AXTextArea`, `AXStaticText`, `AXLink`, `AXCheckBox`, `AXRadioButton`, `AXMenu`, `AXMenuItem`, `AXTab`, `AXScrollBar`, `AXImage`, `AXWindow`

## Vision Pipeline v2 (Unified)
The unified pipeline at `~/subconscious/capabilities/vision_pipeline.py` combines:
- **On-demand capture** (no daemon, no background process)
- **AXUIElement parsing** for element discovery
- **Quartz CGEvent** for scrolling (pyobjc-framework-Quartz)
- **cliclick** for clicking and typing
- **Hash-based diff** for change detection between frames

Commands: `see`, `elements`, `ocr`, `click`, `click_element`, `navigate`, `scroll`, `type`, `key`, `focus`, `window`, `diff`, `health`

## GLM-5V-turbo Direct Vision (Fallback/Batch)

When `vision_analyze` tool is unavailable or for batch/scripted use, `~/subconscious/local_vision.py` provides direct GLM-5V-turbo vision via the BigModel API. This is the ONLY reliable vision model — all glm-4v variants return "model not found".

```bash
# One-shot capture + analyze (auto-loads GLM_API_KEY from ~/.hermes/.env)
python3 ~/subconscious/local_vision.py capture_analyze "What's on screen?"

# Capture only
python3 ~/subconscious/local_vision.py capture

# Analyze existing image
python3 ~/subconscious/local_vision.py analyze /path/to/image.png "Describe this"

# Continuous watch loop (every 30s)
python3 ~/subconscious/local_vision.py watch 30

# Region capture
python3 ~/subconscious/local_vision.py region <x> <y> <w> <h>
```

Screenshots saved to `~/.hermes/local_vision/`, auto-cleanup keeps last 20. Analysis JSON saved alongside each PNG.

GLM-5V-turbo specs: ~13s/call, excellent at UI screenshots/code/diagrams/photos. API endpoint: `https://open.bigmodel.cn/api/paas/v4/chat/completions`, model: `glm-5v-turbo`.

## CRITICAL: vision_analyze FAILS on Local Files (Apr 2026)
The built-in `vision_analyze` tool does NOT reliably work with local file paths. It returns "Invalid image source" or "no image attached" errors on `/tmp/*.png`, `/tmp/*.jpg`, and even Desktop paths. This was confirmed across 10+ attempts with different paths and formats.

**RELIABLE PATH**: Always use `local_vision.py` for local image analysis:
```bash
/Users/dannygomez/hermes-agent/venv/bin/python3 ~/subconscious/local_vision.py analyze /path/to/image.png "your question"
```
GLM-5V-turbo via local_vision.py works on every image format, every path, every time (~12s/call).

**Only use `vision_analyze`** for HTTP/HTTPS URLs — it works fine for those. For local files, always go to local_vision.py.

## CRITICAL: Vision Provider Landscape (May 2026)

**Current state: NO reliable cloud vision provider available.**

| Provider | Model | Status | Why |
|----------|-------|--------|-----|
| GLM/Z.AI | `glm-5v-turbo` | ❌ REMOVED | User directive: "remove the glm" |
| Kimi Coding | `kimi-for-coding` | ❌ No vision | Coding endpoint has no image support |
| Moonshot | `kimi-k2.6` | ❌ 401 auth | Requires separate MOONSHOT_API_KEY, not configured |
| Qwen 27B | `Qwen/Qwen2.5-VL-72B-Instruct` | ⏳ Training | Step 5320/10000, ETA ~26h on DGX |

**Working alternatives RIGHT NOW:**
1. `browser_vision` — for web pages only (91% success after playwright install)
2. `screencapture` + manual user review — save screenshots, user describes them
3. Wait for Qwen 27B deployment on DGX Spark

**Config when Qwen is ready:**
```yaml
auxiliary:
  vision:
    provider: custom
    model: Qwen/Qwen2.5-VL-72B-Instruct  # or whatever checkpoint is trained
    base_url: http://spark-85e8.local:8000/v1
    api_key_env: NONE  # local vLLM, no key needed
```

**Historical config (GLM, removed per user directive):**
```yaml
# DO NOT USE — kept for reference only
auxiliary:
  vision:
    provider: custom
    model: glm-5v-turbo
    base_url: https://api.z.ai/api/paas/v4
    api_key_env: GLM_API_KEY
```

## CRITICAL: Headless Chromium WebGL Compatibility (May 2026)
`MeshPhysicalMaterial` (three.js r128) crashes headless chromium with `uniform3fv` error. **Use `MeshPhongMaterial` or `MeshLambertMaterial`** for WebGL compatibility in browser_vision screenshots.

This affects any 3D web content being captured via browser tools — always use simpler materials for headless rendering. See also: `web/references/headless-browser-compatibility.md`.

## CRITICAL: Playwright Version Pinning for Browser Tools (May 2026)
Hermes expects `chromium_headless_shell-1217` but `playwright install chromium` may install a different build. **Always use `npx playwright install`** (not bare `playwright install`) to match the version in hermes's playwright dependency.

After installation, verify with:
```bash
ls ~/Library/Caches/ms-playwright/chromium_headless_shell-1217/
```

See also: `web/references/headless-browser-compatibility.md`.

## Hermes Hands — Full GUI Automation (May 2026)

The `~/subconscious/hermes_hands.py` module provides complete hands control for macOS:
- `screen()` — capture screenshot
- `click(x, y)` — click at coordinates
- `type(text)` — type text
- `key(key_name)` — press special keys
- `scroll(direction, amount)` — scroll
- `open_app(name)`, `close_app(name)`, `focus_app(name)` — app control
- `get_mouse_pos()` — get cursor position
- `analyze_screen(prompt)` — placeholder until vision enabled

**CRITICAL: Without vision, hands is BLIND.**
- Clicks use approximate coordinates — may miss buttons
- No verification that actions succeeded
- Screenshots are saved but cannot be analyzed automatically
- **Pattern**: Capture → Save → Ask user to verify → Act on user's description

Requires: `brew install cliclick` (macOS GUI automation tool)

See: `~/subconscious/hermes_hands.py` (live module) or `scripts/hermes_hands.py` (skill reference copy).

## General Notes
- Screenshots go to `/tmp/screen_vision_last.png` by default
- The `vision_analyze` tool is a BUILT-IN Hermes tool — but BROKEN for local files
- For multi-monitor: `screencapture -x -D <display_num>` (1-indexed)
- For window-specific: use browser_vision if it's a browser tab
- Screenshots are ~2.5MB at 2560x1440 resolution
- Files with spaces in paths: use `find ... -exec cp {} /tmp/clean_name.png \;` to copy to a simple path first
