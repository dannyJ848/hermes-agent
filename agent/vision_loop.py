"""
Vision Loop — Agent Eyes for Screen Capture and Visual Analysis

Provides the visual perception layer for Hermes Agent:
  1. Screen capture (macOS screencapture)
  2. GUI element detection (clickable regions, text fields)
  3. Visual analysis pipeline (capture → analyze → act)
  4. Integration with browser_vision for web-based visual tasks

Usage:
    from agent.vision_loop import VisionLoop
    vision = VisionLoop()
    result = vision.capture_and_analyze("What do you see on the screen?")
"""

import base64
import json
import logging
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class VisionLoop:
    """
    Agent visual perception system.
    
    Captures screen, analyzes visual content, and provides
    actionable insights for GUI automation.
    """
    
    def __init__(self, screenshot_dir: Optional[Path] = None):
        self.screenshot_dir = screenshot_dir or (Path.home() / ".hermes" / "screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.last_screenshot: Optional[Path] = None
        self.last_analysis: Optional[Dict] = None
        
    def capture_screen(self, name: Optional[str] = None) -> Path:
        """
        Capture the full screen and save to file.
        Returns the path to the screenshot.
        """
        timestamp = int(time.time())
        filename = f"{name or 'screen'}_{timestamp}.png"
        screenshot_path = self.screenshot_dir / filename
        
        try:
            # macOS screencapture
            subprocess.run(
                ["screencapture", "-x", str(screenshot_path)],
                check=True,
                capture_output=True,
                timeout=10,
            )
            self.last_screenshot = screenshot_path
            logger.info(f"Screen captured: {screenshot_path}")
            return screenshot_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Screen capture failed: {e}")
            raise
        except FileNotFoundError:
            logger.error("screencapture not found — macOS only")
            raise
    
    def capture_region(self, x: int, y: int, w: int, h: int, 
                       name: Optional[str] = None) -> Path:
        """
        Capture a specific screen region.
        """
        timestamp = int(time.time())
        filename = f"{name or 'region'}_{timestamp}.png"
        screenshot_path = self.screenshot_dir / filename
        
        try:
            # macOS screencapture with region
            subprocess.run(
                ["screencapture", "-x", "-R", f"{x},{y},{w},{h}", 
                 str(screenshot_path)],
                check=True,
                capture_output=True,
                timeout=10,
            )
            self.last_screenshot = screenshot_path
            logger.info(f"Region captured: {screenshot_path}")
            return screenshot_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Region capture failed: {e}")
            raise
    
    def analyze_screenshot(self, screenshot_path: Path, 
                           question: str = "What do you see?") -> Dict:
        """
        Analyze a screenshot using vision model.
        Falls back to browser_vision if available.
        """
        try:
            # Try to use browser_vision tool
            from tools.browser_vision import browser_vision
            
            # Convert image to base64 for analysis
            with open(screenshot_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            
            # Use browser_vision for analysis
            result = browser_vision(
                url=f"file://{screenshot_path}",
                question=question,
            )
            
            analysis = {
                "question": question,
                "answer": result,
                "screenshot": str(screenshot_path),
                "timestamp": time.time(),
            }
            self.last_analysis = analysis
            return analysis
            
        except Exception as e:
            logger.warning(f"Vision analysis failed: {e}")
            return {
                "question": question,
                "answer": f"Vision analysis unavailable: {e}",
                "screenshot": str(screenshot_path),
                "timestamp": time.time(),
                "error": str(e),
            }
    
    def capture_and_analyze(self, question: str = "What do you see?",
                            region: Optional[Tuple[int, int, int, int]] = None) -> Dict:
        """
        One-shot: capture screen and analyze.
        
        Args:
            question: What to ask about the screen content
            region: Optional (x, y, w, h) tuple for region capture
            
        Returns:
            Dict with screenshot path and analysis result
        """
        if region:
            x, y, w, h = region
            screenshot = self.capture_region(x, y, w, h)
        else:
            screenshot = self.capture_screen()
        
        analysis = self.analyze_screenshot(screenshot, question)
        return {
            "screenshot": str(screenshot),
            "analysis": analysis,
        }
    
    def find_clickable_elements(self, screenshot_path: Optional[Path] = None) -> List[Dict]:
        """
        Analyze screenshot to find clickable GUI elements.
        Returns list of elements with coordinates and descriptions.
        """
        screenshot = screenshot_path or self.last_screenshot
        if not screenshot:
            screenshot = self.capture_screen("clickable")
        
        analysis = self.analyze_screenshot(
            screenshot,
            "Identify all clickable elements (buttons, links, text fields, icons). "
            "For each, provide: type, approximate center coordinates (x,y), and description. "
            "Return as JSON array."
        )
        
        try:
            # Try to parse JSON from response
            answer = analysis.get("answer", "")
            # Extract JSON array from response
            start = answer.find("[")
            end = answer.rfind("]")
            if start != -1 and end != -1:
                elements = json.loads(answer[start:end+1])
                return elements
        except (json.JSONDecodeError, ValueError):
            pass
        
        return []
    
    def click_at(self, x: int, y: int) -> bool:
        """
        Click at specific screen coordinates using cliclick.
        """
        try:
            subprocess.run(
                ["cliclick", "c:{},{}".format(x, y)],
                check=True,
                capture_output=True,
                timeout=5,
            )
            logger.info(f"Clicked at ({x}, {y})")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Click failed: {e}")
            return False
        except FileNotFoundError:
            logger.error("cliclick not found — install with: brew install cliclick")
            return False
    
    def type_text(self, text: str) -> bool:
        """
        Type text using cliclick.
        """
        try:
            subprocess.run(
                ["cliclick", "t:{}".format(text)],
                check=True,
                capture_output=True,
                timeout=5,
            )
            logger.info(f"Typed text: {text[:50]}...")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Type failed: {e}")
            return False
        except FileNotFoundError:
            logger.error("cliclick not found")
            return False
    
    def navigate_and_act(self, instruction: str) -> Dict:
        """
        High-level: capture screen, analyze, and perform action.
        
        Example instruction: "Click the Safari icon in the dock"
        """
        # Capture current state
        screenshot = self.capture_screen("navigate")
        
        # Analyze what we see
        analysis = self.analyze_screenshot(
            screenshot,
            f"Given the instruction '{instruction}', what should I do? "
            f"Identify the target element and provide exact click coordinates (x,y)."
        )
        
        answer = analysis.get("answer", "")
        
        # Try to extract coordinates from response
        import re
        coords = re.findall(r'(\d+)[,\s]+(\d+)', answer)
        
        if coords:
            x, y = int(coords[0][0]), int(coords[0][1])
            success = self.click_at(x, y)
            return {
                "instruction": instruction,
                "screenshot": str(screenshot),
                "analysis": answer,
                "action": "click",
                "coordinates": (x, y),
                "success": success,
            }
        else:
            return {
                "instruction": instruction,
                "screenshot": str(screenshot),
                "analysis": answer,
                "action": "none",
                "success": False,
                "error": "Could not determine coordinates from analysis",
            }


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

_vision_loop: Optional[VisionLoop] = None

def get_vision_loop() -> VisionLoop:
    """Get or create the global VisionLoop instance."""
    global _vision_loop
    if _vision_loop is None:
        _vision_loop = VisionLoop()
    return _vision_loop


def screen_capture(question: str = "What do you see?") -> Dict:
    """Quick screen capture and analysis."""
    vision = get_vision_loop()
    return vision.capture_and_analyze(question)


def click_element(description: str) -> Dict:
    """Find and click an element by description."""
    vision = get_vision_loop()
    return vision.navigate_and_act(f"Click the {description}")


def type_at_focus(text: str) -> bool:
    """Type text at current focus."""
    vision = get_vision_loop()
    return vision.type_text(text)
