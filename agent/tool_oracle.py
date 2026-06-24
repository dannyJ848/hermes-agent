"""tool_oracle — predicts the best tools for a task from usage data.

Data-driven tool recommendation using the skill_tracker's 14K+ usage rows.
Scores tools by success_rate × log(frequency) — the same formula
skill_tracker.recalculate_scores uses. Returns ranked suggestions that
the [Learned Lessons] block can surface to the model.
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

_DB_PATH = Path.home() / ".hermes" / "skill_tracker.db"


class ToolOracle:
    """Predicts optimal tools for a task based on historical usage data."""

    def __init__(self):
        self._cache: List[Dict] = []
        self._cache_ts: float = 0.0
        # SkillTracker instance for preference multipliers (stated/explicit
        # tool preferences boost or suppress predictions independent of usage).
        try:
            from agent.skill_tracker import SkillTracker
            self._skill_tracker = SkillTracker()
        except Exception:
            self._skill_tracker = None

    def _ensure_cache(self):
        """Load scored tools from skill_tracker (cached 60s)."""
        import time
        now = time.time()
        if self._cache and (now - self._cache_ts) < 60:
            return
        try:
            from agent.db_pool import get_connection
            conn = get_connection(_DB_PATH)
            rows = conn.execute(
                "SELECT skill_name, total_uses, successes, fail_rate, "
                "avg_latency, score FROM skill_scores "
                "WHERE total_uses >= 3 ORDER BY score DESC LIMIT 50"
            ).fetchall()
            self._cache = [dict(r) for r in rows]
            self._cache_ts = now
        except Exception as e:
            logger.debug("tool_oracle: cache load failed: %s", e)
            self._cache = []

    def predict_tools(self, task: str, limit: int = 3) -> Dict:
        """Predict the best tools for a task.

        Returns {primary, alternatives, confidence}. Uses semantic relevance
        to the task + historical effectiveness score.
        """
        self._ensure_cache()
        if not self._cache:
            return {"primary": "", "alternatives": [], "confidence": 0}

        try:
            from agent.adaptive_injection import score_relevance
            scored = []

            # Inject preferred tools that aren't in the usage-scored cache yet.
            # A preferred tool with low/no usage history still deserves
            # consideration -- the user explicitly wants it.
            cached_names = {t.get("skill_name", "") for t in self._cache}
            if self._skill_tracker:
                try:
                    prefs = self._skill_tracker.get_preferences()
                    for p in prefs:
                        pn = p.get("tool_name", "")
                        if pn and pn not in cached_names and p.get("weight", 1.0) >= 1.0:
                            # Add as a synthetic cache entry with a neutral
                            # historical score; the preference multiplier below
                            # will boost it.
                            self._cache.append({
                                "skill_name": pn,
                                "score": 0.5,  # neutral placeholder
                                "total_uses": 0,
                            })
                except Exception:
                    pass

            for tool in self._cache:
                name = tool.get("skill_name", "")
                # Blend: historical score (0-1) + semantic relevance (0-1)
                hist = min(1.0, tool.get("score", 0) / 2.0)  # normalize log-score
                sem = score_relevance(task, name)
                combined = hist * 0.6 + sem * 0.4
                # Apply preference multiplier: tools the user has stated they
                # prefer get boosted (2.0 = default, 1.5 = prefer), avoided
                # tools get suppressed (0.3). Neutral = 1.0.
                try:
                    pref = self._skill_tracker.preference_multiplier(name)
                    combined *= pref
                except Exception:
                    pass
                scored.append((combined, name, tool))
            scored.sort(key=lambda x: -x[0])
        except Exception:
            scored = [(t.get("score", 0), t.get("skill_name", ""), t) for t in self._cache[:limit]]
            scored.sort(key=lambda x: -x[0])

        if not scored:
            return {"primary": "", "alternatives": [], "confidence": 0}

        top = scored[0]
        alts = [s[1] for s in scored[1:limit]]
        confidence = min(1.0, top[0])
        return {
            "primary": top[1],
            "alternatives": alts,
            "confidence": round(confidence, 2),
        }

    def validate_choice(self, tool: str, task: str) -> Dict:
        """Validate whether a tool choice is optimal for a task."""
        prediction = self.predict_tools(task, limit=5)
        recommended = [prediction["primary"]] + prediction["alternatives"]
        if tool in recommended:
            return {"is_optimal": True, "suggested": tool, "reason": "top-ranked for this task"}
        if prediction["primary"]:
            return {
                "is_optimal": False,
                "suggested": prediction["primary"],
                "reason": f"{prediction['primary']} has higher historical success for similar tasks",
            }
        return {"is_optimal": True, "suggested": tool, "reason": "no data to compare"}

    def get_recommendation(self, task_type: str) -> str:
        """Get a single tool recommendation string."""
        pred = self.predict_tools(task_type, limit=1)
        return pred.get("primary", "")
