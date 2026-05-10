#!/usr/bin/env python3
"""
tool_router_v2.py — Smart tool routing with failure prediction.

Uses live tool intelligence to:
1. Route around weak tools (<50% success)
2. Suggest proven alternatives
3. Predict failures before they happen
4. Auto-retry with proven combos
"""

import sqlite3
import os
import time
from typing import Dict, List, Tuple, Optional

TOOL_DB = os.path.expanduser("~/.hermes/tool_intelligence.db")
CEREBRUM_DB = os.path.expanduser("~/.hermes/cerebrum_memory.db")

# Known weak tools from historical data
WEAK_TOOLS = {
    'cronjob': {'success_rate': 0.13, 'issue': 'id field confusion', 'alternative': 'terminal with cron syntax'},
    'delegate_parallel': {'success_rate': 0.33, 'issue': 'frequent failure (3x)', 'alternative': 'delegate_task sequential'},
    'patch': {'success_rate': 0.85, 'issue': 'old_string mismatch', 'alternative': 'write_file for small files, execute_code for bulk'},
}

# Proven combos from cross-session memory
PROVEN_COMBOS = [
    ('web_search', 'web_extract'),
    ('execute_code', 'write_file'),
    ('read_file', 'patch'),
    ('search_files', 'read_file'),
]

def get_tool_health(tool_name: str) -> Dict:
    """Get comprehensive tool health report."""
    conn = sqlite3.connect(TOOL_DB)
    c = conn.cursor()
    
    # Recent success rate (last 20 calls)
    c.execute("""
        SELECT success, COUNT(*) 
        FROM tool_calls 
        WHERE tool_name = ? 
        ORDER BY timestamp DESC 
        LIMIT 20
    """, (tool_name,))
    recent = c.fetchall()
    
    # Overall stats
    c.execute("""
        SELECT success_rate, total_calls, avg_duration_ms
        FROM tool_performance_summary
        WHERE tool_name = ?
    """, (tool_name,))
    overall = c.fetchone()
    
    # Recent error patterns
    c.execute("""
        SELECT error_type, COUNT(*) as cnt
        FROM tool_calls
        WHERE tool_name = ? AND success = 0 AND error_type IS NOT NULL
        GROUP BY error_type
        ORDER BY cnt DESC
        LIMIT 3
    """, (tool_name,))
    errors = c.fetchall()
    
    conn.close()
    
    recent_success = sum(1 for r in recent if r[0]) / len(recent) if recent else 0
    
    return {
        'tool': tool_name,
        'recent_success_rate': recent_success,
        'overall_success_rate': overall[0] if overall else 0,
        'total_calls': overall[1] if overall else 0,
        'avg_duration_ms': overall[2] if overall else 0,
        'top_errors': [e[0] for e in errors],
        'status': 'healthy' if recent_success >= 0.8 else 'degraded' if recent_success >= 0.5 else 'broken'
    }

def route_tool_call(tool_name: str, args: Dict) -> Dict:
    """Smart routing decision with failure prediction."""
    
    # Check known weak tools first
    if tool_name in WEAK_TOOLS:
        weak = WEAK_TOOLS[tool_name]
        health = get_tool_health(tool_name)
        
        if health['recent_success_rate'] < 0.5:
            return {
                'decision': 'AVOID',
                'tool': tool_name,
                'reason': f"Known weak tool: {weak['issue']}",
                'alternative': weak['alternative'],
                'confidence': 0.9
            }
    
    # Check live health
    health = get_tool_health(tool_name)
    
    if health['status'] == 'broken':
        return {
            'decision': 'AVOID',
            'tool': tool_name,
            'reason': f"Recent success rate {health['recent_success_rate']:.0%}",
            'alternative': 'terminal fallback',
            'confidence': 0.85
        }
    
    if health['status'] == 'degraded':
        return {
            'decision': 'CAUTION',
            'tool': tool_name,
            'reason': f"Degraded: {health['recent_success_rate']:.0%} success",
            'suggestion': 'Verify args carefully, have fallback ready',
            'confidence': 0.7
        }
    
    return {
        'decision': 'PROCEED',
        'tool': tool_name,
        'reason': f"Healthy: {health['recent_success_rate']:.0%} success",
        'confidence': 0.95
    }

def get_proven_combo(task_type: str) -> List[str]:
    """Get proven tool combo for a task type."""
    combos = {
        'research': ['web_search', 'web_extract'],
        'file_edit': ['read_file', 'write_file'],
        'code_exec': ['execute_code'],
        'debug': ['search_files', 'read_file', 'execute_code'],
        'deploy': ['terminal', 'process'],
    }
    return combos.get(task_type, ['terminal'])

def predict_failure(tool_name: str, args: Dict) -> Optional[str]:
    """Predict if this tool call will fail based on patterns."""
    
    # Patch-specific predictions
    if tool_name == 'patch':
        if 'old_string' in args and len(args['old_string']) < 20:
            return "old_string too short — likely ambiguous match"
        if 'old_string' in args and 'new_string' in args:
            if args['old_string'] == args['new_string']:
                return "old_string and new_string are identical"
    
    # Cron-specific predictions
    if tool_name == 'cronjob':
        if 'action' in args and args['action'] == 'create':
            if 'schedule' not in args or not args['schedule']:
                return "Missing schedule parameter"
    
    # Delegate-specific predictions
    if tool_name == 'delegate_parallel':
        return "Historical 3x failure rate — use delegate_task instead"
    
    return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        tool = sys.argv[1]
        health = get_tool_health(tool)
        print(f"=== {tool} HEALTH ===")
        for k, v in health.items():
            print(f"  {k}: {v}")
    else:
        print("=== WEAK TOOLS (AVOID) ===")
        for tool, info in WEAK_TOOLS.items():
            health = get_tool_health(tool)
            print(f"  {tool}: {health['recent_success_rate']:.0%} success — {info['issue']}")
            print(f"    → Use: {info['alternative']}")
        
        print("\n=== PROVEN COMBOS ===")
        for a, b in PROVEN_COMBOS:
            print(f"  {a} → {b}")
