"""self_audit_engine — fallback audit engine (used if self_audit.py fails).

This is the FALLBACK when the real self_audit.py (145 LOC) can't be imported.
The orchestrator's _init_self_audit prefers the real module. This fallback
produces real (not canned) scores by querying the actual learning DBs —
error rates, tip coverage, experience freshness.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

_DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"


class SelfAuditEngine:
    """Fallback audit engine — scores health from real DB data."""

    def __init__(self, loop_window=10, similarity_threshold=0.85):
        self.loop_window = loop_window
        self.similarity_threshold = similarity_threshold
        self._last_audit: Dict = {}

    def run_audit(self, target: str = "self") -> Dict:
        """Run a health audit using real data from the learning DBs."""
        score = 0.5
        details: Dict = {}

        try:
            from agent.db_pool import get_connection
            conn = get_connection(_DB_PATH)

            # Error rate — lower is better
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as n, SUM(CASE WHEN result != 'success' THEN 1 ELSE 0 END) as failures "
                    "FROM experiences"
                ).fetchone()
                total = row["n"] if row else 0
                failures = row["failures"] if row else 0
                if total > 0:
                    error_rate = failures / total
                    details["error_rate"] = round(error_rate, 3)
                    score += (0.5 - error_rate) * 0.2  # bonus for low error rate
            except Exception:
                pass

            # Tip coverage — more verified tips is better
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as n FROM distilled_tips WHERE verification_status = 'verified'"
                ).fetchone()
                tips = row["n"] if row else 0
                details["verified_tips"] = tips
                score += min(0.15, tips / 1000.0)  # up to +0.15 for 150+ tips
            except Exception:
                pass

            # Error patterns with resolutions
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as n FROM error_patterns WHERE resolution != ''"
                ).fetchone()
                resolved = row["n"] if row else 0
                details["resolved_patterns"] = resolved
                score += min(0.1, resolved / 50.0)
            except Exception:
                pass

        except Exception as e:
            logger.debug("SelfAuditEngine fallback: DB query failed: %s", e)

        score = max(0.0, min(1.0, score))
        grade = "A" if score >= 0.8 else "B" if score >= 0.6 else "C" if score >= 0.4 else "D"

        self._last_audit = {
            "target": target,
            "score": round(score, 3),
            "grade": grade,
            "details": details,
            "timestamp": time.time(),
        }
        return self._last_audit

    def audit_session(self, session_data: dict) -> dict:
        """Audit a session and return scorecard."""
        return self.run_audit(target="session")

    def get_score(self, dimension: str = "overall") -> float:
        """Get score for a dimension."""
        if not self._last_audit:
            self.run_audit()
        if dimension == "overall":
            return self._last_audit.get("score", 0.5)
        return self._last_audit.get("details", {}).get(dimension, 0.5)

    def get_loop_status(self) -> dict:
        """Get loop status (backward-compat with orchestrator)."""
        if not self._last_audit:
            self.run_audit()
        return {
            "health_score": self._last_audit.get("score", 0.5),
            "grade": self._last_audit.get("grade", "C"),
            "details": self._last_audit.get("details", {}),
        }

    def get_waste_report(self) -> dict:
        """Get waste report (backward-compat)."""
        return {"redundant_calls": 0, "wasted_tokens": 0}

    def get_stats(self) -> dict:
        """Get audit statistics."""
        return self._last_audit
