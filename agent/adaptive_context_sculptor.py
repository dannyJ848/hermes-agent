"""adaptive_context_sculptor — dynamic context budget management.

Monitors the total injection size (skills + lessons + memory + tool schemas)
and trims to fit when under context pressure. The "budget allocator" — when
context is tight, it decides what to keep and what to cut based on priority:
  1. Essential system prompt (identity, tools) — never cut
  2. [Learned Lessons] — high value, compact
  3. [Relevant Skills] — high value, compact
  4. Memory block — medium value, capped
  5. Tool-output history — first to prune (already handled by tool-prune)

This subsystem doesn't inject content itself — it shapes what OTHERS inject.
"""
from __future__ import annotations

import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# Pressure thresholds (fraction of context window)
PRESSURE_NORMAL = 0.30
PRESSURE_MEDIUM = 0.50
PRESSURE_HIGH = 0.70
PRESSURE_CRITICAL = 0.85


class AdaptiveContextSculptor:
    """Manages context budget allocation across injection blocks."""

    def __init__(self):
        self._last_pressure = "low"
        self._last_total_tokens = 0

    def assess_pressure(self, used_tokens: int, context_length: int) -> str:
        """Assess context pressure level from current usage.

        Returns: 'low' | 'medium' | 'high' | 'critical'
        """
        if context_length <= 0:
            return "low"
        ratio = used_tokens / context_length
        if ratio >= PRESSURE_CRITICAL:
            level = "critical"
        elif ratio >= PRESSURE_HIGH:
            level = "high"
        elif ratio >= PRESSURE_MEDIUM:
            level = "medium"
        else:
            level = "low"
        self._last_pressure = level
        self._last_total_tokens = used_tokens
        return level

    def allocate_budgets(
        self, total_budget_tokens: int, pressure_level: str = "low"
    ) -> Dict[str, int]:
        """Allocate token budgets to each injection block based on pressure.

        Under pressure, lessons/skills get smaller budgets; under normal
        conditions they get full allocation.
        """
        if pressure_level == "critical":
            # Minimal — only the most essential
            return {
                "skills": 200,
                "lessons": 200,
                "memory": 300,
                "adaptive_context": 0,
            }
        elif pressure_level == "high":
            return {
                "skills": 500,
                "lessons": 300,
                "memory": 400,
                "adaptive_context": 200,
            }
        elif pressure_level == "medium":
            return {
                "skills": 1000,
                "lessons": 600,
                "memory": 600,
                "adaptive_context": 400,
            }
        else:  # low
            return {
                "skills": 1500,
                "lessons": 800,
                "memory": 800,
                "adaptive_context": 600,
            }

    def sculpt(
        self,
        skills_block: str = "",
        lessons_block: str = "",
        memory_block: str = "",
        total_budget_tokens: int = 4000,
    ) -> Tuple[str, str, str]:
        """Trim injection blocks to fit within a total budget.

        Returns (trimmed_skills, trimmed_lessons, trimmed_memory).
        Prioritizes lessons > skills > memory when cutting.
        """
        budget_chars = total_budget_tokens * 4
        total = len(skills_block) + len(lessons_block) + len(memory_block)
        if total <= budget_chars:
            return skills_block, lessons_block, memory_block

        # Under pressure: trim memory first, then skills, keep lessons
        memory_budget = min(len(memory_block), budget_chars // 4)
        memory_trimmed = memory_block[:memory_budget]
        remaining = budget_chars - memory_budget

        lessons_budget = min(len(lessons_block), int(remaining * 0.6))
        lessons_trimmed = lessons_block[:lessons_budget]
        remaining -= lessons_budget

        skills_budget = min(len(skills_block), remaining)
        skills_trimmed = skills_block[:skills_budget]

        return skills_trimmed, lessons_trimmed, memory_trimmed

    def get_stats(self) -> Dict:
        return {
            "last_pressure": self._last_pressure,
            "last_total_tokens": self._last_total_tokens,
        }


_sculptor_instance = None


def get_sculptor():
    global _sculptor_instance
    if _sculptor_instance is None:
        _sculptor_instance = AdaptiveContextSculptor()
    return _sculptor_instance
