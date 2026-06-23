"""attention_context_prioritizer — decides which lessons to inject per turn.

Given a set of candidate lessons (from multiple sources) and a token budget,
selects the top-N most relevant + high-confidence items. Uses the same
semantic scoring as adaptive_injection (no extra embedding cost after the
first turn). Acts as the "attention filter" — not everything learned is
worth injecting every turn.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class AttentionContextPrioritizer:
    """Ranks and filters lesson candidates for per-turn injection."""

    def __init__(self):
        self._last_injection: List[str] = []
        self._injection_count = 0

    def get_injection(
        self,
        query: str,
        candidates: List[Tuple[str, str, float]] = None,
        budget_chars: int = 1600,
        max_items: int = 5,
    ) -> str:
        """Select the top lessons to inject this turn and return as a string.

        Backward-compatible with the old stub signature (query, context="").
        """
        if candidates is None:
            return ""
        selected = self.prioritize(candidates, query, budget_chars, max_items)
        self._last_injection = selected[:]
        self._injection_count += 1
        return "\n".join(selected) if selected else ""

    def prioritize(
        self,
        items: List[Tuple[str, str, float]],
        query: str,
        budget_chars: int = 1600,
        max_items: int = 5,
    ) -> List[str]:
        """Rank and select items by semantic relevance + base score.

        Args:
            items: list of (text, source, base_score) tuples
            query: the current user query
            budget_chars: max total chars
            max_items: max number of items

        Returns: list of selected strings, within budget.
        """
        if not items or not query:
            return []

        try:
            from agent.adaptive_injection import score_relevance
            scored = []
            for text, source, base_score in items:
                relevance = score_relevance(query, text)
                combined = (relevance * 0.5) + (base_score * 0.4)
                scored.append((combined, text))
            scored.sort(key=lambda x: -x[0])
        except Exception:
            scored = [(base, text) for text, _, base in items]
            scored.sort(key=lambda x: -x[0])

        selected: List[str] = []
        used = 0
        for score, text in scored[:max_items]:
            if used + len(text) > budget_chars and selected:
                break
            selected.append(text)
            used += len(text)
        return selected

    def get_context(self, query: str, max_tokens: int = 1000) -> str:
        """Get relevant context — backward-compatible stub."""
        return ""

    def get_stats(self) -> Dict:
        """Return prioritizer stats for the scorecard."""
        return {
            "total_injections": self._injection_count,
            "last_count": len(self._last_injection),
        }
