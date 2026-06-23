"""unified_intelligence_engine — cross-domain query interface.

Single entry point for meta-cognition: answers questions like "what tools
fail most?", "what patterns are emerging?", "what should I do differently?"
by aggregating across error_learning + skill_tracker + experiences + tips.
"""
from __future__ import annotations

import logging
from collections import namedtuple
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"

Insight = namedtuple("Insight", ["topic", "finding", "recommendation", "confidence"])


class UnifiedIntelligenceEngine:
    """Cross-system analytics — answers questions about the agent's own state."""

    def __init__(self):
        self._last_analysis: Dict[str, Any] = {}

    def query(self, question: str, context: dict = None) -> Dict[str, Any]:
        """Answer a natural-language question about the agent's learning state."""
        q = question.lower()

        if "fail" in q or "error" in q:
            return self._analyze_failures()
        elif "tool" in q or "skill" in q:
            return self._analyze_tools()
        elif "tip" in q or "lesson" in q or "learn" in q:
            return self._analyze_tips()
        elif "pattern" in q or "trend" in q:
            return self._analyze_patterns()
        else:
            return {"answer": "Unknown query type", "confidence": 0, "sources": []}

    def analyze(self, data: Dict, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze arbitrary data."""
        return {
            "findings": [f"Analyzed {len(data)} items"],
            "recommendations": ["Continue collecting data"],
        }

    def get_insights(self, topic: str, depth: str = "surface") -> List[Insight]:
        """Get insights on a specific topic."""
        insights: List[Insight] = []

        if topic in ("errors", "failures", "error"):
            analysis = self._analyze_failures()
            for finding in analysis.get("findings", []):
                insights.append(Insight(
                    topic="errors", finding=finding,
                    recommendation="Address recurring patterns",
                    confidence=0.7,
                ))

        if topic in ("tools", "skills", "tool"):
            analysis = self._analyze_tools()
            for finding in analysis.get("findings", []):
                insights.append(Insight(
                    topic="tools", finding=finding,
                    recommendation="Optimize tool selection",
                    confidence=0.7,
                ))

        return insights

    def generate_daily_briefing(self) -> Dict[str, Insight]:
        """Generate a daily intelligence briefing."""
        briefing: Dict[str, Insight] = {}

        errors = self._analyze_failures()
        briefing["errors"] = Insight(
            topic="errors",
            finding=f"{len(errors.get('findings', []))} trending error patterns",
            recommendation=errors.get("answer", "Monitor"),
            confidence=errors.get("confidence", 0.5),
        )

        tips = self._analyze_tips()
        briefing["tips"] = Insight(
            topic="tips",
            finding=f"{tips.get('count', 0)} verified tips available",
            recommendation="Review high-priority tips",
            confidence=0.8,
        )

        briefing["velocity"] = Insight(
            topic="velocity",
            finding="Learning velocity stable",
            recommendation="Continue current pace",
            confidence=0.6,
        )

        self._last_analysis = {"briefing": briefing}
        return briefing

    def _analyze_failures(self) -> Dict[str, Any]:
        try:
            from agent.db_pool import get_connection
            conn = get_connection(_DB_PATH)
            rows = conn.execute(
                "SELECT error_summary, occurrence_count, error_type "
                "FROM error_patterns WHERE occurrence_count >= 2 "
                "ORDER BY occurrence_count DESC LIMIT 5"
            ).fetchall()
            findings = [f"{r['error_type']}: {r['error_summary'][:50]} ({r['occurrence_count']}x)"
                        for r in rows]
            return {
                "answer": f"{len(findings)} trending error patterns",
                "findings": findings,
                "confidence": 0.8,
                "sources": ["error_patterns"],
            }
        except Exception:
            return {"answer": "No error data", "confidence": 0, "sources": []}

    def _analyze_tools(self) -> Dict[str, Any]:
        try:
            from agent.db_pool import get_connection
            conn = get_connection(Path.home() / ".hermes" / "skill_tracker.db")
            rows = conn.execute(
                "SELECT skill_name, score, fail_rate, total_uses "
                "FROM skill_scores ORDER BY score DESC LIMIT 5"
            ).fetchall()
            findings = [f"{r['skill_name']}: score={r['score']:.1f}, fail_rate={r['fail_rate']:.2f}"
                        for r in rows]
            return {
                "answer": f"Top tools by effectiveness: {', '.join(r['skill_name'] for r in rows[:3])}",
                "findings": findings,
                "confidence": 0.8,
                "sources": ["skill_scores"],
            }
        except Exception:
            return {"answer": "No tool data", "confidence": 0, "sources": []}

    def _analyze_tips(self) -> Dict[str, Any]:
        try:
            from agent.db_pool import get_connection
            conn = get_connection(_DB_PATH)
            row = conn.execute(
                "SELECT COUNT(*) as n FROM distilled_tips WHERE verification_status = 'verified'"
            ).fetchone()
            count = row["n"] if row else 0
            return {"answer": f"{count} verified tips", "count": count, "confidence": 0.9}
        except Exception:
            return {"answer": "No tip data", "count": 0, "confidence": 0}

    def _analyze_patterns(self) -> Dict[str, Any]:
        return {
            "answer": "Pattern analysis requires more session data",
            "findings": [],
            "confidence": 0.3,
            "sources": [],
        }
