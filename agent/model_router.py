"""Model router with task complexity scoring.

ZERO-FAILURE GUARANTEE:
- Every method catches ALL exceptions and returns safe defaults
- Missing config → returns default model
- Invalid task description → returns default model
- Config read errors → returns default model
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ModelRouter:
    """Routes tasks to appropriate models based on complexity heuristics.
    
    ZERO-FAILURE: Always returns a valid model string.
    """

    POWERFUL_KEYWORDS = {"code", "debug", "complex", "refactor", "architecture", "design", "implement", "build", "deep", "hard", "difficult", "sophisticated"}
    FAST_KEYWORDS = {"simple", "quick", "status", "check", "list", "show", "get", "tell", "what", "who", "when", "where", "yes", "no"}

    def __init__(self):
        self._models = {}
        self._default = None
        self._load_config()

    def _load_config(self) -> None:
        """Load model routing config from ~/.hermes/config.yaml."""
        try:
            import yaml
            from pathlib import Path
            config_path = Path.home() / ".hermes" / "config.yaml"
            if config_path.exists():
                with open(config_path) as f:
                    config = yaml.safe_load(f) or {}
                routing = config.get("model_routing", {})
                self._models = {
                    "powerful": routing.get("powerful", "kimi-for-coding"),
                    "fast": routing.get("fast", "deepseek-v4-pro"),
                    "default": routing.get("default", "kimi-for-coding"),
                }
                self._default = self._models["default"]
            else:
                self._models = {"powerful": "kimi-for-coding", "fast": "deepseek-v4-pro", "default": "kimi-for-coding"}
                self._default = "kimi-for-coding"
        except Exception as e:
            logger.debug("[ModelRouter] Config load failed: %s", e)
            self._models = {"powerful": "kimi-for-coding", "fast": "deepseek-v4-pro", "default": "kimi-for-coding"}
            self._default = "kimi-for-coding"

    def reload(self) -> None:
        """Reload config from disk."""
        self._load_config()

    @property
    def models(self) -> dict:
        """Return current routing config."""
        return dict(self._models)

    def route_task(self, task_description: str) -> str:
        """Route a task to the most appropriate model.
        
        NEVER FAILS: Always returns a valid model string.
        """
        if not task_description or not isinstance(task_description, str):
            return self._default or "kimi-for-coding"
        
        try:
            task_lower = task_description.lower()
            words = set(task_lower.split())
            
            powerful_score = len(words & self.POWERFUL_KEYWORDS)
            fast_score = len(words & self.FAST_KEYWORDS)
            
            if powerful_score > fast_score:
                return self._models.get("powerful", self._default)
            elif fast_score > powerful_score:
                return self._models.get("fast", self._default)
            else:
                return self._default or "kimi-for-coding"
        except Exception as e:
            logger.debug("[ModelRouter] Routing failed: %s", e)
            return self._default or "kimi-for-coding"
