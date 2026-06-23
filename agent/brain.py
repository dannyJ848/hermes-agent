"""brain — cross-system synthesis and cognitive cycle.

The ParallelBrain aggregates signals from ALL other subsystems at session
end to produce a session intelligence briefing: what errors are trending,
what skills are degrading, what tips are high-confidence, what adjustments
are active. This is the "meta-cognition" layer — the system thinking about
its own learning state.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"


class Brain:
    """Minimal brain wrapper — delegates to ParallelBrain."""

    def __init__(self):
        self._brain = ParallelBrain()

    def run_cycle(self) -> Dict[str, Any]:
        return self._brain.run_cycle()


class ParallelBrain:
    """6-phase cognitive cycle: perceive → reason → plan → act → reflect → learn."""

    def __init__(self):
        self._cycle_count = 0
        self._last_briefing: Dict[str, Any] = {}

    def perceive(self, observation: str) -> Dict[str, Any]:
        """Process an observation into structured perception."""
        return {
            "observation": observation,
            "timestamp": time.time(),
            "salience": min(1.0, len(observation) / 200.0),
        }

    def reason(self, query: str, context: List = None) -> Dict[str, Any]:
        """Apply reasoning — aggregates context for the query."""
        return {
            "query": query,
            "context_size": len(context) if context else 0,
            "conclusion": "analyzed",
            "confidence": 0.7,
        }

    def act(self, decision: str, context: Dict = None) -> Dict[str, Any]:
        """Record a decision."""
        return {"action": decision, "status": "recorded", "context": context or {}}

    def reflect(self, episode: Dict) -> Dict[str, Any]:
        """Reflect on an episode — extract insights."""
        insights: List[str] = []
        if episode.get("success"):
            insights.append("Successful pattern — consider reinforcing")
        if episode.get("error"):
            insights.append(f"Error encountered: {episode['error'][:80]}")
        return {"episode": episode, "insights": insights, "lessons": []}

    def run_cycle(self) -> Dict[str, Any]:
        """Run a full synthesis cycle — produces the session intelligence briefing.

        Aggregates signals from error_learning, skill_tracker, distilled_tips,
        behavior_adjustments, and experiences to answer: what did we learn?
        """
        self._cycle_count += 1
        briefing: Dict[str, Any] = {
            "cycle": self._cycle_count,
            "timestamp": time.time(),
            "signals": {},
        }

        try:
            from agent.db_pool import get_connection
            conn = get_connection(_DB_PATH)

            # Error signal — trending failure patterns
            try:
                rows = conn.execute(
                    "SELECT error_summary, occurrence_count FROM error_patterns "
                    "WHERE occurrence_count >= 2 ORDER BY occurrence_count DESC LIMIT 3"
                ).fetchall()
                briefing["signals"]["trending_errors"] = [
                    {"summary": r["error_summary"][:60], "count": r["occurrence_count"]}
                    for r in rows
                ]
            except Exception:
                pass

            # Tip signal — high-confidence tips count
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as n, AVG(priority) as avg_pri FROM distilled_tips "
                    "WHERE verification_status = 'verified'"
                ).fetchone()
                briefing["signals"]["tip_coverage"] = {
                    "verified_count": row["n"] if row else 0,
                    "avg_priority": round(row["avg_pri"], 1) if row and row["avg_pri"] else 0,
                }
            except Exception:
                pass

            # Experience signal — recent learning velocity
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as n FROM experiences "
                    "WHERE last_seen > strftime('%s','now') - 86400"
                ).fetchone()
                briefing["signals"]["daily_experiences"] = row["n"] if row else 0
            except Exception:
                pass

        except Exception as e:
            logger.debug("brain: synthesis failed: %s", e)

        # Behavior adjustments signal
        try:
            from agent.cortex_flywheel import get_cortex
            cortex = get_cortex()
            adjustments = cortex.get_behavior_adjustments(limit=100)
            briefing["signals"]["active_adjustments"] = len(adjustments)
        except Exception:
            pass

        # Overall health
        signals = briefing.get("signals", {})
        health = 0.5
        if signals.get("tip_coverage", {}).get("verified_count", 0) > 50:
            health += 0.15
        if signals.get("active_adjustments", 0) > 5:
            health += 0.15
        if not signals.get("trending_errors"):
            health += 0.1
        briefing["health_score"] = min(1.0, health)

        self._last_briefing = briefing
        logger.info("[BRAIN] Cycle %d: health=%.2f, signals=%s",
                    self._cycle_count, health, list(signals.keys()))
        return briefing

    def get_last_briefing(self) -> Dict[str, Any]:
        return self._last_briefing
