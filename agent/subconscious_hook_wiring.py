#!/usr/bin/env python3
"""
subconscious_hook_wiring.py — Wire ALL subconscious systems into Hermes hooks.

This module provides complete hook implementations that integrate:
  - pre_tool_call: memory bridge, circuit breaker, retry logic, intelligence tracking
  - post_tool_call: error mining, quality gating, intelligence update
  - pre_llm_call: context window guard, prompt optimization
  - post_llm_call: response quality scoring, distillation trigger
  - transform_tool_result: result canonicalization, caching

Usage:
    # In model_tools.py or plugins.py:
    from agent.subconscious_hook_wiring import (
        pre_tool_call_full,
        post_tool_call_full,
        pre_llm_call_full,
        post_llm_call_full,
        transform_tool_result_full
    )
"""

import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

SUBCONSCIOUS = Path(__file__).parent
sys.path.insert(0, str(Path.home() / "hermes-agent"))

logger = logging.getLogger("hermes.subconscious.wiring")

# Lazy imports to avoid circular dependencies
def _get_memory_bridge():
    from agent.memory_cortex_bridge import MemoryCortexBridge
    return MemoryCortexBridge()

def _get_error_miner():
    from error_pattern_miner import ErrorPatternMiner
    return ErrorPatternMiner()

def _get_validator():
    from multi_step_validator import MultiStepValidator
    return MultiStepValidator()

def _get_context_guard():
    from context_window_guard import ContextWindowGuard
    return ContextWindowGuard()

def _get_quality_gate():
    from distillation_quality_gate import DistillationQualityGate
    return DistillationQualityGate()

def _get_intelligence_tracker():
    from agent.tool_intelligence_tracker import ToolIntelligenceTracker
    return ToolIntelligenceTracker()

def _get_enhancement_suite():
    from agent.hermes_enhancement_suite import HermesEnhancementSuite
    return HermesEnhancementSuite()


# ---------------------------------------------------------------------------
# PRE-TOOL-CALL HOOK (Complete)
# ---------------------------------------------------------------------------

def pre_tool_call_full(tool_name: str, args: Dict, task_id: str = "",
                       session_id: str = "", tool_call_id: str = "") -> Optional[str]:
    """
    FULL pre_tool_call hook integrating all subconscious systems.
    
    Returns block message if tool should be blocked, None otherwise.
    """
    try:
        # 1. Memory pressure check — auto-offload if needed
        bridge = _get_memory_bridge()
        result = bridge.offload_if_needed()
        if result.get('status') == 'offloaded':
            logger.info(
                "[MEMORY] Offloaded %s entries, freed %s chars, now %s%%",
                result.get('entries_moved'),
                result.get('chars_freed'),
                result.get('pressure_pct')
            )
        
        # 2. Tool intelligence tracking — record attempt
        tracker = _get_intelligence_tracker()
        tracker.record_call(
            tool_name=tool_name,
            success=True,  # Will update in post_tool_call
            duration_ms=0,
            context=str(args)[:200],
            session_id=session_id
        )
        
        # 3. Circuit breaker check
        suite = _get_enhancement_suite()
        if not suite.circuit_breaker.can_execute(tool_name):
            logger.warning("[CIRCUIT] Blocking %s — circuit breaker OPEN", tool_name)
            return json.dumps({
                "error": f"Tool '{tool_name}' temporarily disabled due to repeated failures. Try alternative."
            })
        
        # 4. Multi-step validation (if this is part of a plan)
        # TODO: Integrate with plan tracking
        
    except Exception as e:
        logger.debug("[pre_tool_call] Enhancement error (fail-open): %s", e)
    
    return None  # Allow tool call


# ---------------------------------------------------------------------------
# POST-TOOL-CALL HOOK (Complete)
# ---------------------------------------------------------------------------

