"""cortex_flywheel — cognitive subsystem for continuous learning momentum."""

import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Any, Optional


class CortexFlywheel:
    """Cortex flywheel for continuous learning momentum.
    
    Tracks learning velocity, behavior adjustments, and flywheel health.
    Persists to SQLite for cross-session continuity.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (Path.home() / ".hermes" / "cortex_learning.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()
        self._session_start = time.time()
        self._action_count = 0
        self._success_count = 0
    
    def _ensure_schema(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(str(self.db_path))
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS learning_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                subsystem TEXT,
                detail TEXT,
                value REAL DEFAULT 0,
                created_at REAL DEFAULT (unixepoch())
            );
            CREATE TABLE IF NOT EXISTS behavior_adjustments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger TEXT,
                adjustment TEXT,
                applied INTEGER DEFAULT 0,
                created_at REAL DEFAULT (unixepoch())
            );
            CREATE TABLE IF NOT EXISTS flywheel_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric TEXT NOT NULL,
                value REAL,
                recorded_at REAL DEFAULT (unixepoch())
            );
        """)
        conn.commit()
        conn.close()
    
    def record_event(self, event_type: str, subsystem: str = "", detail: str = "", value: float = 0):
        """Record a learning event."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO learning_events (event_type, subsystem, detail, value) VALUES (?, ?, ?, ?)",
            (event_type, subsystem, detail, value)
        )
        conn.commit()
        conn.close()
        self._action_count += 1
        if event_type == "success":
            self._success_count += 1
    
    def get_behavior_adjustments(self, limit: int = 5) -> List[str]:
        """Get recent behavior adjustments for context injection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT adjustment FROM behavior_adjustments WHERE applied = 1 ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return [r["adjustment"] for r in rows if "adjustment" in r]
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Return flywheel health and learning velocity stats."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        # Event counts
        cursor = conn.execute(
            "SELECT event_type, COUNT(*) as count FROM learning_events GROUP BY event_type"
        )
        events = {row["event_type"]: row["count"] for row in cursor.fetchall()}
        
        # Recent adjustments
        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM behavior_adjustments WHERE applied = 1"
        )
        adjustments = cursor.fetchone()["count"]
        
        # Health metrics
        cursor = conn.execute(
            "SELECT metric, value FROM flywheel_health ORDER BY recorded_at DESC LIMIT 10"
        )
        health = {row["metric"]: row["value"] for row in cursor.fetchall()}
        
        conn.close()
        
        session_duration = time.time() - self._session_start
        success_rate = self._success_count / max(self._action_count, 1)
        
        return {
            "total_events": sum(events.values()),
            "events_by_type": events,
            "behavior_adjustments": adjustments,
            "health_metrics": health,
            "session_duration_sec": round(session_duration, 1),
            "action_count": self._action_count,
            "success_rate": round(success_rate, 2),
            "learning_velocity": round(self._action_count / max(session_duration, 1), 2),
        }
    
    def add_behavior_adjustment(self, trigger: str, adjustment: str):
        """Add a new behavior adjustment."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO behavior_adjustments (trigger, adjustment, applied) VALUES (?, ?, 1)",
            (trigger, adjustment)
        )
        conn.commit()
        conn.close()
    
    def record_health(self, metric: str, value: float):
        """Record a health metric."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO flywheel_health (metric, value) VALUES (?, ?)",
            (metric, value)
        )
        conn.commit()
        conn.close()


# Global singleton instance
_cortex_instance: Optional["CortexFlywheel"] = None


def get_cortex() -> "CortexFlywheel":
    """Return the global CortexFlywheel singleton."""
    global _cortex_instance
    if _cortex_instance is None:
        _cortex_instance = CortexFlywheel()
    return _cortex_instance
