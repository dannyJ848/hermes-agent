"""memory_cortex_bridge — bidirectional sync between cerebrum and cortex.

The cerebrum stores raw episodic memories + distilled tips (SQLite).
The cortex learning engine tracks usage/effectiveness of injected memories.
This bridge syncs data between them so:
  - High-confidence distilled tips get usage tracking (push)
  - Cortex effectiveness predictions feed back to injection (pull)

This fixes the writer/reader DB mismatch identified in the audit: the cortex
writer targets PostgreSQL while the reader targets SQLite. This bridge makes
the SQLite path the single source of truth.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"


class MemoryCortexBridge:
    """Bidirectional sync between cerebrum memory and cortex learning."""

    def __init__(self):
        self._last_sync_count = 0

    def sync(self, direction: str = "bidirectional") -> Dict[str, int]:
        """Sync memory data between cerebrum and cortex stores.

        push: high-confidence distilled_tips → cortex memory_units (for usage tracking)
        pull: cortex effectiveness predictions → available for injection ranking
        """
        result = {"direction": direction, "pushed": 0, "pulled": 0}
        if direction in ("push", "bidirectional"):
            result["pushed"] = self._push_to_cortex()
        if direction in ("pull", "bidirectional"):
            result["pulled"] = len(self._pull_from_cortex("", limit=1))
        self._last_sync_count = result.get("pushed", 0)
        return result

    def push(self, memories: List[str]) -> int:
        """Push memory items to the cortex learning store for usage tracking."""
        try:
            from agent.cortex_learning import get_learning_engine
            engine = get_learning_engine()
            if not hasattr(engine, "store"):
                return 0
            count = 0
            for mem in memories:
                if isinstance(mem, str) and len(mem) > 10:
                    # Record that this memory was injected (for effectiveness tracking)
                    try:
                        engine.record_memory_injected(mem[:200])
                        count += 1
                    except Exception:
                        pass
            return count
        except Exception as e:
            logger.debug("memory_bridge: push failed: %s", e)
            return 0

    def pull(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Pull cortex predictions for memory ranking."""
        return self._pull_from_cortex(query, limit)

    def _push_to_cortex(self) -> int:
        """Push high-confidence distilled tips to cortex for tracking."""
        try:
            from agent.db_pool import get_connection
            conn = get_connection(_DB_PATH)
            rows = conn.execute(
                "SELECT tip_text FROM distilled_tips "
                "WHERE verification_status = 'verified' AND priority >= 6 "
                "LIMIT 50"
            ).fetchall()
            tips = [r["tip_text"] for r in rows if r["tip_text"]]
            return self.push(tips)
        except Exception as e:
            logger.debug("memory_bridge: auto-push failed: %s", e)
            return 0

    def _pull_from_cortex(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Pull distilled tips ranked by cortex effectiveness data."""
        try:
            from agent.cortex_learning import get_learning_engine
            engine = get_learning_engine()
            if hasattr(engine, "store"):
                tips = engine.store.get_distilled_tips(limit=limit)
                # Score by semantic relevance if query provided
                if query and tips:
                    try:
                        from agent.adaptive_injection import score_relevance
                        scored = []
                        for tip in tips:
                            text = tip.get("tip_text", "") if isinstance(tip, dict) else str(tip)
                            score = score_relevance(query, text)
                            scored.append((score, tip))
                        scored.sort(key=lambda x: -x[0])
                        return [t for _, t in scored[:limit]]
                    except Exception:
                        pass
                return tips[:limit] if tips else []
        except Exception as e:
            logger.debug("memory_bridge: pull failed: %s", e)
        return []

    def get_stats(self) -> Dict[str, int]:
        return {"last_sync_count": self._last_sync_count}