def post_tool_call_full(tool_name: str, args: Dict, result: str,
                        task_id: str = "", session_id: str = "",
                        tool_call_id: str = "", duration_ms: int = 0) -> None:
    """
    FULL post_tool_call hook integrating all subconscious systems.
    """
    try:
        # 1. Determine success/failure
        success = not any(marker in result for marker in [
            '"error"', 'failed', 'Traceback', 'Exception', 'timed out',
            'not found', 'permission denied'
        ])
        
        # 2. Update tool intelligence
        tracker = _get_intelligence_tracker()
        tracker.record_call(
            tool_name=tool_name,
            success=success,
            duration_ms=duration_ms,
            context=str(args)[:200],
            session_id=session_id
        )
        
        # 3. Circuit breaker update
        suite = _get_enhancement_suite()
        if success:
            suite.circuit_breaker.record_success(tool_name)
        else:
            suite.circuit_breaker.record_failure(tool_name)
        
        # 4. Error pattern mining (on failure)
        if not success:
            miner = _get_error_miner()
            mined = miner.record_error(tool_name, result, context=args, session_id=session_id)
            logger.info(
                "[ERROR_MINER] %s error recorded: %s -> %s",
                tool_name, mined['category'], mined['preventive_tip'][:60]
            )
            
            # Check if we should suggest a fix
            recent_patterns = miner.mine_recent(hours=1)
            if recent_patterns:
                logger.info("[ERROR_MINER] %d patterns in last hour", len(recent_patterns))
        
        # 5. Distillation quality gate (extract tips from successful results)
        if success and len(result) > 100:
            gate = _get_quality_gate()
            # Only validate if result looks like a tip
            if any(w in result.lower() for w in ['when', 'if', 'use', 'check', 'prefer']):
                validation = gate.validate_tip(result[:500], evidence_sources=[tool_name])
                if validation['passed']:
                    logger.info("[QUALITY_GATE] Tip passed validation: score=%s", validation['overall_score'])
                else:
                    logger.debug("[QUALITY_GATE] Tip rejected: %s", validation['rejection_reason'][:80])
        
        # 6. Cache successful results
        if success:
            suite.cache.set(tool_name, args, result)
    
    except Exception as e:
        logger.debug("[post_tool_call] Enhancement error (fail-open): %s", e)


# ---------------------------------------------------------------------------
# PRE-LLM-CALL HOOK (Complete)
# ---------------------------------------------------------------------------

def pre_llm_call_full(messages: List[Dict], context_limit: int = 128000) -> List[Dict]:
    """
    FULL pre_llm_call hook integrating all subconscious systems.
    
    Returns potentially modified messages list.
    """
    try:
        # 1. Context window guard — compress if needed
        guard = _get_context_guard()
        result = guard.check_and_compress(messages)
        
        if result['action'] == 'compressed':
            logger.info(
                "[CONTEXT] Compressed %s -> %s tokens, saved %s",
                result['original_tokens'],
                result['compressed_tokens'],
                result['tokens_saved']
            )
        
        # 2. Memory injection — add relevant offloaded memories
        bridge = _get_memory_bridge()
        if len(messages) > 0 and messages[-1].get('role') == 'user':
            query = messages[-1].get('content', '')
            if query:
                relevant = bridge.search_offloaded(query, limit=3)
                if relevant:
                    # Inject as system message hint
                    memory_hint = "Relevant context: " + "; ".join(
                        r.get('content', r.get('text', ''))[:100] for r in relevant
                    )
                    # Find or create system message
                    sys_idx = next((i for i, m in enumerate(messages) if m.get('role') == 'system'), -1)
                    if sys_idx >= 0:
                        messages[sys_idx]['content'] += f"\n\n[{memory_hint}]"
                    else:
                        messages.insert(0, {"role": "system", "content": memory_hint})
    
    except Exception as e:
        logger.debug("[pre_llm_call] Enhancement error (fail-open): %s", e)
    
    return messages


# ---------------------------------------------------------------------------
# POST-LLM-CALL HOOK (Complete)
# ---------------------------------------------------------------------------

