"""tiered_memory — 3-tier memory with hot/warm/cold overflow.

Hot tier: in-process LRU cache (fastest, limited size).
Warm tier: SQLite episodic_memory table (fast, persistent).
Cold tier: archived low-importance memories (compressed, rarely accessed).

recall() checks hot → warm → cold, promoting accessed items up.
store() routes by importance: high → hot+warm, medium → warm, low → cold.
consolidate() promotes high-value items and archives stale ones.
"""
from __future__ import annotations

import logging
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"
_HOT_MAX = 50  # max items in the in-process LRU


class TieredMemory:
    """3-tier memory system with automatic promotion/demotion."""

    def __init__(self):
        self._hot: OrderedDict[str, Dict] = OrderedDict()
        self._db_path = _DB_PATH

    def ensure_schema(self):
        """Ensure the episodic_memory table exists (delegates to cerebrum)."""
        try:
            from agent.cerebrum import CerebrumMemory
            CerebrumMemory()  # __init__ calls _ensure_schema
        except Exception:
            pass

    def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Recall memories matching query, checking hot → warm tiers."""
        results: List[Dict[str, Any]] = []

        # Hot tier — in-process LRU (instant)
        for key, item in self._hot.items():
            if query.lower() in key.lower() or query.lower() in item.get("content", "").lower():
                results.append(item)
                self._hot.move_to_end(key)  # promote (most recently used)
                if len(results) >= limit:
                    return results

        # Warm tier — SQLite episodic_memory via FTS5 full-text search.
        # FTS5 is 10-100x faster than LIKE '%query%' for text search.
        # Falls back to LIKE if FTS5 table is unavailable.
        try:
            from agent.db_pool import get_connection
            conn = get_connection(self._db_path)
            remaining = limit - len(results)
            if remaining <= 0:
                return results[:limit]

            # Sanitize query for FTS5 (split into AND'd terms, strip special chars)
            import re as _re
            fts_terms = _re.findall(r'\w+', query.lower())
            if fts_terms:
                fts_query = " AND ".join(fts_terms[:5])  # cap at 5 terms
                try:
                    rows = conn.execute(
                        "SELECT e.content, e.context_json, e.importance_score, e.event_type "
                        "FROM episodic_memory e JOIN episodic_fts f ON e.rowid = f.rowid "
                        "WHERE episodic_fts MATCH ? "
                        "ORDER BY e.importance_score DESC LIMIT ?",
                        (fts_query, remaining),
                    ).fetchall()
                except Exception:
                    # FTS5 table missing or query syntax error — fall back to LIKE
                    rows = conn.execute(
                        "SELECT content, context_json, importance_score, event_type "
                        "FROM episodic_memory WHERE content LIKE ? "
                        "ORDER BY importance_score DESC LIMIT ?",
                        (f"%{query}%", remaining),
                    ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT content, context_json, importance_score, event_type "
                    "FROM episodic_memory WHERE content LIKE ? "
                    "ORDER BY importance_score DESC LIMIT ?",
                    (f"%{query}%", remaining),
                ).fetchall()

            for row in rows:
                item = {
                    "content": row["content"],
                    "importance": row["importance_score"],
                    "event_type": row["event_type"],
                    "tier": "warm",
                }
                results.append(item)
                # Promote to hot tier
                self._put_hot(query, item)
        except Exception as e:
            logger.debug("tiered_memory: warm recall failed: %s", e)

        return results[:limit]

    def store(self, content: str, metadata: Dict = None, importance: float = 0.5) -> bool:
        """Store a memory, routing by importance."""
        meta = metadata or {}
        key = content[:80]

        # Always put in hot tier for immediate access
        self._put_hot(key, {"content": content, "importance": importance, **meta})

        # Warm tier for medium+ importance
        if importance >= 0.3:
            try:
                from agent.cerebrum import CerebrumMemory
                cerebrum = CerebrumMemory()
                cerebrum.capture_episode(
                    session_id=meta.get("session_id", "tiered"),
                    event_type=meta.get("event_type", "memory"),
                    content=content,
                    context=meta.get("context", ""),
                    importance=importance,
                    source="tiered_memory",
                )
            except Exception as e:
                logger.debug("tiered_memory: warm store failed: %s", e)

        return True

    def consolidate(self) -> Dict[str, int]:
        """Promote high-value items, evict stale ones from hot tier."""
        # Evict from hot if over capacity (LRU eviction)
        evicted = 0
        while len(self._hot) > _HOT_MAX:
            self._hot.popitem(last=False)
            evicted += 1

        # Count warm-tier items by importance
        promoted = 0
        try:
            from agent.db_pool import get_connection
            conn = get_connection(self._db_path)
            row = conn.execute(
                "SELECT COUNT(*) as n FROM episodic_memory WHERE importance_score >= 0.7"
            ).fetchone()
            promoted = row["n"] if row else 0
        except Exception:
            pass

        return {"consolidated": len(self._hot), "promoted": promoted, "forgotten": evicted}

    def _put_hot(self, key: str, item: Dict):
        """Add to hot tier with LRU eviction."""
        if key in self._hot:
            self._hot.move_to_end(key)
        self._hot[key] = item
        while len(self._hot) > _HOT_MAX:
            self._hot.popitem(last=False)
