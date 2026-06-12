"""brain_cycle — cognitive subsystem for background thought processing.

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


class BrainCycle:
    """Background thought processor — records insights, reflections, and ideas."""

    def __init__(self):
        self._ensure_schema()

    def _ensure_schema(self):
        with _cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS brain_thoughts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thought TEXT NOT NULL,
                    importance REAL DEFAULT 0.5,
                    category TEXT DEFAULT 'general',
                    processed INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_brain_importance ON brain_thoughts(importance DESC, timestamp DESC)
            """)

    def record_thought(self, thought: str, importance: float = 0.5, category: str = "general"):
        """Record a thought or insight."""
        try:
            with _cursor() as cur:
                cur.execute("""
                    INSERT INTO brain_thoughts (thought, importance, category)
                    VALUES (?, ?, ?)
                """, (thought, importance, category))
        except Exception as e:
            logger.debug("record_thought failed: %s", e)

    def get_recent_thoughts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent unprocessed thoughts."""
        try:
            with _cursor() as cur:
                cur.execute("""
                    SELECT * FROM brain_thoughts
                    WHERE processed = 0
                    ORDER BY importance DESC, timestamp DESC
                    LIMIT ?
                """, (limit,))
                return [dict(r) for r in cur.fetchall()]
        except Exception as e:
            logger.debug("get_recent_thoughts failed: %s", e)
            return []

    def get_brain_state(self) -> Dict[str, Any]:
        """Get current brain state summary."""
        try:
            with _cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM brain_thoughts WHERE processed = 0")
                pending = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM brain_thoughts WHERE processed = 1")
                processed = cur.fetchone()[0]
                cur.execute("SELECT AVG(importance) FROM brain_thoughts")
                avg_importance = cur.fetchone()[0] or 0.0
                return {
                    "pending_thoughts": pending,
                    "processed_thoughts": processed,
                    "avg_importance": avg_importance,
                }
        except Exception as e:
            logger.debug("get_brain_state failed: %s", e)
            return {"pending_thoughts": 0, "processed_thoughts": 0, "avg_importance": 0.0}

    def mark_processed(self, thought_id: int):
        """Mark a thought as processed."""
        try:
            with _cursor() as cur:
                cur.execute("UPDATE brain_thoughts SET processed = 1 WHERE id = ?", (thought_id,))
        except Exception as e:
            logger.debug("mark_processed failed: %s", e)

    def get_stats(self) -> Dict[str, Any]:
        return self.get_brain_state()


_brain = None


def get_brain() -> BrainCycle:
    global _brain
    if _brain is None:
        _brain = BrainCycle()
    return _brain
