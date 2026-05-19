#!/usr/bin/env python3
"""
Cortex Flywheel — Continuous learning engine.

Loop: Experience → Capture → Reflect → Distill → Apply → Measure → Experience
"""

import sqlite3
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

HERMES_HOME = Path.home() / ".hermes"
CORTEX_DB = HERMES_HOME / "cortex.db"

# Import cerebrum for tip storage (lazy to avoid circular)
def _get_cerebrum():
    try:
        from agent.cerebrum import get_cerebrum
        return get_cerebrum()
    except Exception:
        return None


def _safe(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            print(f"[cortex] {fn.__name__} failed: {e}")
            if fn.__name__.startswith("get_") or fn.__name__.startswith("query_"):
                return []
            if fn.__name__.startswith("count_"):
                return 0
            return None
    return wrapper


class CortexFlywheel:
    """Continuous learning engine with experience capture and reflection."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or CORTEX_DB
        self._ensure_db()
        self.cerebrum = _get_cerebrum()

    def _ensure_db(self):
        try:
            HERMES_HOME.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS experience_captures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    capture_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    outcome TEXT,
                    lessons TEXT,
                    tags TEXT,
                    timestamp REAL DEFAULT (julianday('now'))
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reflection_cycles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_number INTEGER UNIQUE,
                    period_start REAL,
                    period_end REAL,
                    experiences_analyzed INTEGER,
                    patterns_found TEXT,
                    tips_generated INTEGER,
                    consolidation_summary TEXT,
                    timestamp REAL DEFAULT (julianday('now'))
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    context TEXT,
                    timestamp REAL DEFAULT (julianday('now'))
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS skill_candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_name TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    evidence_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'pending',
                    created_at REAL DEFAULT (julianday('now'))
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[cortex] DB init failed: {e}")

    @_safe
    def capture_experience(self, session_id: str, capture_type: str, description: str,
                          outcome: Optional[str] = None, lessons: Optional[str] = None,
                          tags: Optional[List[str]] = None) -> Optional[int]:
        """Capture a learning experience."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO experience_captures (session_id, capture_type, description, outcome, lessons, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, capture_type, description, outcome, lessons,
              json.dumps(tags) if tags else None))
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        # Also store in cerebrum episodic
        if self.cerebrum:
            self.cerebrum.capture_episode(
                session_id, capture_type, description,
                context={"outcome": outcome, "lessons": lessons, "tags": tags},
                importance=0.7 if capture_type == "error" else 0.5
            )
        return row_id

    @_safe
    def get_recent_experiences(self, hours: int = 24, capture_type: Optional[str] = None) -> List[Dict]:
        """Get experiences from the last N hours."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM experience_captures WHERE timestamp >= julianday('now', ?)"
        params = [f"-{hours} hours"]
        if capture_type:
            query += " AND capture_type = ?"
            params.append(capture_type)
        query += " ORDER BY timestamp DESC"
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @_safe
    def run_reflection_cycle(self) -> Dict[str, Any]:
        """Analyze recent experiences, find patterns, generate tips."""
        experiences = self.get_recent_experiences(hours=24)
        if len(experiences) < 3:
            return {"status": "skipped", "reason": "insufficient_experiences", "count": len(experiences)}

        # Pattern detection
        patterns = self._detect_patterns(experiences)
        tips = []
        for pattern in patterns:
            tip = self._pattern_to_tip(pattern)
            if tip and self.cerebrum:
                self.cerebrum.store_tip(
                    tip["topic"], tip["text"], priority=tip["priority"],
                    source_sessions=tip["sessions"]
                )
                tips.append(tip)

        # Record cycle
        cycle_num = self._record_cycle(len(experiences), patterns, len(tips))

        # Update metrics
        self._record_metric("reflection_cycles", 1)
        self._record_metric("tips_generated_24h", len(tips))
        self._record_metric("experiences_captured_24h", len(experiences))

        return {
            "status": "completed",
            "cycle_number": cycle_num,
            "experiences_analyzed": len(experiences),
            "patterns_found": len(patterns),
            "tips_generated": len(tips),
            "tips": tips
        }

    def _detect_patterns(self, experiences: List[Dict]) -> List[Dict]:
        """Find repeated patterns in experiences."""
        # Group by capture_type
        by_type = {}
        for exp in experiences:
            ct = exp["capture_type"]
            by_type.setdefault(ct, []).append(exp)

        patterns = []
        for ct, exps in by_type.items():
            if len(exps) >= 2:
                # Extract common words
                words = []
                for e in exps:
                    words.extend(re.findall(r"\b[a-z]{4,}\b", e["description"].lower()))
                from collections import Counter
                common = Counter(words).most_common(3)
                if common:
                    patterns.append({
                        "type": ct,
                        "frequency": len(exps),
                        "common_terms": [w for w, c in common],
                        "descriptions": [e["description"] for e in exps],
                        "outcomes": [e.get("outcome") for e in exps if e.get("outcome")],
                        "lessons": [e.get("lessons") for e in exps if e.get("lessons")],
                        "session_ids": list(set(e["session_id"] for e in exps))
                    })
        return patterns

    def _pattern_to_tip(self, pattern: Dict) -> Optional[Dict]:
        """Convert a detected pattern into a distilled tip."""
        if not pattern["lessons"]:
            return None
        best_lesson = max(pattern["lessons"], key=len) if pattern["lessons"] else ""
        if len(best_lesson) < 10:
            return None
        topic = " ".join(pattern["common_terms"][:2]) if pattern["common_terms"] else pattern["type"]
        priority = min(5 + pattern["frequency"], 9)
        return {
            "topic": topic,
            "text": best_lesson,
            "priority": priority,
            "sessions": pattern["session_ids"]
        }

    @_safe
    def _record_cycle(self, exp_count: int, patterns: List[Dict], tips_count: int) -> int:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(cycle_number) FROM reflection_cycles")
        row = cursor.fetchone()
        cycle_num = (row[0] or 0) + 1
        cursor.execute('''
            INSERT INTO reflection_cycles (cycle_number, period_start, period_end,
                                           experiences_analyzed, patterns_found, tips_generated)
            VALUES (?, julianday('now', '-1 day'), julianday('now'), ?, ?, ?)
        ''', (cycle_num, exp_count, json.dumps([p["type"] for p in patterns]), tips_count))
        conn.commit()
        conn.close()
        return cycle_num

    @_safe
    def _record_metric(self, name: str, value: float, context: Optional[str] = None):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO learning_metrics (metric_name, metric_value, context)
            VALUES (?, ?, ?)
        ''', (name, value, context))
        conn.commit()
        conn.close()

    @_safe
    def get_behavior_adjustments(self, limit: int = 10) -> List[str]:
        """Get context-ready tips for behavior adjustment."""
        if not self.cerebrum:
            return []
        tips = self.cerebrum.get_all_tips(limit=limit)
        return [f"[{t['priority']}] {t['topic']}: {t['tip_text']}" for t in tips
                if t.get("verification_status") != "deprecated"]

    @_safe
    def get_skill_candidates(self, min_evidence: int = 3) -> List[Dict]:
        """Get patterns ready for skill promotion."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM skill_candidates
            WHERE evidence_count >= ? AND status = 'pending'
            ORDER BY success_rate DESC
        ''', (min_evidence,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @_safe
    def promote_skill_candidate(self, candidate_name: str) -> bool:
        """Mark a candidate as promoted (manual step to create actual skill)."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("UPDATE skill_candidates SET status = 'promoted' WHERE candidate_name = ?",
                      (candidate_name,))
        conn.commit()
        conn.close()
        return True

    @_safe
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        stats = {}
        for table in ["experience_captures", "reflection_cycles", "skill_candidates"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        cursor.execute('''
            SELECT metric_name, AVG(metric_value) FROM learning_metrics
            WHERE timestamp >= julianday('now', '-7 days')
            GROUP BY metric_name
        ''')
        stats["weekly_averages"] = {r[0]: round(r[1], 2) for r in cursor.fetchall()}
        conn.close()
        if self.cerebrum:
            stats["cerebrum"] = self.cerebrum.get_stats()
        return stats


# Singleton
_cortex_instance = None

def get_cortex() -> CortexFlywheel:
    global _cortex_instance
    if _cortex_instance is None:
        _cortex_instance = CortexFlywheel()
    return _cortex_instance
