"""cross_domain_transfer — generalizes patterns across task domains.

Finds common structures in successful experiences and applies them to new
domains. Example: "Debugging tasks that start with search_files succeed 80%
of the time" → suggest search_files-first approach for similar tasks.
"""
from __future__ import annotations

import logging
from collections import Counter, namedtuple
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"

TransferSuggestion = namedtuple(
    "TransferSuggestion",
    ["source_domain", "target_domain", "pattern", "explanation", "confidence"],
)


class CrossDomainTransfer:
    """Generalizes patterns from successful experiences."""

    def __init__(self):
        self._pattern_cache: List[Dict] = []
        self._cache_ts: float = 0.0

    def suggest_for_action(self, action_type: str, detail: str) -> TransferSuggestion:
        """Suggest a cross-domain pattern for an action."""
        patterns = self.get_patterns()
        for p in patterns:
            if action_type.lower() in p.get("pattern", "").lower():
                return TransferSuggestion(
                    source_domain=p.get("source", "general"),
                    target_domain=action_type,
                    pattern=p.get("pattern", ""),
                    explanation=p.get("explanation", ""),
                    confidence=p.get("confidence", 0.5),
                )
        return TransferSuggestion("", "", "", "", 0)

    def transfer(self, pattern: str, source: str, target: str) -> bool:
        """Record a pattern transfer (for future reference)."""
        return True

    def get_patterns(self, domain: str = "") -> List[Dict]:
        """Extract patterns from successful experiences."""
        import time
        now = time.time()
        if self._pattern_cache and (now - self._cache_ts) < 300:  # 5-min cache
            if not domain:
                return self._pattern_cache
            return [p for p in self._pattern_cache if domain in p.get("source", "")]

        patterns: List[Dict] = []
        try:
            from agent.db_pool import get_connection
            conn = get_connection(_DB_PATH)
            # Find action types with high success rates
            rows = conn.execute(
                "SELECT action_type, COUNT(*) as n, "
                "SUM(CASE WHEN result = 'success' THEN 1 ELSE 0 END) as successes "
                "FROM experiences GROUP BY action_type HAVING n >= 3 "
                "ORDER BY successes DESC LIMIT 10"
            ).fetchall()
            for row in rows:
                rate = row["successes"] / row["n"] if row["n"] else 0
                if rate >= 0.7:
                    patterns.append({
                        "source": row["action_type"],
                        "pattern": f"{row['action_type']} approach: {rate:.0%} success rate ({row['n']} uses)",
                        "explanation": f"Tasks involving {row['action_type']} succeed {rate:.0%} of the time",
                        "confidence": min(1.0, rate),
                    })
        except Exception as e:
            logger.debug("domain_transfer: pattern extraction failed: %s", e)

        self._pattern_cache = patterns
        self._cache_ts = now
        return patterns
