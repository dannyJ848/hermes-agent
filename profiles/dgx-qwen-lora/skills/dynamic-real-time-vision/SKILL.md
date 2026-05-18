---
name: dynamic-real-time-vision
description: Visual Loop pattern for dynamic real-time screen navigation. See → Think → Act → Verify cycle for GUI interaction. Tested live Apr 4 2026.
version: 3.0
---

# Dynamic Real-Time Vision (Visual Loop)

## The Pattern

Every visual navigation task follows this cycle:

```
CAPTURE → DESCRIBE → PLAN → ACT → VERIFY → (repeat)
```

## Tool Chain

| Step | Tool | Purpose |
|------|------|---------|
| CAPTURE | `visual_loop.py capture` | Screenshot to /tmp/visual_loop_current.png |
| DESCRIBE | `vision_analyze` | See screen + describe what's visible |
| PLAN | LLM reasoning | Decide next action based on visual context |
| ACT | `visual_loop.py click/scroll/type/key` OR AppleScript | Execute action |
| VERIFY | `vision_analyze` | Confirm action had intended effect |

## Commands Reference

All via: `cd ~/subconscious/capabilities && /Users/dannygomez/hermes-agent/venv/bin/python3 visual_loop.py <command>`

| Command | Args | Description |
|---------|------|-------------|
| `capture` | | Screenshot + metadata |
| `click` | x y | Click coordinates |
| `double_click` | x y | Double click |
| `right_click` | x y | Right click |
| `type` | "text" | Type text |
| `key` | key_name | Press key (enter, tab, esc, etc.) |
| `key_combo` | key1 key2 | Key combo (cmd t, cmd c, etc.) |
| `scroll` | down/up amount | Scroll (uses Quartz CGEvent) |
| `drag` | x1 y1 x2 y2 | Drag element |
| `focus` | app_name | Bring app to front |
| `active_window` | | Get active window info |
| `wait` | seconds | Wait for UI update |

## PITFALLS — Lessons from Live Testing (Apr 4 2026)

### 1. ALWAYS Click Inside Content Area Before Scrolling
Scroll events (Quartz CGEvent) go to whatever has OS focus. If you focused an app but the terminal/desktop has hover focus, scrolls go THERE. 

**FIX:** Always click the center of the browser content area (e.g., x=800 y=600) BEFORE any scroll operation. Then scroll immediately.

### 2. Vision Coordinates Are IMPRECISE
`vision_analyze` returns approximate coordinates from descriptions. They're often 50-100px off. Clicking "the Notifications bell at x=295, y=205" may click outside the window entirely.

**FIX:** For navigation to known URLs, use AppleScript instead of visual clicking:
```bash
osascript -e 'tell application "Safari" to set URL of document 1 to "https://x.com/Teknium"'
```
This is faster, more reliable, and doesn't waste vision cycles.

### 3. cliclick Key Names, Not Keycodes
cliclick uses NAMED keys, not keycodes: `return`, `enter`, `space`, `tab`, `esc`, `arrow-up`, `arrow-down`, NOT keycodes like `36` or `125`. The `key_combo` action in visual_loop.py handles this via AppleScript.

### 4. browser_vision Is NOT the Desktop
`browser_vision` connects to a Browserbase cloud session — it CANNOT see your actual desktop Safari. Use `vision_analyze` with the screenshot path instead:
```
vision_analyze(image_url="/tmp/visual_loop_current.png", question="...")
```

### 5. Tesseract OCR Requires Workarounds on macOS
Tesseract/leptonica CANNOT read PNGs and CANNOT read from /tmp (symlink to /private/tmp). Use screen_vision.py which handles the TIFF conversion + Path.resolve() automatically:
```bash
cd ~/subconscious/capabilities && /Users/dannygomez/hermes-agent/venv/bin/python3 screen_vision.py ocr
```

### 6. Focus Issues — Clicks May Land on Desktop
If a click seems to do nothing, you may have clicked outside the app window (especially with imprecise vision coordinates). The click "succeeds" but hits the desktop wallpaper. Always verify with a follow-up capture.

