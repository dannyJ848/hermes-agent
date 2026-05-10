#!/usr/bin/env python3
"""
hermes_hands.py — Autonomous GUI Control System for Hermes Agent

Provides:
- screen(): capture screen and return path
- click(x, y): click at screen coordinates
- type(text): type text
- scroll(direction): scroll up/down
- key(key): press key (enter, tab, escape, etc)
- open_app(name): open application
- close_app(name): close application
- focus_app(name): focus application
- get_windows(): list open windows
- vision_loop(callback, interval): continuous screen capture + analysis

Dependencies: cliclick (brew install cliclick), screencapture (built-in)
"""

import subprocess
import time
import tempfile
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

class HermesHands:
    """GUI automation controller for macOS.
    
    Vision analysis: Currently disabled. Waiting for Qwen 27B vision capability.
    Screenshots are saved to /tmp/hermes_screen_*.png for later analysis.
    """
    
    def __init__(self):
        self.last_screenshot: Optional[str] = None
        self.screenshot_history: list = []
        self.cliclick_path = "/opt/homebrew/bin/cliclick"
        self.vision_enabled = False  # Will enable when Qwen 27B gets vision
        
    def screen(self, region: Optional[str] = None) -> str:
        """Capture screen. Returns path to screenshot."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = f"/tmp/hermes_screen_{timestamp}.png"
        
        cmd = ['screencapture', '-x']
        if region:
            cmd.extend(['-R', region])
        cmd.append(path)
        
        subprocess.run(cmd, check=True, timeout=10)
        self.last_screenshot = path
        self.screenshot_history.append(path)
        # Keep only last 50 screenshots
        if len(self.screenshot_history) > 50:
            old = self.screenshot_history.pop(0)
            try:
                Path(old).unlink()
            except:
                pass
        return path
    
    def analyze_screen(self, prompt: str = "Describe what you see") -> str:
        """Analyze current screen. Returns placeholder until vision is enabled."""
        if not self.vision_enabled:
            return f"Vision analysis disabled. Screenshot saved to {self.last_screenshot}. Enable when Qwen 27B vision is available."
        # Vision analysis code would go here
        return "Vision not yet implemented"
    
    def click(self, x: int, y: int, button: str = "left") -> str:
        """Click at screen coordinates."""
        btn = "c" if button == "left" else "rc" if button == "right" else "dc"
        result = subprocess.run(
            [self.cliclick_path, f"{btn}:{x},{y}"],
            capture_output=True, text=True, timeout=5
        )
        return f"Clicked {button} at ({x}, {y})"
    
    def double_click(self, x: int, y: int) -> str:
        """Double-click at coordinates."""
        subprocess.run(
            [self.cliclick_path, f"dc:{x},{y}"],
            capture_output=True, text=True, timeout=5
        )
        return f"Double-clicked at ({x}, {y})"
    
    def type(self, text: str) -> str:
        """Type text at current cursor position."""
        # Escape special characters for cliclick
        escaped = text.replace("'", "\\'").replace('"', '\\"')
        subprocess.run(
            [self.cliclick_path, f"t:{escaped}"],
            capture_output=True, text=True, timeout=5
        )
        return f"Typed: {text[:50]}"
    
    def key(self, key_name: str) -> str:
        """Press special key."""
        key_map = {
            'enter': 'return', 'return': 'return',
            'tab': 'tab', 'escape': 'esc', 'esc': 'esc',
            'space': 'space', 'delete': 'delete', 'backspace': 'delete',
            'up': 'up', 'down': 'down', 'left': 'left', 'right': 'right',
            'cmd': 'cmd', 'command': 'cmd',
            'shift': 'shift', 'ctrl': 'ctrl', 'alt': 'alt',
            'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4', 'f5': 'f5',
            'f6': 'f6', 'f7': 'f7', 'f8': 'f8', 'f9': 'f9', 'f10': 'f10',
        }
        mapped = key_map.get(key_name.lower(), key_name)
        subprocess.run(
            [self.cliclick_path, f"kp:{mapped}"],
            capture_output=True, text=True, timeout=5
        )
        return f"Pressed key: {mapped}"
    
    def scroll(self, direction: str, amount: int = 3) -> str:
        """Scroll up or down."""
        direction = "up" if direction.lower() in ["up", "u"] else "down"
        for _ in range(amount):
            subprocess.run(
                [self.cliclick_path, f"scroll:{direction}"],
                capture_output=True, text=True, timeout=2
            )
            time.sleep(0.05)
        return f"Scrolled {direction} x{amount}"
    
    def move(self, x: int, y: int) -> str:
        """Move mouse to coordinates without clicking."""
        subprocess.run(
            [self.cliclick_path, f"m:{x},{y}"],
            capture_output=True, text=True, timeout=5
        )
        return f"Moved to ({x}, {y})"
    
    def drag(self, x1: int, y1: int, x2: int, y2: int) -> str:
        """Drag from (x1,y1) to (x2,y2)."""
        subprocess.run(
            [self.cliclick_path, f"dd:{x1},{y1}", f"du:{x2},{y2}"],
            capture_output=True, text=True, timeout=5
        )
        return f"Dragged from ({x1},{y1}) to ({x2},{y2})"
    
    def open_app(self, app_name: str) -> str:
        """Open application."""
        subprocess.run(
            ['open', '-a', app_name],
            capture_output=True, text=True, timeout=10
        )
        return f"Opened: {app_name}"
    
    def close_app(self, app_name: str) -> str:
        """Close application."""
        script = f'tell application "{app_name}" to quit'
        subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=10
        )
        return f"Closed: {app_name}"
    
    def focus_app(self, app_name: str) -> str:
        """Focus/bring application to front."""
        script = f'tell application "{app_name}" to activate'
        subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=10
        )
        return f"Focused: {app_name}"
    
    def get_windows(self) -> list:
        """List open windows."""
        # Fast approach: use lsappinfo instead of applescript
        try:
            result = subprocess.run(
                ['lsappinfo', 'info', '-only', 'name', 'all'],
                capture_output=True, text=True, timeout=3
            )
            apps = []
            for line in result.stdout.split('\n'):
                if '"LSASN"' in line:
                    # Extract app name from bundle
                    pass
                elif line.strip() and not line.startswith('LSASN'):
                    apps.append(line.strip().strip('"'))
            return apps[:15]
        except:
            # Fallback: list frontmost apps
            try:
                result = subprocess.run(
                    ['osascript', '-e', 'tell application "System Events" to get name of every application process whose visible is true'],
                    capture_output=True, text=True, timeout=3
                )
                apps = [a.strip() for a in result.stdout.split(',') if a.strip()]
                return apps[:15]
            except:
                return []
    
    def get_mouse_pos(self) -> tuple:
        """Get current mouse position."""
        result = subprocess.run(
            [self.cliclick_path, "p"],
            capture_output=True, text=True, timeout=5
        )
        # Output format: "123,456"
        pos = result.stdout.strip().split(',')
        return (int(pos[0]), int(pos[1]))
    
    def wait(self, seconds: float) -> str:
        """Wait for specified seconds."""
        time.sleep(seconds)
        return f"Waited {seconds}s"
    
    def vision_loop(self, callback: Callable[[str, str], None], interval: float = 5.0, max_iterations: int = 100):
        """
        Continuous screen capture loop.
        
        Args:
            callback: function(screenshot_path, analysis) -> None
            interval: seconds between captures
            max_iterations: max number of captures (0 = infinite)
        """
        iteration = 0
        while max_iterations == 0 or iteration < max_iterations:
            try:
                path = self.screen()
                # Analysis would be done by vision model
                callback(path, "captured")
                iteration += 1
                if iteration < max_iterations or max_iterations == 0:
                    time.sleep(interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                callback(None, f"error: {e}")
                time.sleep(interval)
        return f"Vision loop completed: {iteration} captures"


# Singleton instance
_hands: Optional[HermesHands] = None

def get_hands() -> HermesHands:
    """Get or create hands instance."""
    global _hands
    if _hands is None:
        _hands = HermesHands()
    return _hands


# Convenience functions for direct use
def screen(region: Optional[str] = None) -> str:
    return get_hands().screen(region)

def click(x: int, y: int, button: str = "left") -> str:
    return get_hands().click(x, y, button)

def double_click(x: int, y: int) -> str:
    return get_hands().double_click(x, y)

def type_text(text: str) -> str:
    return get_hands().type(text)

def key(key_name: str) -> str:
    return get_hands().key(key_name)

def scroll(direction: str, amount: int = 3) -> str:
    return get_hands().scroll(direction, amount)

def move(x: int, y: int) -> str:
    return get_hands().move(x, y)

def drag(x1: int, y1: int, x2: int, y2: int) -> str:
    return get_hands().drag(x1, y1, x2, y2)

def open_app(app_name: str) -> str:
    return get_hands().open_app(app_name)

def close_app(app_name: str) -> str:
    return get_hands().close_app(app_name)

def focus_app(app_name: str) -> str:
    return get_hands().focus_app(app_name)

def get_windows() -> list:
    return get_hands().get_windows()

def get_mouse_pos() -> tuple:
    return get_hands().get_mouse_pos()

def vision_loop(callback, interval=5.0, max_iterations=100):
    return get_hands().vision_loop(callback, interval, max_iterations)


if __name__ == "__main__":
    # Test
    hands = HermesHands()
    print("Hermes Hands test:")
    print(f"  Mouse position: {hands.get_mouse_pos()}")
    print(f"  Screenshot: {hands.screen()}")
    print(f"  Windows: {len(hands.get_windows())} found")
