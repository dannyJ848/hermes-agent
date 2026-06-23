"""learned_lessons — per-turn retrieval of learned lessons for the model.

Pulls from the REAL learning stores (the ones with actual data) and formats
them into a compact [Learned Lessons] block injected alongside [Relevant Skills]
each turn. Reuses the semantic scoring from adaptive_injection to rank lessons
by relevance to the current query.

Data sources (in priority order):
  1. iteration_engine.before_action() — proven approaches + past failure warnings
  2. error_learning.get_preemptive_warning() — error patterns that match the query
  3. cortex_store.get_distilled_tips() — high-confidence verified tips
  4. skill_tracker.get_recommendations() — tools that worked for similar queries
  5. cortex_flywheel.get_behavior_adjustments() — persistent behavior changes

Each source is try/except guarded — a broken store never blocks the others.
The whole block is config-gated (cognitive_orchestrator.learned_lessons_enabled).
"""
from __future__ import annotations

import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

# Token budget for the [Learned Lessons] block. Tuned to ~400 tokens — enough
# for 3-5 high-value lessons, small enough to not bloat the per-turn payload.
DEFAULT_BUDGET_TOKENS = 1600  # ~400 tokens at 4 chars/token


def _collect_candidates(query: str, limit: int = 10) -> List[Tuple[str, str, float]]:
    """Collect lesson candidates from all learning stores.

    Returns list of (text, source, base_score) tuples. The base_score is a
    heuristic priority (0.0-1.0) — will be refined by semantic relevance.
    """
    candidates: List[Tuple[str, str, float]] = []

    # 1. Iteration engine — proven approaches + failure warnings
    try:
        from agent.iteration_engine import get_engine
        engine = get_engine()
        ctx = engine.before_action("__query__", query)
        if ctx.get("warnings"):
            for w in ctx["warnings"][:2]:
                text = f"⚠️ Past failure: {w.get('lesson', '')} (seen {w.get('frequency', 1)}x)"
                candidates.append((text, "iteration_engine", 0.9))
        if ctx.get("proven_approaches"):
            for a in ctx["proven_approaches"][:2]:
                text = f"✓ Proven approach: {a.get('approach', '')} (worked {a.get('frequency', 1)}x)"
                candidates.append((text, "iteration_engine", 0.85))
    except Exception as e:
        logger.debug("learned_lessons: iteration_engine source failed: %s", e)

    # 2. Error learning — preemptive warnings
    try:
        from agent.error_learning import ErrorLearningStore
        store = ErrorLearningStore()
        warning = store.get_preemptive_warning(query)
        if warning and len(warning) > 10:
            candidates.append((f"⚠️ Error pattern: {warning}", "error_learning", 0.8))
    except Exception as e:
        logger.debug("learned_lessons: error_learning source failed: %s", e)

    # 3. Distilled tips — high-confidence verified lessons
    try:
        from agent.cortex_learning import get_learning_engine
        engine = get_learning_engine()
        if hasattr(engine, "store"):
            tips = engine.store.get_distilled_tips(limit=limit)
            for tip in tips:
                if isinstance(tip, dict):
                    text = tip.get("tip_text", "")
                    priority = tip.get("priority", 5)
                    if text and priority >= 5:
                        # Higher priority → higher base score
                        score = 0.5 + (priority / 10.0) * 0.4  # 0.5-0.9
                        candidates.append((f"💡 {text}", "distilled_tips", score))
                elif isinstance(tip, str) and tip:
                    candidates.append((f"💡 {tip}", "distilled_tips", 0.6))
    except Exception as e:
        logger.debug("learned_lessons: distilled_tips source failed: %s", e)

    # 4. Skill tracker — tool recommendations from usage data
    try:
        from agent.skill_tracker import SkillTracker
        tracker = SkillTracker()
        recs = tracker.get_recommendations(query, limit=3)
        for rec in recs:
            if isinstance(rec, str) and rec:
                candidates.append((f"🔧 Recommended tool: {rec}", "skill_tracker", 0.6))
    except Exception as e:
        logger.debug("learned_lessons: skill_tracker source failed: %s", e)

    # 5. Behavior adjustments — persistent behavior changes
    try:
        from agent.cortex_flywheel import get_cortex
        cortex = get_cortex()
        adjustments = cortex.get_behavior_adjustments(limit=3)
        for adj in adjustments:
            if isinstance(adj, str) and adj:
                candidates.append((f"📌 Always do: {adj}", "behavior_adjustments", 0.75))
    except Exception as e:
        logger.debug("learned_lessons: behavior_adjustments source failed: %s", e)

    return candidates


def build_learned_lessons_prompt(
    query: str,
    budget_tokens: int = DEFAULT_BUDGET_TOKENS,
    max_lessons: int = 5,
) -> str:
    """Build the [Learned Lessons] block for per-turn injection.

    Collects candidates from all learning stores, scores them by semantic
    relevance to the query + base priority, and formats the top-N within
    the token budget into a compact block.

    Returns empty string if no lessons are available (graceful degradation).
    """
    if not query or len(query.strip()) < 3:
        return ""

    candidates = _collect_candidates(query)
    if not candidates:
        return ""

    # Score each candidate by semantic relevance to the query + base priority.
    # Reuses the embeddings already loaded for adaptive skills (no extra cost
    # after the first turn — the model is cached on score_relevance._model).
    try:
        from agent.adaptive_injection import score_relevance
        scored = []
        for text, source, base_score in candidates:
            # Semantic relevance (0-1) blended with base priority (50/50)
            relevance = score_relevance(query, text)
            combined = (relevance * 0.5) + (base_score * 0.5)
            scored.append((combined, text, source))
        scored.sort(key=lambda x: -x[0])
    except Exception:
        # If semantic scoring fails, fall back to base_score only
        scored = [(base, text, src) for text, src, base in candidates]
        scored.sort(key=lambda x: -x[0])

    # Select top lessons within budget
    selected: List[str] = []
    used_chars = 0
    budget_chars = budget_tokens * 4  # rough chars-per-token
    for score, text, source in scored[:max_lessons]:
        if used_chars + len(text) > budget_chars and selected:
            break  # Budget exhausted
        selected.append(text)
        used_chars += len(text)

    if not selected:
        return ""

    # Format as a compact block
    lines = ["Lessons from past experience (apply if relevant):"]
    for lesson in selected:
        lines.append(f"  - {lesson}")

    return "\n".join(lines)
