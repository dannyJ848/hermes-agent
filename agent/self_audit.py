"""self_audit — cognitive subsystem for continuous self-evaluation.

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
    """SQLite cursor context manager using the process-level connection pool.

    Avoids 'Cannot operate on a closed cursor' errors that occur when the
    non-pooled sqlite3.connect() connection is closed by another thread
    accessing the same DB during session-end parallel execution.
    """
    from agent.db_pool import get_connection
    conn = get_connection(DB_PATH)
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
        if self.cur is not None:
            try:
                self.cur.close()
            except Exception:
                pass
        # Connection is pooled — not closed here.
        return False


class SelfAudit:
    """Continuous self-evaluation engine."""

    def __init__(self):
        self._ensure_schema()

    def _ensure_schema(self):
        with _cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS self_audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_type TEXT DEFAULT 'general',
                    score REAL DEFAULT 0.0,
                    findings TEXT,
                    recommendations TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def run_audit(self, audit_type: str = "general") -> Dict[str, Any]:
        """Run a self-audit and store results."""
        try:
            # Gather metrics from other tables
            score = 0.5
            findings = []

            with _cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM error_patterns WHERE occurrence_count >= 3")
                frequent_errors = cur.fetchone()[0]
                if frequent_errors > 0:
                    findings.append(f"{frequent_errors} frequent error patterns detected")
                    score -= 0.1 * frequent_errors

                cur.execute("SELECT COUNT(*) FROM distilled_tips")
                tips = cur.fetchone()[0]
                if tips > 0:
                    findings.append(f"{tips} distilled tips available")
                    score += 0.1

                cur.execute("SELECT COUNT(*) FROM experiences WHERE lesson = ''")
                missing_lessons = cur.fetchone()[0]
                if missing_lessons > 0:
                    findings.append(f"{missing_lessons} experiences missing lessons")
                    score -= 0.05

                score = max(0.0, min(1.0, score))

                cur.execute("""
                    INSERT INTO self_audits (audit_type, score, findings, recommendations)
                    VALUES (?, ?, ?, ?)
                """, (audit_type, score, json.dumps(findings), json.dumps(["Run learning loop"])))

            return {
                "score": score,
                "findings": findings,
                "recommendations": ["Run learning loop"],
            }
        except Exception as e:
            logger.debug("run_audit failed: %s", e)
            return {"score": 0.0, "findings": [], "recommendations": []}

    def get_last_audit(self) -> Optional[Dict[str, Any]]:
        """Get the most recent audit."""
        try:
            with _cursor() as cur:
                cur.execute("""
                    SELECT * FROM self_audits
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                row = cur.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.debug("get_last_audit failed: %s", e)
            return None

    def get_audit_score(self) -> float:
        """Get the most recent audit score."""
        audit = self.get_last_audit()
        return audit["score"] if audit else 0.0

    def get_stats(self) -> Dict[str, Any]:
        try:
            with _cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM self_audits")
                total = cur.fetchone()[0]
                cur.execute("SELECT AVG(score) FROM self_audits")
                avg = cur.fetchone()[0] or 0.0
                return {"total_audits": total, "avg_score": avg}
        except Exception as e:
            logger.debug("get_stats failed: %s", e)
            return {"total_audits": 0, "avg_score": 0.0}


_self_audit = None


def get_self_audit() -> SelfAudit:
    global _self_audit
    if _self_audit is None:
        _self_audit = SelfAudit()
    return _self_audit
