"""
Hermes Learning Brain Plugin
=============================
Wires the self-improvement learning loop into the agent runtime.

Hooks:
- pre_tool_call: Loop guard + tip injection + confidence check
- post_tool_call: Error analysis + healing + state update
- on_session_start: Task initialization + tip preload
- on_session_end: Intent verification + budget check
"""

import json
import sys
import os
from pathlib import Path

# Ensure hermes_cli is on path for brain imports
HERMES_ROOT = Path(__file__).resolve().parent.parent.parent
if str(HERMES_ROOT / "hermes_cli") not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT / "hermes_cli"))

from hermes_brain import HermesBrain
from context_updater import ContextUpdater
from subconscious.llm_judge import LLMJudge
from subconscious.self_audit_engine import SelfAuditEngine, PreflightChecker

# Singleton brain instance (lives for plugin lifetime)
_brain = None
_updater = None
_judge = None
_audit = None

def _get_brain():
    global _brain
    if _brain is None:
        _brain = HermesBrain()
    return _brain

def _get_updater():
    global _updater
    if _updater is None:
        _updater = ContextUpdater()
    return _updater

def _get_judge():
    global _judge
    if _judge is None:
        _judge = LLMJudge(model="deepseek-v4-pro")
    return _judge

def _get_audit():
    global _audit
    if _audit is None:
        _audit = SelfAuditEngine()
    return _audit


# ─── Hook: Session Start ───────────────────────────────────────────────────

def on_session_start_hook(**kwargs):
    """Called when a new session begins."""
    brain = _get_brain()
    
    # Extract session context from kwargs
    session_id = kwargs.get("session_id", "unknown")
    user_message = kwargs.get("user_message", "")
    
    # Initialize task with tips and confidence check
    task_info = brain.on_task_start(user_message)
    
    # Log to unified context
    updater = _get_updater()
    updater.update_session(session_id, task=user_message[:100])
    
    # Return tips for the system to consider (stored in session metadata)
    return {
        "learning_tips": task_info.get("tips", []),
        "confidence": task_info.get("confidence", {}),
        "should_verify": task_info.get("should_verify", False),
    }


# ─── Hook: Pre-Tool Call ───────────────────────────────────────────────────

def pre_tool_call_hook(**kwargs):
    """
    Called before every tool call.
    Returns a block message string if the call should be blocked,
    or None to allow it to proceed.
    """
    brain = _get_brain()
    audit = _get_audit()
    
    tool_name = kwargs.get("tool_name", "")
    args = kwargs.get("args", {})
    session_id = kwargs.get("session_id", "")
    task_id = kwargs.get("task_id", "")
    
    # ─── SELF-AUDIT: Pre-flight check ─────────────────────────────────────
    preflight = PreflightChecker.check(tool_name, args)
    if not preflight["ready"]:
        return {
            "action": "block",
            "message": f"[SELF-AUDIT] Pre-flight failed: {preflight['advice']}. Fix args before calling."
        }
    
    # ─── SELF-AUDIT: Loop detection ───────────────────────────────────────
    # We check after recording so we have history
    audit.record_call(tool_name, args, None, tokens_used=0)
    loop_status = audit.get_loop_status()
    
    if loop_status["loop_detected"]:
        suggestions = audit.suggest_recovery()
        return {
            "action": "block",
            "message": f"[SELF-AUDIT] LOOP DETECTED ({loop_status['loop_count']} loops). " + " ".join(suggestions[:2])
        }
    
    # Run brain's pre-flight checks
    check = brain.before_tool_call(tool_name, args, session_id)
    
    if check.get("action") == "BLOCK":
        reason = check.get("reason", "Loop detected")
        alt = check.get("alternative", "Try a different approach")
        return {
            "action": "block",
            "message": f"[LEARNING BRAIN] {reason}. Suggestion: {alt}"
        }
    
    return None  # Allow the call


# ─── Hook: Post-Tool Call ──────────────────────────────────────────────────

