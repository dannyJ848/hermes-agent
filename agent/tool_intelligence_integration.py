#!/usr/bin/env python3
"""
tool_intelligence_integration.py — Active tool routing for Hermes Agent

This module is called BEFORE each tool call to check historical performance
and either warn, block, or suggest alternatives.

Usage:
    from tool_intelligence_integration import check_tool_before_use
    recommendation = check_tool_before_use("cronjob", {"action": "create"})
    if not recommendation["proceed"]:
        # Use alternative
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / "hermes-agent"))

from cognitive_infrastructure_v2 import get_tool_router

# Weak tools from empirical data
WEAK_TOOLS = {
    "cronjob": {"rate": 0.13, "issue": "id field confusion", "alt": "terminal with crontab"},
    "delegate_parallel": {"rate": 0.33, "issue": "frequent failure (3x)", "alt": "delegate_task sequential"},
}

PROVEN_COMBOS = [
    ("web_search", "web_extract"),
    ("execute_code", "write_file"),
    ("read_file", "patch"),
    ("search_files", "read_file"),
]

def check_tool_before_use(tool_name: str, args: dict) -> dict:
    """Check tool intelligence before executing.
    
    Returns:
        {
            "proceed": bool,
            "warning": str,
            "alternatives": [str],
            "historical_rate": float,
            "suggestion": str
        }
    """
    router = get_tool_router()
    rec = router.recommend(tool_name)
    
    # Add weak tool specifics
    if tool_name in WEAK_TOOLS:
        weak = WEAK_TOOLS[tool_name]
        rec["warning"] = f"{tool_name}: {weak['issue']} ({weak['rate']*100:.0f}% success). Use {weak['alt']}."
        rec["historical_rate"] = weak["rate"]
        if weak["rate"] < 0.2:
            rec["proceed"] = False
    
    # Check for proven combo opportunities
    suggestion = ""
    if tool_name == "web_search":
        suggestion = "Proven combo: follow with web_extract for full content."
    elif tool_name == "execute_code" and "write" in str(args).lower():
        suggestion = "Proven combo: execute_code → write_file for bulk operations."
    
    rec["suggestion"] = suggestion
    
    # Log the decision
    router.log_decision(tool_name, "proceed" if rec["proceed"] else "blocked", "pending")
    
    return rec

def get_proven_combo(tool_name: str) -> str:
    """Get the recommended follow-up tool for a proven combo."""
    for first, second in PROVEN_COMBOS:
        if tool_name == first:
            return second
    return ""

if __name__ == "__main__":
    # Test
    for tool in ["cronjob", "execute_code", "web_search", "delegate_parallel"]:
        rec = check_tool_before_use(tool, {})
        print(f"{tool}: proceed={rec['proceed']}, rate={rec.get('historical_rate', rec['confidence']):.2f}")
        if rec.get("warning"):
            print(f"  WARNING: {rec['warning']}")
        if rec.get("suggestion"):
            print(f"  SUGGESTION: {rec['suggestion']}")
