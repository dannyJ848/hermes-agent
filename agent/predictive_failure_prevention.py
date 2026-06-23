"""predictive_failure_prevention — warns before risky actions using error history.

Scores risk for a proposed action by matching against known error patterns
from error_learning. When an action matches a pattern that has failed ≥2
times, emits a warning with the known failure mode and any recorded resolution.
This is the "guard rail" of the learning loop — it stops the model from
repeating known-bad approaches.
"""
from __future__ import annotations

import logging
from collections import namedtuple
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

RiskAssessment = namedtuple(
    "RiskAssessment", ["risk_level", "risk_score", "mitigation", "confidence", "warnings"]
)

_DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"


class PredictiveFailurePrevention:
    """Assesses risk of actions against historical error patterns."""

    def __init__(self):
        self._warning_cache: List[Dict] = []
        self._cache_ts: float = 0.0

    def _load_patterns(self):
        """Load error patterns with occurrence_count >= 2 (cached 60s)."""
        import time
        now = time.time()
        if self._warning_cache and (now - self._cache_ts) < 60:
            return
        try:
            from agent.db_pool import get_connection
            conn = get_connection(_DB_PATH)
            rows = conn.execute(
                "SELECT fingerprint, error_summary, context, resolution, "
                "occurrence_count, resolution_success_rate "
                "FROM error_patterns WHERE occurrence_count >= 2 "
                "ORDER BY occurrence_count DESC LIMIT 20"
            ).fetchall()
            self._warning_cache = [dict(r) for r in rows]
            self._cache_ts = now
        except Exception as e:
            logger.debug("failure_prevention: pattern load failed: %s", e)
            self._warning_cache = []

    def assess_risk(self, action_type: str, detail: str, context: str = "") -> RiskAssessment:
        """Assess risk of an action against known failure patterns.

        Returns a RiskAssessment with risk_level (low/medium/high), score
        (0-1), mitigations, and warnings for matching patterns.
        """
        self._load_patterns()
        if not self._warning_cache:
            return RiskAssessment(
                risk_level="low", risk_score=0.1,
                mitigation=["Proceed normally"], confidence=0.8, warnings=[],
            )

        action_text = f"{action_type} {detail} {context}".lower()
        warnings: List[str] = []
        mitigations: List[str] = []
        max_score = 0.0

        for pattern in self._warning_cache:
            # Check if action text shares keywords with the error pattern
            error_words = set(pattern.get("error_summary", "").lower().split())
            action_words = set(action_text.split())
            overlap = error_words & action_words
            if len(overlap) >= 1:
                freq = pattern.get("occurrence_count", 1)
                score = min(1.0, freq / 5.0)  # 5+ occurrences = max risk
                max_score = max(max_score, score)
                summary = pattern.get("error_summary", "")[:100]
                warnings.append(f"Past failure ({freq}x): {summary}")
                resolution = pattern.get("resolution", "")
                if resolution:
                    mitigations.append(resolution)

        if max_score >= 0.6:
            level = "high"
        elif max_score >= 0.3:
            level = "medium"
        else:
            level = "low"

        if not mitigations:
            mitigations = ["Proceed normally"] if level == "low" else ["Consider an alternative approach"]

        return RiskAssessment(
            risk_level=level,
            risk_score=round(max_score, 2),
            mitigation=mitigations[:3],
            confidence=0.7 + max_score * 0.2,
            warnings=warnings[:3],
        )

    def predict_failure(self, action: str, context: dict = None) -> dict:
        """Predict failure probability for an action."""
        ctx_str = str(context or "")
        assessment = self.assess_risk(action, ctx_str)
        return {
            "probability": assessment.risk_score,
            "reasons": assessment.warnings,
            "mitigations": assessment.mitigation,
            "level": assessment.risk_level,
        }

    def get_mitigation(self, risk_type: str) -> list:
        """Get mitigations for a risk type."""
        self._load_patterns()
        mitigations = []
        for p in self._warning_cache:
            if risk_type.lower() in p.get("error_summary", "").lower():
                res = p.get("resolution", "")
                if res:
                    mitigations.append(res)
        return mitigations[:3]
