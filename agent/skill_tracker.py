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
DEFAULT_DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"
DB_PATH = DEFAULT_DB_PATH  # backwards-compat module-level reference


def _cursor():
    """SQLite cursor context manager (default DB)."""
    return _cursor_for(DEFAULT_DB_PATH)


def _cursor_for(db_path):
    """SQLite cursor context manager for an explicit DB path."""
    conn = sqlite3.connect(str(db_path))
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
    """Track skill usage patterns and effectiveness.

    Accepts optional orchestrator-style kwargs (skills_dir, experiences_db,
    tracker_db) for backwards-compat with CognitiveOrchestrator._init_skill_tracker.
    If `tracker_db` is provided and points to a writable path, uses it;
    otherwise falls back to cerebrum_memory.db.
    """

    def __init__(self, skills_dir: str = None, experiences_db=None,
                 tracker_db: str = None, min_samples: int = 3, **kwargs):
        if tracker_db and Path(tracker_db).parent.exists():
            self._db_path = Path(tracker_db)
        elif experiences_db and Path(experiences_db).parent.exists():
            self._db_path = Path(experiences_db)
        else:
            self._db_path = DEFAULT_DB_PATH
        self._min_samples = min_samples
        self._ensure_schema()

    def _ensure_schema(self):
        with _cursor_for(self._db_path) as cur:
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
            # Aggregate scores table (used by recalculate_scores + orchestrator)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS skill_scores (
                    skill_name TEXT PRIMARY KEY,
                    total_uses INTEGER DEFAULT 0,
                    successes INTEGER DEFAULT 0,
                    fail_rate REAL DEFAULT 0,
                    avg_latency REAL DEFAULT 0,
                    score REAL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def track_skill_usage(self, skill_name: str, context: str = None, success: bool = True, latency_ms: int = 0):
        """Record a skill usage event."""
        try:
            with _cursor_for(self._db_path) as cur:
                cur.execute("""
                    INSERT INTO skill_usage (skill_name, context, success, latency_ms)
                    VALUES (?, ?, ?, ?)
                """, (skill_name, context or "", 1 if success else 0, latency_ms))
        except Exception as e:
            logger.debug("track_skill_usage failed: %s", e)

    # --- Orchestrator adapter API (drop-in compat) ---

    def record_observation(self, skill_name: str, outcome: str = "success",
                           context: str = "", duration_ms: int = 0,
                           source: str = "", **kwargs) -> bool:
        """Orchestrator-compatible skill observation recorder."""
        success = (str(outcome).lower() in ("success", "ok", "pass", "true", "1"))
        self.track_skill_usage(skill_name, context=context or source,
                               success=success, latency_ms=int(duration_ms or 0))
        return True

    def get_recommendations(self, query: str, limit: int = 3) -> List[str]:
        """Orchestrator-compatible recommendation API."""
        recs = self.get_skill_recommendations(query)
        return recs[:limit] if recs else []

    def get_skill_stats(self) -> Dict[str, Any]:
        """Get aggregate skill statistics."""
        try:
            with _cursor_for(self._db_path) as cur:
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
            with _cursor_for(self._db_path) as cur:
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

    def recalculate_scores(self) -> Dict[str, Any]:
        """Recompute aggregate skill_scores table from skill_usage history.

        Score = success_rate * log(1 + total_uses) — rewards both correctness
        and frequency, only computes for skills with >= min_samples observations.
        Returns summary dict.
        """
        try:
            with _cursor_for(self._db_path) as cur:
                cur.execute("""
                    INSERT OR REPLACE INTO skill_scores
                        (skill_name, total_uses, successes, fail_rate,
                         avg_latency, score, updated_at)
                    SELECT
                        skill_name,
                        COUNT(*) AS total_uses,
                        COALESCE(SUM(success), 0) AS successes,
                        1.0 - (1.0 * COALESCE(SUM(success),0) / COUNT(*)) AS fail_rate,
                        COALESCE(AVG(latency_ms), 0) AS avg_latency,
                        (1.0 * COALESCE(SUM(success),0) / COUNT(*)) *
                            LOG(1 + COUNT(*)) AS score,
                        CURRENT_TIMESTAMP
                    FROM skill_usage
                    GROUP BY skill_name
                    HAVING COUNT(*) >= ?
                """, (self._min_samples,))
                cur.execute("SELECT COUNT(*) FROM skill_scores")
                n = cur.fetchone()[0]
                return {"skills_scored": n, "status": "ok"}
        except Exception as e:
            logger.warning("recalculate_scores failed: %s", e)
            return {"skills_scored": 0, "status": "error", "error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        return self.get_skill_stats()


_skill_tracker = None


def get_skill_tracker() -> SkillTracker:
    global _skill_tracker
    if _skill_tracker is None:
        _skill_tracker = SkillTracker()
    return _skill_tracker