## Best Practice Workflow

### For Navigation to Known URLs:
```
1. osascript -e 'tell application "Safari" to set URL of document 1 to "URL"'  (fastest, most reliable)
2. wait 3
3. visual_loop.py capture
4. vision_analyze — read the results
5. If need to scroll: click center of content area first, then scroll
```

### For Exploring Unknown UI:
```
1. visual_loop.py focus <app>
2. visual_loop.py capture
3. vision_analyze — identify elements and their approximate locations
4. visual_loop.py click <x> <y> — try the coordinates
5. wait 1
6. visual_loop.py capture
7. vision_analyze — verify what happened
8. If wrong: use AppleScript fallback or try different coordinates
```

### For Scrolling Through Content:
```
1. visual_loop.py click 800 600  — focus the content area
2. visual_loop.py scroll down 5  — scroll multiple times
3. wait 1
4. visual_loop.py capture
5. vision_analyze — read new content
6. Repeat steps 2-5
```

## AXUIElement Integration (macOS Accessibility API)

Apple's AXUIElement gives you UI element labels and roles FOR FREE — no vision model needed. This is the OmniParser approach but zero-cost.

### Setup
```bash
/Users/dannygomez/hermes-agent/venv/bin/python3 -m pip install pyobjc-framework-ApplicationServices
```

### API Signature — CRITICAL
```python
from ApplicationServices import (
    AXUIElementCreateApplication, AXUIElementCopyAttributeValue,
    kAXChildrenAttribute, kAXRoleAttribute, kAXTitleAttribute,
    kAXPositionAttribute, kAXSizeAttribute, kAXValueAttribute,
    kAXMainWindowAttribute, kAXDescriptionAttribute
)

# MUST pass 3 args: (element, attribute, None)
# NOT 2 args — that raises TypeError: "argument 2 must be None or objc.NULL"
err, value = AXUIElementCopyAttributeValue(elem, kAXRoleAttribute, None)
```

### Get Frontmost App PID
```python
import subprocess
r = subprocess.run(['osascript', '-e', 'tell application "System Events" to get unix id of first application process whose frontmost is true'], capture_output=True, text=True)
pid = int(r.stdout.strip().split(',')[0].strip())
```

### Walk Element Tree
```python
app = AXUIElementCreateApplication(pid)
err, window = AXUIElementCopyAttributeValue(app, kAXMainWindowAttribute, None)
err, children = AXUIElementCopyAttributeValue(window, kAXChildrenAttribute, None)
for child in children:
    _, role = AXUIElementCopyAttributeValue(child, kAXRoleAttribute, None)
    _, title = AXUIElementCopyAttributeValue(child, kAXTitleAttribute, None)
```

### Key Limitations (LEARNED THE HARD WAY)
1. ~~**Safari/WebKit returns positions as 0,0**~~ → **SOLVED: Use Safari JS `getBoundingClientRect()` instead** (see below).
2. **Terminal.app still returns 0,0 positions** — AX limitation. Use vision_analyze for Terminal.
3. **JSON sanitization REQUIRED** — AX returns bad unicode (e.g. `\\uXXXX` with invalid sequences). Use `str(s).encode('utf-8', errors='replace').decode('utf-8')` on all string values.
4. **Cap element count at ~40** — AX trees can be enormous. Limit to prevent multi-second JSON serialization.

### Safari JavaScript — EXACT Pixel Coordinates (BREAKTHROUGH Apr 2026)

Safari web content DOES expose exact coordinates, but NOT through AXUIElement. Instead, use AppleScript to execute JavaScript in the active tab:

**Prerequisites (one-time setup):**
```bash
defaults write com.apple.Safari AllowJavaScriptFromAppleEvents 1
defaults write com.apple.Safari IncludeDevelopMenu 1
```

