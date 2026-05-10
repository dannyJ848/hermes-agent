"""
Cognitive Systems Plugin — Hermes Agent Integration

This module registers ALL cognitive systems as Hermes plugins,
wireing them into the agent loop via the official plugin hook system.

Each cognitive system registers for specific hooks:
  - pre_tool_call:  tool_misuse_prevention (validate tool health)
  - post_tool_call: agent_scorecard, red_team_hippocampus (score, mine errors)
  - pre_llm_call:   iteration_engine (retrieve past lessons)
  - post_llm_call:  cortex_flywheel, memory_cortex_bridge, hermes_enhancement_suite

Usage:
    from agent.cognitive_systems_plugin import register_cognitive_systems
    register_cognitive_systems(ctx)  # Called by Hermes plugin loader
"""

import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# ── COGNITIVE SYSTEM REGISTRY ──
# Each system is loaded lazily and registered for its hooks

_SYSTEMS: Dict[str, Any] = {}


def _load_system(name: str):
    """Lazy-load a cognitive system module."""
    if name in _SYSTEMS:
        return _SYSTEMS[name]
    
    try:
        if name == "iteration_engine":
            from agent.iteration_engine import get_engine
            _SYSTEMS[name] = get_engine()
        elif name == "cortex_flywheel":
            from agent.cortex_flywheel import CortexDB
            _SYSTEMS[name] = CortexDB()
        elif name == "agent_scorecard":
            from agent.agent_scorecard import AgentScorecard
            _SYSTEMS[name] = AgentScorecard()
        elif name == "tool_misuse_prevention":
            from agent.tool_misuse_prevention import ToolHealthMonitor
            _SYSTEMS[name] = ToolHealthMonitor()
        elif name == "red_team_hippocampus":
            from agent.red_team_hippocampus import ErrorMiner
            _SYSTEMS[name] = ErrorMiner()
        elif name == "memory_cortex_bridge":
            from agent.memory_cortex_bridge import MemoryBridge
            _SYSTEMS[name] = MemoryBridge()
        elif name == "hermes_enhancement_suite":
            from agent.hermes_enhancement_suite import EnhancementTracker
            _SYSTEMS[name] = EnhancementTracker()
        else:
            logger.warning(f"Unknown cognitive system: {name}")
            return None
        
        logger.info(f"Loaded cognitive system: {name}")
        return _SYSTEMS[name]
    except Exception as e:
        logger.warning(f"Failed to load cognitive system {name}: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# HOOK HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

def _pre_tool_call_handler(tool_name: str, args: Dict, **kwargs) -> Optional[str]:
    """
    Called before every tool call.
    Returns context string to inject, or None.
    """
    contexts = []
    
    # 1. Iteration engine: retrieve past lessons for this tool
    engine = _load_system("iteration_engine")
    if engine:
        try:
            lesson_ctx = engine.before_action(tool_name, str(args)[:200])
            if lesson_ctx.get("has_history"):
                parts = []
                if lesson_ctx.get("warnings"):
                    parts.append("PAST FAILURES:")
                    for w in lesson_ctx["warnings"][:2]:
                        parts.append(f"  - {w['lesson']} ({w['frequency']}x)")
                if lesson_ctx.get("proven_approaches"):
                    parts.append("PROVEN APPROACHES:")
                    for a in lesson_ctx["proven_approaches"][:2]:
                        parts.append(f"  - {a['approach']} ({a['frequency']}x)")
                if parts:
                    contexts.append("\n".join(parts))
        except Exception as e:
            logger.debug(f"Iteration engine pre_tool failed: {e}")
    
    # 2. Tool health monitor: check if tool is reliable
    health = _load_system("tool_misuse_prevention")
    if health:
        try:
            proceed, warnings, alt = health.validate_tool_call(tool_name)
            if not proceed:
                contexts.append(f"⚠️ TOOL DANGER: {tool_name} is unreliable! Consider: {alt}")
            for w in warnings:
                contexts.append(f"⚠️ TOOL WARNING: {w}")
        except Exception as e:
            logger.debug(f"Tool health check failed: {e}")
    
    return "\n\n".join(contexts) if contexts else None


def _post_tool_call_handler(tool_name: str, result: Any, error: str = "", 
                           duration_ms: int = 0, **kwargs) -> None:
    """
    Called after every tool call completes.
    Records the experience for learning.
    """
    # 1. Iteration engine: record the experience
    engine = _load_system("iteration_engine")
    if engine:
        try:
            result_str = "success" if not error else "failure"
            engine.after_action(
                action_type=tool_name,
                detail=str(result)[:200] if result else "",
                result=result_str,
                error=error,
                speed_ms=duration_ms,
            )
        except Exception as e:
            logger.debug(f"Iteration engine post_tool failed: {e}")
    
    # 2. Agent scorecard: score the tool call quality
    scorecard = _load_system("agent_scorecard")
    if scorecard:
        try:
            scorecard.record_tool_call(tool_name, result, error, duration_ms)
        except Exception as e:
            logger.debug(f"Scorecard failed: {e}")
    
    # 3. Red team hippocampus: mine errors for patterns
    red_team = _load_system("red_team_hippocampus")
    if red_team and error:
        try:
            red_team.mine_error(tool_name, error, str(result)[:500] if result else "")
        except Exception as e:
            logger.debug(f"Red team error mining failed: {e}")


def _pre_llm_call_handler(user_message: str, conversation_history: list, 
                          **kwargs) -> Optional[str]:
    """
    Called before every LLM call.
    Returns context to inject into the prompt.
    """
    contexts = []
    
    # 1. Iteration engine: retrieve session-level lessons
    engine = _load_system("iteration_engine")
    if engine:
        try:
            stats = engine.get_learning_stats()
            if stats["session_actions"] > 0:
                contexts.append(
                    f"[Session learning: {stats['session_learnings']} new insights from "
                    f"{stats['session_actions']} actions]"
                )
        except Exception as e:
            logger.debug(f"Iteration engine pre_llm failed: {e}")
    
    return "\n".join(contexts) if contexts else None


def _post_llm_call_handler(assistant_response: str, conversation_history: list,
                           **kwargs) -> None:
    """
    Called after every LLM call completes.
    Records to memory, cortex, etc.
    """
    # 1. Cortex flywheel: record the turn
    cortex = _load_system("cortex_flywheel")
    if cortex:
        try:
            cortex.record_turn(
                response=assistant_response,
                history_length=len(conversation_history),
            )
        except Exception as e:
            logger.debug(f"Cortex record failed: {e}")
    
    # 2. Memory cortex bridge: consolidate memory
    bridge = _load_system("memory_cortex_bridge")
    if bridge:
        try:
            bridge.consolidate_turn(conversation_history, assistant_response)
        except Exception as e:
            logger.debug(f"Memory bridge failed: {e}")
    
    # 3. Enhancement tracker: track improvements
    enhancement = _load_system("hermes_enhancement_suite")
    if enhancement:
        try:
            enhancement.track_turn(assistant_response)
        except Exception as e:
            logger.debug(f"Enhancement tracker failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# PLUGIN REGISTRATION
# ═══════════════════════════════════════════════════════════════════════════════

def register_cognitive_systems(ctx) -> None:
    """
    Register all cognitive systems with the Hermes plugin system.
    
    This is called by the Hermes plugin loader when it discovers
    the cognitive_systems_plugin module.
    """
    logger.info("Registering cognitive systems with Hermes plugin hooks...")
    
    # Register pre_tool_call hook
    ctx.register_hook("pre_tool_call", _pre_tool_call_handler)
    logger.info("  ✓ pre_tool_call: iteration_engine + tool_misuse_prevention")
    
    # Register post_tool_call hook
    ctx.register_hook("post_tool_call", _post_tool_call_handler)
    logger.info("  ✓ post_tool_call: iteration_engine + agent_scorecard + red_team")
    
    # Register pre_llm_call hook
    ctx.register_hook("pre_llm_call", _pre_llm_call_handler)
    logger.info("  ✓ pre_llm_call: iteration_engine")
    
    # Register post_llm_call hook
    ctx.register_hook("post_llm_call", _post_llm_call_handler)
    logger.info("  ✓ post_llm_call: cortex_flywheel + memory_bridge + enhancement")
    
    # Register on_session_start hook
    ctx.register_hook("on_session_start", _on_session_start_handler)
    logger.info("  ✓ on_session_start: all systems initialized")
    
    logger.info("Cognitive systems registration complete.")


def _on_session_start_handler(session_id: str, model: str, platform: str, **kwargs) -> None:
    """Initialize all cognitive systems at session start."""
    systems = [
        "iteration_engine",
        "cortex_flywheel", 
        "agent_scorecard",
        "tool_misuse_prevention",
        "red_team_hippocampus",
        "memory_cortex_bridge",
        "hermes_enhancement_suite",
    ]
    
    for system in systems:
        try:
            _load_system(system)
        except Exception as e:
            logger.debug(f"Failed to init {system}: {e}")
    
    logger.info(f"Cognitive systems ready for session {session_id[:8]}...")


# Legacy compatibility — called by old subconscious_plugin_loader
init_subconscious_plugins = register_cognitive_systems
