"""subconscious — cognitive subsystem for background whispers and intuition.

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


class Subconscious:
    """Background intuition engine — whispers insights during idle moments."""

    def __init__(self):
        self._ensure_schema()

    def _ensure_schema(self):
        with _cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subconscious_whispers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    whisper TEXT NOT NULL,
                    priority REAL DEFAULT 0.5,
                    triggered INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_whisper_priority ON subconscious_whispers(priority DESC, triggered)
            """)

    def inject_whisper(self, whisper: str, priority: float = 0.5):
        """Inject a background whisper/insight."""
        try:
            with _cursor() as cur:
                cur.execute("""
                    INSERT INTO subconscious_whispers (whisper, priority)
                    VALUES (?, ?)
                """, (whisper, priority))
        except Exception as e:
            logger.debug("inject_whisper failed: %s", e)

    def get_whispers(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get untriggered high-priority whispers."""
        try:
            with _cursor() as cur:
                cur.execute("""
                    SELECT * FROM subconscious_whispers
                    WHERE triggered = 0
                    ORDER BY priority DESC, timestamp DESC
                    LIMIT ?
                """, (limit,))
                return [dict(r) for r in cur.fetchall()]
        except Exception as e:
            logger.debug("get_whispers failed: %s", e)
            return []

    def mark_triggered(self, whisper_id: int):
        """Mark a whisper as triggered."""
        try:
            with _cursor() as cur:
                cur.execute("UPDATE subconscious_whispers SET triggered = 1 WHERE id = ?", (whisper_id,))
        except Exception as e:
            logger.debug("mark_triggered failed: %s", e)

    def process_background_task(self, task: str) -> Optional[str]:
        """Process a background task and return a result."""
        # Stub: could do async processing here
        self.inject_whisper(f"Background task completed: {task[:100]}", priority=0.3)
        return None

    def get_stats(self) -> Dict[str, Any]:
        try:
            with _cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM subconscious_whispers WHERE triggered = 0")
                pending = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM subconscious_whispers WHERE triggered = 1")
                triggered = cur.fetchone()[0]
                return {"pending_whispers": pending, "triggered_whispers": triggered}
        except Exception as e:
            logger.debug("get_stats failed: %s", e)
            return {"pending_whispers": 0, "triggered_whispers": 0}


_subconscious = None


def get_subconscious() -> Subconscious:
    global _subconscious
    if _subconscious is None:
        _subconscious = Subconscious()
    return _subconscious