def post_tool_call_hook(**kwargs):
    """Called after every tool call completes."""
    brain = _get_brain()
    updater = _get_updater()
    audit = _get_audit()
    
    tool_name = kwargs.get("tool_name", "")
    args = kwargs.get("args", {})
    result = kwargs.get("result", "")
    duration_ms = kwargs.get("duration_ms", 0)
    session_id = kwargs.get("session_id", "")
    task_id = kwargs.get("task_id", "")
    tokens_used = kwargs.get("tokens_used", 0)
    
    # ─── SELF-AUDIT: Record and analyze ────────────────────────────────────
    audit_result = audit.record_call(tool_name, args, result, tokens_used, duration_ms)
    
    # Log waste if detected
    if audit_result.get("waste_detected"):
        updater.record_error(
            tool_name,
            f"Token waste detected: {tokens_used} tokens on failed/repeated call",
            "Switch approach or verify args before retry"
        )
    
    # Determine success from result
    success = True
    error = None
    try:
        parsed = json.loads(result) if isinstance(result, str) else result
        if isinstance(parsed, dict) and "error" in parsed:
            success = False
            error = parsed["error"]
    except (json.JSONDecodeError, TypeError):
        pass
    
    # Run post-flight analysis
    analysis = brain.after_tool_call(tool_name, args, result, error)
    
    # ─── LLM Judge: Auto-evaluate generated tips ──────────────────────────
    judge = _get_judge()
    
    # Extract tips from successful tool results for evaluation
    if success and isinstance(result, str):
        try:
            parsed = json.loads(result) if result.strip().startswith('{') else {}
            # Check if result contains tips or learnings
            tips_found = []
            if isinstance(parsed, dict):
                # Look for tip-like content in various result shapes
                for key in ['tip', 'tips', 'learning', 'learnings', 'lesson', 'lessons']:
                    if key in parsed:
                        val = parsed[key]
                        if isinstance(val, list):
                            tips_found.extend(val)
                        elif isinstance(val, str):
                            tips_found.append(val)
                
                # Also check nested structures
                if 'content' in parsed and isinstance(parsed['content'], str):
                    # Simple heuristic: if content looks like a tip
                    content = parsed['content']
                    if len(content) > 20 and ('use ' in content.lower() or 'always ' in content.lower() or 'never ' in content.lower()):
                        tips_found.append(content)
            
            # Evaluate each found tip
            for tip_text in tips_found[:3]:  # Max 3 tips per call to control cost
                if isinstance(tip_text, str) and len(tip_text) > 10:
                    tip = {"text": tip_text, "domain": tool_name, "confidence": 0.7}
                    eval_result = judge.evaluate_single(tip)
                    
                    # Store low-quality tips for review
                    quality_score = eval_result.get("quality_score", 0.5)
                    if quality_score < 0.6:
                        updater.record_error(
                            tool_name,
                            f"Low-quality tip (score {quality_score}): {tip_text[:80]}",
                            eval_result.get("suggested_fix", "Review and rewrite")
                        )
                    
                    # If tip is actionable and high quality, consider distilling
                    is_actionable = eval_result.get("is_actionable", True)
                    if is_actionable and quality_score >= 0.7:
                        # Log to cortex for potential distillation
                        updater.update_session(
                            session_id,
                            tip=f"[{tool_name}] {tip_text[:120]}"
                        )
        except (json.JSONDecodeError, Exception):
            pass  # Not all results are JSON or contain tips
    
    # Update tool intelligence in unified context
    updater.update_tool_result(tool_name, success, duration_ms, error)
    
    # Record errors
    if error:
        fix = analysis.get("lesson", "Review error and try alternative approach")
        updater.record_error(tool_name, error, fix)
    
    # Return analysis for logging (not used by caller, but useful for debug)
    return {
        "success": success,
        "analyzed": True,
        "healed": analysis.get("healed", False) if error else None,
        "judge_evaluated": True,
        "audit": audit_result,
    }


# ─── Hook: Session End ─────────────────────────────────────────────────────

def on_session_end_hook(**kwargs):
    """Called when a session ends."""
    brain = _get_brain()
    
    session_id = kwargs.get("session_id", "")
    final_response = kwargs.get("final_response", "")
    
    # Verify intent if we had a task
    # (In practice we'd need to track the original task expectation)
    budget = brain.on_task_end(session_id, "", final_response)
    
    return {
        "budget_status": budget.get("budget_status", {}),
    }


# ─── Plugin Registration ────────────────────────────────────────────────────

def register(ctx):
    """Register all hooks with the plugin system."""
    ctx.register_hook("on_session_start", on_session_start_hook)
    ctx.register_hook("pre_tool_call", pre_tool_call_hook)
    ctx.register_hook("post_tool_call", post_tool_call_hook)
    ctx.register_hook("on_session_end", on_session_end_hook)
    
    # Verify judge is ready
    judge = _get_judge()
    print(f"[learning-brain] Learning loop wired: pre_tool_call, post_tool_call, on_session_start, on_session_end")
    print(f"[learning-brain] LLM Judge ready: {judge.model} @ {judge.base_url}")