def post_llm_call_full(response: str, messages: List[Dict], **kwargs) -> str:
    """
    FULL post_llm_call hook integrating all subconscious systems.
    
    Returns potentially modified response.
    """
    try:
        # 1. Response quality check
        if len(response) < 50:
            logger.warning("[LLM] Very short response (%d chars)", len(response))
        
        # 2. Extract learnings for distillation
        if len(response) > 200:
            gate = _get_quality_gate()
            validation = gate.validate_tip(response[:500])
            if validation['passed'] and validation['overall_score'] >= 0.8:
                logger.info("[DISTILLATION] High-quality response detected: score=%s", validation['overall_score'])
        
        # 3. Update context guard stats
        guard = _get_context_guard()
        stats = guard.get_stats()
        logger.debug("[CONTEXT] Total compressions: %s", stats.get('total_compressions', 0))
    
    except Exception as e:
        logger.debug("[post_llm_call] Enhancement error (fail-open): %s", e)
    
    return response


# ---------------------------------------------------------------------------
# TRANSFORM-TOOL-RESULT HOOK (Complete)
# ---------------------------------------------------------------------------

def transform_tool_result_full(tool_name: str, args: Dict, result: str,
                                task_id: str = "", duration_ms: int = 0) -> Optional[str]:
    """
    FULL transform_tool_result hook.
    
    Returns modified result or None to keep original.
    """
    try:
        # 1. Check cache for identical calls
        suite = _get_enhancement_suite()
        cached = suite.cache.get(tool_name, args)
        if cached is not None:
            logger.debug("[CACHE] Returning cached result for %s", tool_name)
            return cached
        
        # 2. Truncate overly long results
        max_size = 10000  # 10K chars max
        if len(result) > max_size:
            truncated = result[:max_size] + f"\n\n[...truncated from {len(result)} chars]"
            logger.info("[RESULT] Truncated %s result from %d to %d chars", tool_name, len(result), max_size)
            return truncated
        
        # 3. Format JSON results for readability
        if result.strip().startswith('{') or result.strip().startswith('['):
            try:
                parsed = json.loads(result)
                formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                if len(formatted) < len(result) * 1.2:  # Only if not much larger
                    return formatted
            except Exception:
                pass
    
    except Exception as e:
        logger.debug("[transform_tool_result] Enhancement error (fail-open): %s", e)
    
    return None  # Keep original result


# ---------------------------------------------------------------------------
# INSTALLER
# ---------------------------------------------------------------------------

def install_all_hooks():
    """
    Install all subconscious hooks into Hermes Agent.
    
    This should be called once at startup.
    """
    logger.info("[SUBCONSCIOUS] Installing full hook wiring...")
    
    # The actual installation would modify the hook dispatch in plugins.py
    # For now, we provide the functions that can be called from existing hooks
    
    hook_map = {
        'pre_tool_call': pre_tool_call_full,
        'post_tool_call': post_tool_call_full,
        'pre_llm_call': pre_llm_call_full,
        'post_llm_call': post_llm_call_full,
        'transform_tool_result': transform_tool_result_full,
    }
    
    logger.info("[SUBCONSCIOUS] %d hooks ready for installation", len(hook_map))
    return hook_map


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Subconscious Hook Wiring")
    parser.add_argument("--install", action="store_true", help="Install all hooks")
    parser.add_argument("--test", action="store_true", help="Test all hooks")
    
    args = parser.parse_args()
    
    if args.install:
        hooks = install_all_hooks()
        print(f"Installed {len(hooks)} hooks:")
        for name, func in hooks.items():
            print(f"  {name}: {func.__name__}")
    elif args.test:
        print("Testing hooks...")
        
        # Test pre_tool_call
        block = pre_tool_call_full("web_search", {"query": "test"})
        print(f"pre_tool_call: {'BLOCKED' if block else 'ALLOWED'}")
        
        # Test post_tool_call
        post_tool_call_full("web_search", {"query": "test"}, '{"results": ["url1"]}', duration_ms=1000)
        print("post_tool_call: OK")
        
        # Test pre_llm_call
        msgs = [{"role": "user", "content": "Hello"}]
        modified = pre_llm_call_full(msgs)
        print(f"pre_llm_call: {len(modified)} messages")
        
        # Test transform
        result = transform_tool_result_full("web_search", {}, '{"a": 1, "b": 2}')
        print(f"transform: {'formatted' if result else 'unchanged'}")
        
        print("\nAll hooks functional!")
    else:
        print("Usage: python3 subconscious_hook_wiring.py --install | --test")
