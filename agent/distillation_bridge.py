"""distillation_bridge — connects distillation output to behavior_adjustments.

The distillation pipeline produces tips (in distilled_tips table). Some of
those tips are high-signal enough to become PERMANENT behavior adjustments
(in behavior_adjustments table). This bridge identifies which tips warrant
promotion and creates the adjustments.

This is the "tip → adjustment" gap identified in the audit: tips accumulate
but never become persistent behavior changes. This bridge closes that gap.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"
_CORTEX_DB = Path.home() / ".hermes" / "cortex_learning.db"


class DistillationBridge:
    """Bridges distilled tips to persistent behavior adjustments."""

    def __init__(self):
        self._promoted_count = 0

    def distill(self, experiences: List[Dict], min_confidence: float = 0.7) -> List[str]:
        """Distill experiences into tips.

        Takes raw experience data and identifies patterns worth promoting
        to tips (and potentially behavior adjustments).
        """
        tips: List[str] = []
        if not experiences:
            return tips

        # Group by action_type and compute success rates
        by_type: Dict[str, List[Dict]] = {}
        for exp in experiences:
            if isinstance(exp, dict):
                atype = exp.get("action_type", "unknown")
                by_type.setdefault(atype, []).append(exp)

        for atype, exps in by_type.items():
            if len(exps) < 3:
                continue
            successes = sum(1 for e in exps if e.get("result") == "success")
            rate = successes / len(exps)
            if rate >= min_confidence and successes >= 3:
                # High-success pattern → tip
                lesson = exps[0].get("lesson", f"Approach for {atype} works {rate:.0%} of the time")
                if lesson:
                    tips.append(lesson)

        return tips

    def process_research(self, research: str, topic: str = "") -> List[str]:
        """Process research text into actionable tips.

        Extracts actionable sentences from research/conversation text.
        """
        tips: List[str] = []
        if not research:
            return tips

        # Simple heuristic: look for imperative sentences (actionable tips)
        for line in research.split("\n"):
            line = line.strip()
            if not line or len(line) < 20:
                continue
            # Imperative indicators
            first_word = line.split()[0].lower() if line.split() else ""
            if first_word in ("use", "always", "never", "avoid", "prefer", "run", "check", "before", "after", "when"):
                tips.append(line)
            elif line.startswith("- ") or line.startswith("* "):
                tips.append(line[2:])

        return tips[:10]

    def promote_to_adjustments(self, min_priority: int = 8) -> int:
        """Promote high-priority distilled tips to behavior_adjustments.

        This is the key bridge: tips with priority >= min_priority become
        persistent adjustments that get injected via get_behavior_adjustments.
        """
        try:
            from agent.db_pool import get_connection
            # Read high-priority tips
            conn = get_connection(_DB_PATH)
            rows = conn.execute(
                "SELECT tip_hash, tip_text, priority, verification_status "
                "FROM distilled_tips WHERE priority >= ? AND verification_status = 'verified'",
                (min_priority,),
            ).fetchall()

            if not rows:
                return 0

            # Check which are already adjustments (avoid duplicates)
            cortex_conn = get_connection(_CORTEX_DB)
            existing = {r[0] for r in cortex_conn.execute(
                "SELECT trigger FROM behavior_adjustments"
            ).fetchall()}

            promoted = 0
            for row in rows:
                trigger = f"tip:{row['tip_hash']}"
                if trigger in existing:
                    continue
                cortex_conn.execute(
                    "INSERT INTO behavior_adjustments (trigger, adjustment, applied) VALUES (?, ?, 1)",
                    (trigger, row["tip_text"]),
                )
                promoted += 1
            cortex_conn.commit()
            self._promoted_count += promoted
            logger.info("distillation_bridge: promoted %d tips to adjustments", promoted)
            return promoted
        except Exception as e:
            logger.debug("distillation_bridge: promotion failed: %s", e)
            return 0

    def get_stats(self) -> Dict[str, int]:
        return {"promoted_adjustments": self._promoted_count}