**Get all interactive elements with exact coordinates:**
```bash
# Helper script at /tmp/get_elements.sh:
osascript -e 'tell application "Safari" to do JavaScript "JSON.stringify(Array.from(document.querySelectorAll(\"a, button, input, select, textarea, [role=button], [role=link], [role=tab]\")).slice(0,40).map((e,i)=>({i:i, tag:e.tagName, text:(e.textContent||\"\").slice(0,50), href:e.href||\"\", x:Math.round(e.getBoundingClientRect().x), y:Math.round(e.getBoundingClientRect().y), w:Math.round(e.getBoundingClientRect().width), h:Math.round(e.getBoundingClientRect().height)})))" in document 1'
```

**Result:** Returns JSON array with `{tag, text, href, x, y, w, h}` for every visible element — EXACT pixel coordinates. No vision model needed. Zero cost. This is OmniParser-level precision for FREE.

**Tested:** 33 elements detected on UWorld medical platform with sub-pixel accuracy.

**Limitation:** Only works when Safari is frontmost with a web page loaded. Falls back to AXUIElement for native apps.

### Set-of-Mark (SoM) Annotation Engine

The SoM engine (`~/subconscious/capabilities/som.py`) combines Safari JS detection with Pillow annotation to produce numbered bounding boxes on screenshots — identical to Microsoft OmniParser's approach.

**Commands:**
```bash
cd ~/subconscious/capabilities
VENV=/Users/dannygomez/hermes-agent/venv/bin/python3

$VENV som.py annotate          # Full pipeline: capture → detect → annotate
$VENV som.py annotate_with PATH # Annotate existing screenshot
$VENV som.py lookup N          # Get coordinates for mark number N
$VENV som.py click N           # Click on mark number N
$VENV som.py health            # Check dependencies
```

**Architecture:**
1. Safari JS detects web elements with exact coords (or AXUIElement for native apps)
2. Pillow draws numbered colored bounding boxes on screenshot
3. Saves to `/private/tmp/vision_annotated.png` + `/tmp/vision_marks.json`
4. Vision model sees numbered boxes → returns "click [5]" instead of guessing coordinates
5. `som.py lookup 5` returns exact center coordinates for clicking

**Workflow for complex UI interaction:**
```
1. som.py annotate → get annotated screenshot with 30+ numbered elements
2. vision_analyze(image_url="/private/tmp/vision_annotated.png") → LLM picks the right element number
3. som.py click N → precise click on the element center
4. Wait + capture to verify
```

### Correct Architecture (Updated Apr 2026)
```
Safari JS getBoundingClientRect() for WEB (exact coords, free)
     OR
AXUIElement for NATIVE APPS (labels + roles, position only for non-web)
     +
Pillow SoM annotation (numbered boxes on screenshot for LLM reference)
     +
vision_analyze (for elements that JS/AX can't detect: images, canvas, video)
     +
cliclick/Quartz for ACTION (click, scroll, type)
```

Three detection layers, each with clear strengths. Use the cheapest that works.

### Using vision_pipeline.py (Built-in Wrapper)
```bash
cd ~/subconscious/capabilities
VENV=/Users/dannygomez/hermes-agent/venv/bin/python3

$VENV vision_pipeline.py see          # Capture + parse elements
$VENV vision_pipeline.py elements     # Get elements without screenshot
$VENV vision_pipeline.py click_element "Button label"  # Click by description
$VENV vision_pipeline.py navigate https://x.com        # Navigate browser
$VENV vision_pipeline.py scroll down 5                 # Scroll with auto-focus
$VENV vision_pipeline.py health       # Check all deps
```

## When NOT to Use Visual Navigation

- **X/Twitter data** → Use `/tmp/x_scanner.py` API (10x faster, structured data)
- **Known URLs** → Use AppleScript `set URL` (instant, no vision needed)
- **Text extraction** → Use `screen_vision.py ocr` (direct, no visual loop needed)
- **Terminal commands** → Use `terminal` tool directly

## Performance Characteristics

- Single vision cycle: ~4-6 seconds (screenshot + vision_analyze + action)
- Full page navigation: ~90 seconds (12 cycles for X profile exploration)
- API equivalent: ~2 seconds for same X data
- Use visual loop ONLY when no API or direct method exists
