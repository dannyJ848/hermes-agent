---
name: hermes-hands
description: GUI automation for Hermes Agent on macOS — screen capture, mouse/keyboard control, app management, and continuous vision loop. Enables autonomous screen interaction.
version: "1.0"
---

# Hermes Hands — GUI Automation

Full-screen GUI automation module for macOS. Provides screen capture, mouse/keyboard control, app opening/closing, and a continuous vision loop (capture → analyze → act → repeat).

## When to Use

- Opening/closing/focusing applications programmatically
- Clicking buttons, typing text, scrolling in GUI apps
- Capturing screenshots for visual verification
- Building autonomous vision loops (when vision model available)
- Automating repetitive UI tasks

## Prerequisites

- macOS with `screencapture`, `osascript`, `cliclick`
- `cliclick` installed: `brew install cliclick` (typically at `/opt/homebrew/bin/cliclick`)
- Accessibility permissions enabled for the terminal/IDE running Hermes

## Core Functions

### Screen Capture

```python
from tools.hands import HermesHands

hands = HermesHands()
path = hands.screen()  # Full screen → /tmp/hermes_screen_YYYYMMDD_HHMMSS.png
path = hands.screen(region="100,200,300,400")  # Region: x,y,w,h
```

### Mouse Control

```python
from tools.hands import HermesHands

hands = HermesHands()
hands.click(500, 300)          # Left click at (500, 300)
hands.dblclick(500, 300)     # Double click
hands.rightclick(500, 300)   # Right click
hands.drag(100, 100, 200, 200)  # Drag from (100,100) to (200,200)
pos = hands.get_mouse_pos()  # Returns (x, y) tuple
```

### Keyboard

```python
from hermes_hands import type_text, key

type_text("Hello World")  # Type string
key("escape")             # Press escape
key("enter")              # Press enter
key("tab")                # Press tab
key("space")              # Press space
```

### App Management

```python
from hermes_hands import open_app, close_app, focus_app, get_windows

open_app("Calculator")    # Launch application
close_app("Calculator")   # Quit application
focus_app("Terminal")   # Bring to front
windows = get_windows()   # List visible windows/apps
```

## Vision Integration

When a vision model is configured (see `hermes-vision-provider-setup`):

```python
from hermes_hands import screen, analyze_screen

# Capture and analyze
path = screen()
result = analyze_screen("What applications are open?")
```

**Current state (May 2026):** Vision analysis disabled. Provider landscape:
- **GLM-5V**: Removed per user directive ("no remove the glm")
- **Kimi-k2.6**: 401 errors — different API key from Z.AI/BigModel
- **Kimi-for-coding**: 404 — coding endpoint has no vision support
- **browser_vision**: Works for web pages only (91% success), not local screenshots
- **Qwen 27B**: Training in progress (step 5340/10000, ~26h left). Will be local on DGX at `spark-85e8.local:8000`

**Interim pattern — User describes, agent acts:**
```python
from hermes_hands import screen

path = screen()
# User describes what they see, agent uses click/type/focus accordingly
# No AI vision analysis until Qwen 27B is ready
```

## Continuous Vision Loop

```python
from hermes_hands import get_hands
import time

hands = get_hands()

while True:
    # 1. Capture
    path = hands.screen()
    
    # 2. Analyze (when vision enabled)
    if hands.vision_enabled:
        result = hands.analyze_screen()
        # 3. Act based on analysis
        # ... decision logic ...
    
    time.sleep(5)  # Loop interval
```

## Screenshot History

The module maintains a rolling history of last 50 screenshots:

```python
hands = get_hands()
print(f"History: {len(hands.screenshot_history)} images")
print(f"Last: {hands.last_screenshot}")
```

## Tested Example

```python
from hermes_hands import screen, click, get_mouse_pos, focus_app

# 1. Focus Terminal
focus_app("Terminal")

# 2. Get mouse position
pos = get_mouse_pos()
print(f"Mouse at: {pos}")

# 3. Click at specific coordinates
click(500, 300)

# 4. Capture screenshot
path = screen()
print(f"Screenshot saved: {path}")

# 5. Capture region
path = screen(region="100,200,300,400")
print(f"Region screenshot: {path}")
```

## Pitfalls

- **Coordinates are screen-relative, not window-relative.** Calculator at (830, 704) means clicks must be offset from screen origin, not window origin.
- **Accessibility permissions required** for mouse/keyboard control. If clicks don't work, check System Preferences → Security & Privacy → Accessibility.
- **App names are case-sensitive** for `open_app`/`close_app`/`focus_app`. Use exact app bundle name.
- **Window position changes** — always verify window position with `osascript` before clicking if precision matters.
- **Vision analysis disabled** — `analyze_screen()` returns placeholder until vision model configured. Use `browser_vision` for web-based visual analysis in the meantime.
- **No OCR built-in** — Install `tesseract` (`brew install tesseract`) if you need text extraction from screenshots.

## File Location

**Integrated into Hermes source:** `~/hermes-agent/tools/hands.py` (class `HermesHands`)

**Legacy prototype:** `~/subconscious/hermes_hands.py` (deprecated, kept for reference)

To make hands a discoverable Hermes tool, add `registry.register()`:
```python
from hermes_cli.tools import registry

registry.register(name="hermes_hands", toolset="automation")
```

See `references/hermes_hands_implementation.py` for the complete tested source code.

## Related Skills

- `hermes-vision-provider-setup` — Configure vision model for `analyze_screen()`
- `dynamic-real-time-vision` — Visual Loop pattern for dynamic screen navigation
- `hermes-provider-config` — Provider and endpoint configuration (including vision routing)
