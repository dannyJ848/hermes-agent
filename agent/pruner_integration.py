"""
pruner_integration.py - Thin adapter connecting distillation_bridge ↔ memory_auto_pruner.
Every call wrapped so pruner crashes NEVER block the main pipeline.
"""
import logging
import os
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger("subconscious.pruner_integration")

MEMORY_HARD_LIMIT = int(os.getenv("MEMORY_HARD_LIMIT", 50_000))
MEMORY_PRUNE_TARGET = int(os.getenv("MEMORY_PRUNE_TARGET", 30_000))
PRUNE_CALL_INTERVAL = int(os.getenv("PRUNE_CALL_INTERVAL", 10))
PRUNE_PCT_THRESHOLD = float(os.getenv("PRUNE_PCT_THRESHOLD", 0.80))

@dataclass
class _PrunerState:
    call_counter: int = 0
    last_prune_stats: Optional[Dict[str, Any]] = None
    last_error: Optional[str] = None
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def increment(self) -> int:
        with self._lock:
            self.call_counter += 1
            return self.call_counter

_state = _PrunerState()

def _get_pruner():
    try:
        from agent.memory_auto_pruner import prune
        return prune
    except Exception as exc:
        logger.warning("Could not import memory_auto_pruner: %s", exc)
        _state.last_error = str(exc)
        return None

def _read_memory_size() -> int:
    mem_path = os.path.expanduser("~/.hermes/memories/MEMORY.md")
    try:
        with open(mem_path, "r", encoding="utf-8") as fh:
            return len(fh.read())
    except Exception:
        return 0

def should_prune() -> bool:
    n = _state.increment()
    if n % PRUNE_CALL_INTERVAL == 0:
        return True
    current = _read_memory_size()
    if current >= int(MEMORY_HARD_LIMIT * PRUNE_PCT_THRESHOLD):
        logger.info("Size trigger: MEMORY at %d chars (>= threshold %d)", current, int(MEMORY_HARD_LIMIT * PRUNE_PCT_THRESHOLD))
        return True
    return False

def safe_prune(force: bool = False) -> Optional[Dict[str, Any]]:
    prune_fn = _get_pruner()
    if prune_fn is None:
        return None
    try:
        stats = prune_fn(force=force)
        _state.last_prune_stats = stats
        logger.info("Prune completed: %s", stats)
        return stats
    except Exception as exc:
        logger.exception("Prune raised (suppressed): %s", exc)
        _state.last_error = str(exc)
        return None

def memory_health() -> Dict[str, Any]:
    current = _read_memory_size()
    usage_pct = (current / MEMORY_HARD_LIMIT * 100) if MEMORY_HARD_LIMIT else 0
    return {
        "size_chars": current,
        "hard_limit": MEMORY_HARD_LIMIT,
        "target": MEMORY_PRUNE_TARGET,
        "usage_pct": round(usage_pct, 1),
        "needs_prune": current >= int(MEMORY_HARD_LIMIT * PRUNE_PCT_THRESHOLD),
        "last_prune_stats": _state.last_prune_stats,
        "last_error": _state.last_error,
    }
