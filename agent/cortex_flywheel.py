"""cortex_flywheel — cognitive subsystem for continuous learning momentum."""

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Process-level connection pool (agent.db_pool).
from agent.db_pool import get_connection

logger = logging.getLogger(__name__)


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
        conn = get_connection(self.db_path)
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
        # Connection pooled — not closed (agent.db_pool).
    
    def record_event(self, event_type: str, subsystem: str = "", detail: str = "", value: float = 0):
        """Record a learning event."""
        conn = get_connection(self.db_path)
        conn.execute(
            "INSERT INTO learning_events (event_type, subsystem, detail, value) VALUES (?, ?, ?, ?)",
            (event_type, subsystem, detail, value)
        )
        conn.commit()
        # Connection pooled — not closed (agent.db_pool).
        self._action_count += 1
        if event_type == "success":
            self._success_count += 1
    
    def get_behavior_adjustments(self, limit: int = 5) -> List[str]:
        """Get recent behavior adjustments for context injection."""
        conn = get_connection(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT adjustment FROM behavior_adjustments WHERE applied = 1 ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        rows = [dict(row) for row in cursor.fetchall()]
        # Connection pooled — not closed (agent.db_pool).
        return [r["adjustment"] for r in rows if "adjustment" in r]
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Return flywheel health and learning velocity stats."""
        conn = get_connection(self.db_path)
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
        # Connection pooled — not closed (agent.db_pool).
        
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
        conn = get_connection(self.db_path)
        conn.execute(
            "INSERT INTO behavior_adjustments (trigger, adjustment, applied) VALUES (?, ?, 1)",
            (trigger, adjustment)
        )
        conn.commit()
        # Connection pooled — not closed (agent.db_pool).
    
    def record_health(self, metric: str, value: float):
        """Record a health metric."""
        conn = get_connection(self.db_path)
        conn.execute(
            "INSERT INTO flywheel_health (metric, value) VALUES (?, ?)",
            (metric, value)
        )
        conn.commit()
        # Connection pooled — not closed (agent.db_pool).

    def capture_experience(self, action_type: str = "", detail: str = "",
                           result: str = "unknown", error: str = "",
                           duration_ms: int = 0):
        """Capture a tool-call experience for the learning loop.

        Called from mega_wiring after each tool execution. Records a
        learning_event AND delegates to cerebrum for episodic storage.
        This is the per-tool experience capture that was previously broken
        (mega_wiring called cortex.capture_experience but the method didn't
        exist — silently swallowed by try/except).
        """
        # Record the event in the flywheel's own table
        event_type = "success" if result == "success" else "failure" if result == "failure" else result
        self.record_event(event_type, subsystem=action_type, detail=detail[:200], value=duration_ms)
        # Also capture an episodic memory in cerebrum (graceful if cerebrum unavailable)
        try:
            from agent.cerebrum import CerebrumMemory
            cerebrum = CerebrumMemory()
            importance = 0.8 if result == "failure" else 0.3
            cerebrum.capture_episode(
                session_id="cortex",
                event_type=f"tool_{result}",
                content=f"{action_type}: {detail[:200]} → {result}" + (f" ({error[:100]})" if error else ""),
                context=detail[:200],
                emotional_valence=-0.5 if result == "failure" else 0.2,
                importance=importance,
                source="cortex_flywheel",
            )
        except Exception:
            pass

    def run_reflection_cycle(self) -> Dict[str, Any]:
        """Run the full reflection + learning cycle at session end.

        Called from mega_wiring's session-end hook (was previously broken —
        the method didn't exist). Orchestrates the learning pipeline:
        1. Distillation (experiences → tips)
        2. Auto-memory extraction (conversation → tips)
        3. Memory learning reweighting
        4. Behavior adjustment identification
        5. Health metric recording

        Each step is try/except guarded — a failure in one doesn't block others.
        Returns a summary of what was learned.
        """
        summary: Dict[str, Any] = {"distillation": 0, "auto_memory": 0, "adjustments": 0}

        # 1. Distillation — turn experiences into distilled tips
        try:
            from agent.distillation import DistillationPipeline
            pipeline = DistillationPipeline()
            new_tips = pipeline.distill_last_24h()
            summary["distillation"] = len(new_tips) if new_tips else 0
        except Exception as e:
            logger.debug("Reflection: distillation failed: %s", e)

        # 2. Auto-memory extraction (conversation → tips) — wired in Phase 3
        # Placeholder; auto_memory needs the session messages which aren't
        # available here. Will be called directly from session_end with msgs.

        # 3. Memory learning reweighting — wired in Phase 3
        # Placeholder; needs session results which come from session_end.

        # 4. Behavior adjustments — identify high-signal patterns
        try:
            adjustments = self._identify_behavior_adjustments()
            for trigger, adjustment in adjustments:
                self.add_behavior_adjustment(trigger, adjustment)
            summary["adjustments"] = len(adjustments)
        except Exception as e:
            logger.debug("Reflection: behavior adjustments failed: %s", e)

        # 5. Record health metrics
        try:
            stats = self.get_learning_stats()
            self.record_health("consolidation_score", min(1.0, summary["distillation"] / 10.0))
            self.record_health("reflection_completed", 1.0)
        except Exception:
            pass

        # Record the reflection event itself
        self.record_event("reflection_cycle", subsystem="cortex",
                          detail=f"distilled={summary['distillation']}, adjustments={summary['adjustments']}",
                          value=float(summary.get("distillation", 0)))

        logger.info("[CORTEX] Reflection cycle: %s", summary)
        return summary

    def _identify_behavior_adjustments(self) -> List[tuple]:
        """Identify patterns that should become persistent behavior adjustments.

        Scans error patterns (from error_learning) and distilled tips for
        high-signal patterns worth promoting to permanent adjustments.
        Returns list of (trigger, adjustment) tuples.
        """
        adjustments: List[tuple] = []

        # Source 1: Error patterns with occurrence_count >= 3
        try:
            from agent.error_learning import ErrorLearningStore
            store = ErrorLearningStore()
            conn = get_connection(Path.home() / ".hermes" / "cerebrum_memory.db")
            rows = conn.execute(
                "SELECT error_summary, context, resolution, occurrence_count "
                "FROM error_patterns WHERE occurrence_count >= 3 "
                "ORDER BY occurrence_count DESC LIMIT 5"
            ).fetchall()
            existing = {r[0] for r in get_connection(self.db_path).execute(
                "SELECT trigger FROM behavior_adjustments"
            ).fetchall()}
            for row in rows:
                trigger = f"error:{row['error_summary'][:80]}"
                if trigger in existing:
                    continue
                fix = row['resolution'] if row['resolution'] else f"Avoid: {row['error_summary'][:100]}"
                adjustments.append((trigger, f"Known failure ({row['occurrence_count']}x): {fix}"))
        except Exception as e:
            logger.debug("Behavior adjustment scan (errors) failed: %s", e)

        # Source 2: High-priority distilled tips
        try:
            from agent.cortex_learning import get_learning_engine
            engine = get_learning_engine()
            if hasattr(engine, 'store'):
                tips = engine.store.get_distilled_tips(limit=10)
                existing = {r[0] for r in get_connection(self.db_path).execute(
                    "SELECT trigger FROM behavior_adjustments"
                ).fetchall()}
                for tip in tips:
                    if isinstance(tip, dict):
                        priority = tip.get('priority', 5)
                        text = tip.get('tip_text', '')
                        if priority >= 8 and text:
                            trigger = f"tip:{text[:60]}"
                            if trigger not in existing:
                                adjustments.append((trigger, text))
        except Exception as e:
            logger.debug("Behavior adjustment scan (tips) failed: %s", e)

        return adjustments[:5]  # Cap to avoid flooding


# Global singleton instance
_cortex_instance: Optional["CortexFlywheel"] = None


def get_cortex() -> "CortexFlywheel":
    """Return the global CortexFlywheel singleton."""
    global _cortex_instance
    if _cortex_instance is None:
        _cortex_instance = CortexFlywheel()
    return _cortex_instance
