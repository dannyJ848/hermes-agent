"""
Curator Integration for Iteration Pipeline

Wires the Hermes Curator into the agent's per-turn iteration loop so that:
1. After N turns, the curator reviews agent-created skills
2. Tool usage history from predictive_tools.py feeds into curator decisions
3. Error patterns from error_learning.py inform skill quality scoring
4. The curator runs synchronously in the iteration pipeline (not just gateway cron)

This is a lightweight shim — the heavy lifting stays in agent/curator.py.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Curator runs every N turns in the iteration pipeline
CURATOR_TURN_INTERVAL = 50  # Review skills every 50 turns


def maybe_run_curator_in_iteration(
    turn_count: int,
    tool_usage_history: list,
    error_history: list,
    force: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Best-effort curator trigger from the iteration pipeline.
    
    Args:
        turn_count: Current turn number in the session
        tool_usage_history: Recent tool calls from predictive_tools tracking
        error_history: Recent errors from error_learning tracking  
        force: If True, bypass the turn interval gate
    
    Returns:
        Curator result dict if a review was started, else None
    """
    # Gate: only run every N turns unless forced
    if not force and turn_count % CURATOR_TURN_INTERVAL != 0:
        return None
    
    try:
        from agent.curator import maybe_run_curator
        
        # Build a summary of recent activity for the curator's context
        activity_summary = _build_activity_summary(tool_usage_history, error_history)
        
        # Run curator with the activity context
        result = maybe_run_curator(
            idle_for_seconds=float("inf"),  # We're in the pipeline, not waiting for idle
            on_summary=lambda msg: logger.info("curator[iteration]: %s", msg),
        )
        
        if result:
            logger.debug("Curator review triggered at turn %d", turn_count)
            
        return result
        
    except Exception as e:
        logger.debug("Curator iteration hook failed: %s", e)
        return None


def _build_activity_summary(tool_history: list, error_history: list) -> str:
    """Build a text summary of recent agent activity for curator context."""
    parts = []
    
    if tool_history:
        # Count tool usage frequency
        from collections import Counter
        tool_counts = Counter(t.get("tool_name", "unknown") for t in tool_history[-20:])
        top_tools = tool_counts.most_common(5)
        parts.append(f"Recent tools: {', '.join(f'{n}({c})' for n,c in top_tools)}")
    
    if error_history:
        # Count error patterns
        from collections import Counter
        error_counts = Counter(e.get("error_type", "unknown") for e in error_history[-10:])
        top_errors = error_counts.most_common(3)
        parts.append(f"Recent errors: {', '.join(f'{n}({c})' for n,c in top_errors)}")
    
    return " | ".join(parts) if parts else "No recent activity"


def record_skill_creation(skill_name: str, trigger: str, quality_score: float = 0.5):
    """
    Record that a skill was created by the agent.
    This feeds into the curator's agent-created skill detection.
    
    Args:
        skill_name: Name of the created skill
        trigger: What triggered creation (e.g., 'error_pattern', 'user_request')
        quality_score: Initial quality estimate (0-1)
    """
    try:
        from agent.cortex_learning import get_learning_engine
        engine = get_learning_engine()
        
        # Store in memory_units as an agent-created skill record
        engine.store.save_memory_unit(
            content=f"Agent-created skill: {skill_name} (trigger: {trigger}, quality: {quality_score})",
            memory_type="agent_skill",
            source="iteration_pipeline",
            confidence=quality_score,
        )
        logger.debug("Recorded skill creation: %s", skill_name)
    except Exception as e:
        logger.debug("Failed to record skill creation: %s", e)


def get_curator_status() -> Dict[str, Any]:
    """Get curator status for iteration pipeline diagnostics."""
    try:
        from agent.curator import load_state, should_run_now
        state = load_state()
        return {
            "enabled": True,
            "should_run_now": should_run_now(),
            "last_run_at": state.get("last_run_at", "never"),
            "run_count": state.get("run_count", 0),
            "last_summary": state.get("last_run_summary", "no runs yet"),
            "next_run_reason": "7-day interval or manual trigger",
        }
    except Exception as e:
        return {"enabled": False, "error": str(e)}
