"""
Vision Tools — Screen capture and GUI automation for Hermes Agent

Registers vision_loop capabilities as Hermes tools.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def screen_capture_tool(question: str = "What do you see on the screen?") -> Dict[str, Any]:
    """
    Capture the screen and analyze what is visible.
    
    Args:
        question: What to ask about the screen content
        
    Returns:
        Dict with screenshot path and analysis
    """
    from agent.vision_loop import get_vision_loop
    vision = get_vision_loop()
    return vision.capture_and_analyze(question)


def gui_click_tool(description: str) -> Dict[str, Any]:
    """
    Find and click a GUI element by description.
    
    Args:
        description: Description of element to click (e.g. "Safari icon in dock")
        
    Returns:
        Dict with action result
    """
    from agent.vision_loop import get_vision_loop
    vision = get_vision_loop()
    return vision.navigate_and_act(f"Click the {description}")


def gui_type_tool(text: str) -> bool:
    """
    Type text at current focus.
    
    Args:
        text: Text to type
        
    Returns:
        True if successful
    """
    from agent.vision_loop import get_vision_loop
    vision = get_vision_loop()
    return vision.type_text(text)


# Tool schemas for registry
SCREEN_CAPTURE_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {
            "type": "string",
            "description": "What to ask about the screen content",
            "default": "What do you see on the screen?"
        }
    }
}

GUI_CLICK_SCHEMA = {
    "type": "object",
    "properties": {
        "description": {
            "type": "string",
            "description": "Description of element to click (e.g. 'Safari icon in dock')"
        }
    },
    "required": ["description"]
}

GUI_TYPE_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {
            "type": "string",
            "description": "Text to type at current focus"
        }
    },
    "required": ["text"]
}
