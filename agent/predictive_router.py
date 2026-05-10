#!/usr/bin/env python3
"""
predictive_router.py — Route tool calls based on historical success rates.

Before executing a tool, check its historical performance and:
- Route to proven tools (>95% success)
- Warn about weak tools (<80% success)
- Suggest alternatives for failing tools
"""

import sqlite3
import os
from typing import Dict, List, Tuple

TOOL_DB = os.path.expanduser("~/.hermes/tool_intelligence.db")

def get_tool_rankings() -> List[Tuple[str, float, int]]:
    """Get tools ranked by success rate."""
    conn = sqlite3.connect(TOOL_DB)
    c = conn.cursor()
    
    c.execute("""
        SELECT tool_name, success_rate, total_calls
        FROM tool_performance_summary
        ORDER BY success_rate DESC, total_calls DESC
    """)
    
    rankings = c.fetchall()
    conn.close()
    return rankings

def get_tool_recommendation(tool_name: str) -> Dict:
    """Get routing recommendation for a specific tool."""
    conn = sqlite3.connect(TOOL_DB)
    c = conn.cursor()
    
    c.execute("""
        SELECT success_rate, total_calls, avg_duration_ms
        FROM tool_performance_summary
        WHERE tool_name = ?
    """, (tool_name,))
    
    result = c.fetchone()
    conn.close()
    
    if not result:
        return {"status": "unknown", "recommendation": "no_data", "success_rate": None}
    
    rate, calls, avg_dur = result
    
    if rate >= 0.95 and calls >= 10:
        return {"status": "proven", "recommendation": "use", "success_rate": rate, "calls": calls}
    elif rate >= 0.80:
        return {"status": "reliable", "recommendation": "use_with_caution", "success_rate": rate, "calls": calls}
    elif rate >= 0.50:
        return {"status": "weak", "recommendation": "avoid_or_verify", "success_rate": rate, "calls": calls}
    else:
        return {"status": "broken", "recommendation": "avoid", "success_rate": rate, "calls": calls}

def get_best_tool_for_task(task_keywords: List[str]) -> str:
    """Find the best tool for a task based on keywords and success rates."""
    rankings = get_tool_rankings()
    
    # Simple keyword matching
    for tool_name, rate, calls in rankings:
        if calls < 3:  # Need minimum data
            continue
        tool_base = tool_name.replace('_', ' ').lower()
        matches = sum(1 for kw in task_keywords if kw.lower() in tool_base)
        if matches > 0 and rate >= 0.90:
            return tool_name
    
    # Fallback: highest success rate tool with data
    for tool_name, rate, calls in rankings:
        if calls >= 10 and rate >= 0.95:
            return tool_name
    
    return "terminal"  # Ultimate fallback

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        tool = sys.argv[1]
        rec = get_tool_recommendation(tool)
        print(f"{tool}: {rec['status']} ({rec['success_rate']*100:.1f}% success, {rec.get('calls', 0)} calls)")
        print(f"Recommendation: {rec['recommendation']}")
    else:
        print("=== TOOL RANKINGS ===")
        for tool, rate, calls in get_tool_rankings()[:20]:
            status = "✓" if rate >= 0.95 else "~" if rate >= 0.80 else "✗"
            print(f"{status} {tool:30s} {rate*100:5.1f}% ({calls} calls)")
