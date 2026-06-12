"""skill_tracker — cognitive subsystem for tracking skill effectiveness.

SQLite backend using cerebrum_memory.db.
Uses ? placeholders, INTEGER PRIMARY KEY AUTOINCREMENT, CURRENT_TIMESTAMP.
"""

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)
DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"


def _cursor():
    """SQLite cursor context manager."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return _Ctx(conn)


class _Ctx:
    def __init__(self, conn):
        self.conn = conn
        self.cur = None
    def __enter__(self):
        self.cur = self.conn.cursor()
        return self.cur
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.cur.close()
        self.conn.close()
        return False


class SkillTracker:
    """Track skill usage patterns and effectiveness."""

    def __init__(self):
        self._ensure_schema()

    def _ensure_schema(self):
        with _cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS skill_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT NOT NULL,
                    context TEXT,
                    success INTEGER DEFAULT 0,
                    latency_ms INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_skill_name ON skill_usage(skill_name, timestamp DESC)
            """)

    def track_skill_usage(self, skill_name: str, context: str = None, success: bool = True, latency_ms: int = 0):
        """Record a skill usage event."""
        try:
            with _cursor() as cur:
                cur.execute("""
                    INSERT INTO skill_usage (skill_name, context, success, latency_ms)
                    VALUES (?, ?, ?, ?)
                """, (skill_name, context or "", 1 if success else 0, latency_ms))
        except Exception as e:
            logger.debug("track_skill_usage failed: %s", e)

    def get_skill_stats(self) -> Dict[str, Any]:
        """Get aggregate skill statistics."""
        try:
            with _cursor() as cur:
                cur.execute("""
                    SELECT skill_name,
                           COUNT(*) as uses,
                           SUM(success) as successes,
                           AVG(latency_ms) as avg_latency
                    FROM skill_usage
                    GROUP BY skill_name
                    ORDER BY uses DESC
                """)
                rows = [dict(r) for r in cur.fetchall()]
                return {"skills": rows, "total_uses": sum(r["uses"] for r in rows)}
        except Exception as e:
            logger.debug("get_skill_stats failed: %s", e)
            return {"skills": [], "total_uses": 0}

    def get_skill_recommendations(self, query: str) -> List[str]:
        """Recommend skills based on query context."""
        try:
            with _cursor() as cur:
                words = query.lower().split()[:3]
                if not words:
                    return []
                clauses = " OR ".join(["context LIKE ?" for _ in words])
                params = [f"%{w}%" for w in words]
                cur.execute(f"""
                    SELECT skill_name, COUNT(*) as cnt, SUM(success) as ok
                    FROM skill_usage
                    WHERE {clauses}
                    GROUP BY skill_name
                    ORDER BY ok DESC, cnt DESC
                    LIMIT 5
                """, params)
                return [r["skill_name"] for r in cur.fetchall()]
        except Exception as e:
            logger.debug("get_skill_recommendations failed: %s", e)
            return []

    def get_stats(self) -> Dict[str, Any]:
        return self.get_skill_stats()


_skill_tracker = None


def get_skill_tracker() -> SkillTracker:
    global _skill_tracker
    if _skill_tracker is None:
        _skill_tracker = SkillTracker()
    return _skill_tracker
