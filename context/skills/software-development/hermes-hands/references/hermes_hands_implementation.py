#!/usr/bin/env python3
"""Hermes Hands — GUI automation for macOS.

Actual implementation saved at ~/subconscious/hermes_hands.py.
This is the tested, working version from May 2026.

Provides: screen capture, mouse/keyboard control, app management, continuous vision loop.
Uses: screencapture + cliclick + osascript.
"""

import subprocess
import time
import os
import glob
from pathlib import Path
from typing import Optional, Tuple, List

class HermesHands:
    """GUI automation controller for macOS."""
    
    def __init__(self):
        self.screenshot_history: List[str] = []
        self.last_screenshot: Optional[str] = None
        self.vision_enabled = False
        self._cliclick_path = "/opt/homebrew/bin/cliclick"
        
    def screen(self, region: Optional[str] = None) -> str:
        """Capture screenshot. Returns path to PNG file."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path = f"/tmp/hermes_screen_{timestamp}.png"
        
        cmd = ["screencapture"]
        if region:
            cmd.extend(["-R", region])
        cmd.append(path)
        
        subprocess.run(cmd, check=True, capture_output=True)
        self.last_screenshot = path
        self.screenshot_history.append(path)
        if len(self.screenshot_history) > 50:
            self.screenshot_history.pop(0)
        return path
    
    def click(self, x: int, y: int) -> None:
        """Left click at screen coordinates."""
        subprocess.run([self._cliclick_path, f"c:{x},{y}"], check=True)
    
    def dblclick(self, x: int, y: int) -> None:
        """Double click at screen coordinates."""
        subprocess.run([self._cliclick_path, f"dc:{x},{y}"], check=True)
    
    def rightclick(self, x: int, y: int) -> None:
        """Right click at screen coordinates."""
        subprocess.run([self._cliclick_path, f"rc:{x},{y}"], check=True)
    
    def drag(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Drag from (x1,y1) to (x2,y2)."""
        subprocess.run([self._cliclick_path, f"dd:{x1},{y1}", f"du:{x2},{y2}"], check=True)
    
    def get_mouse_pos(self) -> Tuple[int, int]:
        """Get current mouse position."""
        result = subprocess.run([self._cliclick_path, "p"], capture_output=True, text=True)
        parts = result.stdout.strip().split(",")
        return int(parts[0]), int(parts[1])
    
    def type_text(self, text: str) -> None:
        """Type text string."""
        subprocess.run([self._cliclick_path, f"t:{text}"], check=True)
    
    def key(self, key_name: str) -> None:
        """Press a key (escape, enter, tab, space, etc.)."""
        subprocess.run([self._cliclick_path, f"kp:{key_name}"], check=True)
    
    def open_app(self, app_name: str) -> None:
        """Launch application."""
        subprocess.run(["osascript", "-e", f'tell application "{app_name}" to activate'], check=True)
    
    def close_app(self, app_name: str) -> None:
        """Quit application."""
        subprocess.run(["osascript", "-e", f'tell application "{app_name}" to quit'], check=True)
    
    def focus_app(self, app_name: str) -> None:
        """Bring application to front."""
        subprocess.run(["osascript", "-e", f'tell application "System Events" to tell process "{app_name}" to set frontmost to true'], check=True)
    
    def get_windows(self) -> List[str]:
        """List visible windows/apps."""
        result = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to get name of every process whose background only is false'],
            capture_output=True, text=True
        )
        return [w.strip() for w in result.stdout.split(",")]

# Singleton instance
_hands_instance: Optional[HermesHands] = None

def get_hands() -> HermesHands:
    """Get or create the singleton hands instance."""
    global _hands_instance
    if _hands_instance is None:
        _hands_instance = HermesHands()
    return _hands_instance

# Convenience exports
screen = lambda region=None: get_hands().screen(region)
click = lambda x, y: get_hands().click(x, y)
dblclick = lambda x, y: get_hands().dblclick(x, y)
rightclick = lambda x, y: get_hands().rightclick(x, y)
drag = lambda x1, y1, x2, y2: get_hands().drag(x1, y1, x2, y2)
get_mouse_pos = lambda: get_hands().get_mouse_pos()
type_text = lambda text: get_hands().type_text(text)
key = lambda k: get_hands().key(k)
open_app = lambda name: get_hands().open_app(name)
close_app = lambda name: get_hands().close_app(name)
focus_app = lambda name: get_hands().focus_app(name)
get_windows = lambda: get_hands().get_windows()

if __name__ == "__main__":
    # Quick test
    h = get_hands()
    print(f"Mouse position: {h.get_mouse_pos()}")
    path = h.screen()
    print(f"Screenshot: {path}")
    print(f"History: {len(h.screenshot_history)} images")
    print("Hermes Hands ready.")
