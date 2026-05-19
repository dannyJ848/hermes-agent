"""Model router -- heuristic task-to-model selection.

Reads model lists from ``~/.hermes/config.yaml`` under the ``router_models``
key and falls back to the default model when no match is found.

Example config snippet::

    router_models:
      powerful: "anthropic/claude-opus-4.6"
      fast: "openai/gpt-4.1-mini"
      default: "anthropic/claude-sonnet-4"

If ``router_models`` is absent, the router falls back to the top-level
``model.default`` value.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Keywords that signal a task needs a powerful (slow/expensive) model.
_POWERFUL_KEYWORDS = frozenset(
    {"code", "debug", "complex", "refactor", "architecture", "design", "algorithm"}
)

# Keywords that signal a task can use a fast/cheap model.
_FAST_KEYWORDS = frozenset(
    {"simple", "quick", "status", "summary", "list", "check", "ping", "hello"}
)

# Regexes compiled from the keyword sets for whole-word matching.
_POWERFUL_RE = re.compile(
    r"\b(" + "|".join(map(re.escape, _POWERFUL_KEYWORDS)) + r")\b", re.IGNORECASE
)
_FAST_RE = re.compile(
    r"\b(" + "|".join(map(re.escape, _FAST_KEYWORDS)) + r")\b", re.IGNORECASE
)


def _load_router_config() -> Dict[str, Any]:
    """Load the ``router_models`` section from user config.

    Returns an empty dict when the config file is missing or the key
    is absent so that callers can apply their own fallback logic.
    """
    try:
        from hermes_cli.config import load_config
    except Exception as exc:  # pragma: no cover
        logger.debug("Unable to import hermes_cli.config: %s", exc)
        return {}

    try:
        cfg = load_config()
    except Exception as exc:  # pragma: no cover
        logger.debug("Config load failed: %s", exc)
        return {}

    return cfg.get("router_models") or {}


def _get_default_model() -> str:
    """Return the user's default model from config, or a hard-coded fallback."""
    try:
        from hermes_cli.config import load_config
        cfg = load_config()
        default = cfg.get("model", {}).get("default") or cfg.get("model", {}).get("model")
        if default:
            return str(default)
    except Exception as exc:  # pragma: no cover
        logger.debug("Could not resolve default model from config: %s", exc)
    return "anthropic/claude-sonnet-4"


class ModelRouter:
    """Heuristic router that maps a task description to a model name.

    The router scans the *task_description* for keywords and selects:

    * **powerful** model – when keywords like ``code``, ``debug``,
      ``complex`` are detected.
    * **fast** model – when keywords like ``simple``, ``quick``,
      ``status`` are detected.
    * **default** model – when no strong signal is present or when the
      configured model name is missing.

    Model names are read from the ``router_models`` config block;
    missing entries fall back to the user's default model.
    """

    def __init__(self, models: Dict[str, str] | None = None) -> None:
        """Initialise the router.

        Args:
            models: Optional mapping of ``{"powerful": ..., "fast": ...,
            "default": ...}``.  When *None* the mapping is loaded from
            ``~/.hermes/config.yaml``.
        """
        if models is not None:
            self._models = dict(models)
        else:
            self._models = _load_router_config()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route_task(self, task_description: str) -> str:
        """Return the model name best suited for *task_description*.

        Args:
            task_description: Free-form text describing the task.

        Returns:
            A model identifier string (e.g. ``"anthropic/claude-opus-4.6"``).
        """
        if not isinstance(task_description, str):
            task_description = str(task_description)

        powerful_hits = len(_POWERFUL_RE.findall(task_description))
        fast_hits = len(_FAST_RE.findall(task_description))

        if powerful_hits > fast_hits:
            chosen = self._models.get("powerful")
            logger.debug(
                "Router chose powerful model (%d > %d hits): %s",
                powerful_hits,
                fast_hits,
                chosen,
            )
        elif fast_hits > powerful_hits:
            chosen = self._models.get("fast")
            logger.debug(
                "Router chose fast model (%d > %d hits): %s",
                fast_hits,
                powerful_hits,
                chosen,
            )
        else:
            # No strong signal or tied scores → default.
            chosen = self._models.get("default")
            logger.debug(
                "Router chose default model (powerful=%d, fast=%d): %s",
                powerful_hits,
                fast_hits,
                chosen,
            )

        if not chosen:
            chosen = _get_default_model()
            logger.debug("Router falling back to default model: %s", chosen)

        return chosen

    # ------------------------------------------------------------------
    # Helpers for testing / introspection
    # ------------------------------------------------------------------

    @property
    def models(self) -> Dict[str, str]:
        """Current model mapping (read-only copy)."""
        return dict(self._models)

    def reload(self) -> None:
        """Reload model mapping from disk config."""
        self._models = _load_router_config()
