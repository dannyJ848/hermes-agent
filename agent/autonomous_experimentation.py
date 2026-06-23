"""autonomous_experimentation — A/B testing for behavior adjustments.

Proposes experiments to test whether behavior adjustments actually improve
outcomes. Low-frequency: runs at session end when there's enough data.
Example: "Does injecting error warnings before git commits reduce failures?"
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_DB_PATH = Path.home() / ".hermes" / "cortex_learning.db"


class AutonomousExperimentation:
    """Top-level experimentation wrapper."""

    def __init__(self):
        self._loop = AutonomousExperimentationLoop()

    def run_experiment(self, hypothesis: str, params: Dict = None) -> Dict:
        return self._loop.run_experiment(hypothesis, params)

    def suggest(self, context: str) -> List:
        return self._loop.suggest(context)


class AutonomousExperimentationLoop:
    """Proposes and evaluates A/B tests for behavior adjustments."""

    def __init__(self):
        self._experiments: Dict[str, Dict] = {}
        self._ensure_schema()

    def _ensure_schema(self):
        try:
            from agent.db_pool import get_connection
            conn = get_connection(_DB_PATH)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hypothesis TEXT,
                    adjustment TEXT,
                    start_time REAL,
                    end_time REAL,
                    baseline_rate REAL,
                    experiment_rate REAL,
                    validated INTEGER DEFAULT 0,
                    result TEXT DEFAULT 'pending'
                )
            """)
            conn.commit()
        except Exception:
            pass

    def run_experiment(self, hypothesis: str, params: Dict = None) -> Dict[str, Any]:
        """Record an experiment hypothesis (evaluation happens over time)."""
        exp_id = f"exp_{int(time.time())}"
        self._experiments[exp_id] = {
            "hypothesis": hypothesis,
            "params": params or {},
            "start_time": time.time(),
            "validated": False,
        }
        try:
            from agent.db_pool import get_connection
            conn = get_connection(_DB_PATH)
            conn.execute(
                "INSERT INTO experiments (hypothesis, start_time, result) VALUES (?, ?, 'pending')",
                (hypothesis, time.time()),
            )
            conn.commit()
        except Exception:
            pass
        return {"hypothesis": hypothesis, "id": exp_id, "result": "started", "validated": False}

    def suggest(self, context: str) -> List[str]:
        """Suggest experiments based on current data gaps."""
        suggestions: List[str] = []
        try:
            from agent.db_pool import get_connection
            conn = get_connection(_DB_PATH)
            # Suggest testing adjustments that have no experiment yet
            adjustments = conn.execute(
                "SELECT trigger, adjustment FROM behavior_adjustments WHERE applied = 1 LIMIT 3"
            ).fetchall()
            for adj in adjustments:
                suggestions.append(
                    f"Test whether '{adj['adjustment'][:50]}' improves success rate"
                )
        except Exception:
            pass
        return suggestions[:3]

    def get_results(self, experiment_id: str = "") -> List[Dict]:
        """Get experiment results."""
        try:
            from agent.db_pool import get_connection
            conn = get_connection(_DB_PATH)
            if experiment_id:
                rows = conn.execute(
                    "SELECT * FROM experiments WHERE id = ?", (experiment_id,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM experiments ORDER BY start_time DESC LIMIT 5"
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
