"""epistemic_trust_scorer — confidence scoring for learned lessons.

Assigns a trust tier (🥇/🥈/🥉) to each lesson based on:
  - Source reliability: verified distilled tip > raw experience > inferred
  - Corroboration count: how many times the pattern was observed
  - Age: recent observations weighted higher than stale ones

This is the quality gate for the [Learned Lessons] block — low-trust
lessons are filtered out so the model only sees high-confidence guidance.
The orchestrator's before_action calls score_fact() to filter lessons.
"""
from __future__ import annotations

import logging
import time
from collections import namedtuple
from typing import Dict, Optional

logger = logging.getLogger(__name__)

TrustScore = namedtuple(
    "TrustScore",
    ["overall_trust", "trust_tier", "source_reliability", "corroboration", "freshness", "category"],
)

# Source reliability weights — verified data > raw observations > inference
_SOURCE_WEIGHTS = {
    "distilled_tips": 0.95,      # verified by distillation pipeline
    "behavior_adjustments": 0.90, # promoted from tips after reflection
    "iteration_engine": 0.80,    # deduped experience data
    "error_learning": 0.75,      # observed error patterns
    "skill_tracker": 0.70,       # usage statistics
    "cerebrum": 0.60,            # raw episodic memory
    "inferred": 0.40,            # heuristic/guessed
    "unknown": 0.50,
}


class EpistemicTrustScorer:
    """Scores the trustworthiness of learned facts/lessons."""

    def __init__(self):
        self._scored_count = 0

    def score_fact(
        self,
        content: str = "",
        source: str = "unknown",
        grounding: str = "",
        category: str = "general",
        corroboration: int = 1,
        age_hours: float = 0.0,
    ) -> TrustScore:
        """Score the trustworthiness of a fact or lesson.

        Args:
            content: the fact/lesson text
            source: where it came from (see _SOURCE_WEIGHTS keys)
            grounding: supporting evidence text
            category: fact type (tool_usage, error_pattern, workflow, etc.)
            corroboration: number of independent observations
            age_hours: hours since last verified

        Returns: TrustScore namedtuple with overall_trust (0-1), tier (🥇/🥈/🥉).
        """
        # Source reliability (0-1)
        source_rel = _SOURCE_WEIGHTS.get(source, 0.50)

        # Corroboration factor — log scale, capped at 1.0
        import math
        corroboration_score = min(1.0, math.log1p(max(0, corroboration)) / math.log(10))

        # Freshness — decays over 30 days, floor at 0.3
        if age_hours <= 0:
            freshness = 1.0
        else:
            decay = max(0.3, 1.0 - (age_hours / (30 * 24)))
            freshness = decay

        # Grounding bonus — having supporting evidence adds 0-0.1
        grounding_bonus = 0.1 if grounding and len(grounding) > 20 else 0.0

        # Weighted combination
        overall = (
            source_rel * 0.45
            + corroboration_score * 0.30
            + freshness * 0.15
            + grounding_bonus
        )
        overall = min(1.0, max(0.0, overall))

        # Tier assignment
        if overall >= 0.75:
            tier = "🥇"  # gold — high confidence
        elif overall >= 0.55:
            tier = "🥈"  # silver — moderate confidence
        else:
            tier = "🥉"  # bronze — low confidence, filter unless only source

        self._scored_count += 1
        return TrustScore(
            overall_trust=round(overall, 3),
            trust_tier=tier,
            source_reliability=round(source_rel, 3),
            corroboration=corroboration_score,
            freshness=round(freshness, 3),
            category=category,
        )

    def should_inject(self, score: TrustScore, min_trust: float = 0.55) -> bool:
        """Decide whether a lesson with this score should be injected."""
        return score.overall_trust >= min_trust

    def filter_lessons(self, lessons: list, min_trust: float = 0.55) -> list:
        """Filter a list of (content, source, corroboration) tuples by trust."""
        filtered = []
        for item in lessons:
            if isinstance(item, tuple) and len(item) >= 3:
                content, source, corroboration = item[0], item[1], item[2]
                score = self.score_fact(content=content, source=source, corroboration=corroboration)
                if self.should_inject(score, min_trust):
                    filtered.append(item)
            elif isinstance(item, str):
                # Bare string — assume unknown source, minimal trust
                score = self.score_fact(content=item, source="unknown")
                if self.should_inject(score, min_trust):
                    filtered.append(item)
        return filtered

    def get_stats(self) -> Dict:
        return {"total_scored": self._scored_count}


_trust_scorer_instance: Optional[EpistemicTrustScorer] = None


def get_trust_scorer() -> EpistemicTrustScorer:
    global _trust_scorer_instance
    if _trust_scorer_instance is None:
        _trust_scorer_instance = EpistemicTrustScorer()
    return _trust_scorer_instance
