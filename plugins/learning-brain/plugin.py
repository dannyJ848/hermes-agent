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

# Singleton brain instance (lives for plugin lifetime)
_brain = None
_updater = None

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
    
    tool_name = kwargs.get("tool_name", "")
    args = kwargs.get("args", {})
    session_id = kwargs.get("session_id", "")
    task_id = kwargs.get("task_id", "")
    
    # Run pre-flight checks
    check = brain.before_tool_call(tool_name, args, session_id)
    
    if check.get("action") == "BLOCK":
        reason = check.get("reason", "Loop detected")
        alt = check.get("alternative", "Try a different approach")
        return f"[LEARNING BRAIN BLOCKED] {reason}. Suggestion: {alt}"
    
    # Log the attempt
    updater = _get_updater()
    # (We update success after the call in post_tool_call)
    
    return None  # Allow the call


# ─── Hook: Post-Tool Call ──────────────────────────────────────────────────

def post_tool_call_hook(**kwargs):
    """Called after every tool call completes."""
    brain = _get_brain()
    updater = _get_updater()
    
    tool_name = kwargs.get("tool_name", "")
    args = kwargs.get("args", {})
    result = kwargs.get("result", "")
    duration_ms = kwargs.get("duration_ms", 0)
    session_id = kwargs.get("session_id", "")
    task_id = kwargs.get("task_id", "")
    
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
    
    print("[learning-brain] Learning loop wired: pre_tool_call, post_tool_call, on_session_start, on_session_end")
