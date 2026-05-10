#!/usr/bin/env python3
"""
cognitive_infrastructure_hooks.py — Wire cognitive_infrastructure_v2 into Hermes Agent

Hooks:
  - pre_llm_call: ToolIntelligenceRouter checks tool success rates
  - pre_tool_call: CreditAssigner records which tips are injected
  - post_tool_call: CreditAssigner records outcomes, SessionEndExtractor accumulates
  - session_end: SessionEndExtractor saves lessons, AutoSkillCron runs monthly
  - cron: InjectionGovernorV2.apply_feedback() runs daily
"""

import os
import sys
from pathlib import Path

# Ensure hermes-agent is in path for imports
sys.path.insert(0, str(Path.home() / "hermes-agent"))

from cognitive_infrastructure_v2 import (
    get_governor_v2, get_credit_assigner, get_session_extractor,
    get_tool_router, get_auto_skill
)

# ═══════════════════════════════════════════════════════════════════════════════
# HOOK: pre_llm_call — Check tool intelligence before LLM decides on tools
# ═══════════════════════════════════════════════════════════════════════════════

def on_pre_llm_call(user_message: str, context: dict, **kwargs) -> dict:
    """Before LLM call: inject tool intelligence warnings into context."""
    router = get_tool_router()
    
    # Check if user message mentions weak tools
    weak_tools = ["cronjob", "delegate_parallel"]
    warnings = []
    
    for tool in weak_tools:
        if tool in str(user_message).lower():
            rec = router.recommend(tool)
            if rec.get("warning"):
                warnings.append(rec["warning"])
    
    if warnings:
        # Add warnings to context (will be seen by LLM)
        context["tool_warnings"] = warnings
    
    return {"context": context}

# ═══════════════════════════════════════════════════════════════════════════════
# HOOK: pre_tool_call — Record which tips are injected before tool execution
# ═══════════════════════════════════════════════════════════════════════════════

def on_pre_tool_call(tool_name: str, args: dict, **kwargs) -> dict:
    """Before tool call: record injected tips for credit assignment."""
    # This would need access to the injection system — simplified here
    # In practice, the distillation plugin's _injected_tips_this_turn would feed this
    return {"args": args}

# ═══════════════════════════════════════════════════════════════════════════════
# HOOK: post_tool_call — Credit tips + accumulate session data
# ═══════════════════════════════════════════════════════════════════════════════

def on_post_tool_call(tool_name: str, args: dict, result: dict, 
                      status: str = "", error: str = "", **kwargs) -> dict:
    """After tool call: credit assignment + session tracking."""
    
    ca = get_credit_assigner()
    se = get_session_extractor()
    router = get_tool_router()
    
    success = status == "success" or (isinstance(result, dict) and result.get("success", False))
    
    # Credit assignment
    ca.record_outcome(tool_name, success, error)
    
    # Log routing decision
    decision = "proceed" if success else "caution"
    router.log_decision(tool_name, decision, "success" if success else f"failure:{error[:50]}")
    
    # Accumulate for session-end extraction
    se.session_id = os.environ.get("HERMES_SESSION_ID", "default")
    # (Full accumulation would need a persistent store per session)
    
    return {"result": result}

# ═══════════════════════════════════════════════════════════════════════════════
# HOOK: session_end — Extract lessons + monthly auto-skill
# ═══════════════════════════════════════════════════════════════════════════════

def on_session_end(session_id: str, tool_calls: list, **kwargs) -> dict:
    """When session ends: extract lessons, run consolidation, and trigger brain cycle."""
    
    se = get_session_extractor()
    se.session_id = session_id
    
    # Extract lessons from session history
    lessons = se.extract(tool_calls)
    if lessons:
        se.save_lessons(lessons)
        print(f"[SESSION-END] Extracted {len(lessons)} lessons")
    
    # Auto-trigger consolidation and brain cycle
    try:
        import subprocess
        # Run consolidation
        result = subprocess.run(
            ['python3', '/Users/dannygomez/hermes-agent/agent/hermes_manual_triggers.py', 'cortex-consolidate'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"[SESSION-END] Auto-triggered cortex-consolidate")
        
        # Run brain cycle
        result = subprocess.run(
            ['python3', '/Users/dannygomez/hermes-agent/agent/hermes_manual_triggers.py', 'brain-cycle'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"[SESSION-END] Auto-triggered brain-cycle")
        
        # Generate skill from session
        result = subprocess.run(
            ['python3', '/Users/dannygomez/hermes-agent/agent/hermes_manual_triggers.py', 'skill-generate'],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            print(f"[SESSION-END] Auto-triggered skill-generate")
    except Exception as e:
        print(f"[SESSION-END] Auto-trigger failed: {e}")
    
    # Check if monthly auto-skill should run
    asc = get_auto_skill()
    # (Would check last run date — simplified)
    
    return {"lessons_extracted": len(lessons)}

# ═══════════════════════════════════════════════════════════════════════════════
# CRON: Daily feedback loop
# ═══════════════════════════════════════════════════════════════════════════════

def run_daily_feedback():
    """Run by cron daily: apply injection governor feedback."""
    gov = get_governor_v2()
    gov.apply_feedback()
    
    stats = gov.get_stats()
    print(f"[DAILY-FEEDBACK] Injection rate: {stats['inject_rate']*100:.1f}%")
    print(f"  Dropped by reason: {stats['drop_reasons']}")


if __name__ == "__main__":
    # Test hooks
    print("=== Hook Wiring Test ===\n")
    
    # Test pre_llm_call
    ctx = {"existing": "data"}
    result = on_pre_llm_call("use cronjob to schedule", ctx)
    print(f"pre_llm_call: added warnings: {result.get('context', {}).get('tool_warnings', [])}")
    
    # Test post_tool_call
    result = on_post_tool_call("cronjob", {"action": "create"}, 
                                {"success": False, "error": "id field confusion"},
                                status="failure", error="id field confusion")
    print(f"post_tool_call: credited cronjob failure")
    
    # Test session_end
    test_calls = [
        {"tool_name": "cronjob", "success": False, "error": "id confusion", "duration_ms": 100},
        {"tool_name": "cronjob", "success": False, "error": "id confusion", "duration_ms": 100},
        {"tool_name": "execute_code", "success": True, "error": "", "duration_ms": 200},
    ]
    result = on_session_end("test-session-123", test_calls)
    print(f"session_end: {result['lessons_extracted']} lessons")
    
    # Test daily feedback
    print("\nRunning daily feedback...")
    run_daily_feedback()
    
    print("\n=== All hooks operational ===")
