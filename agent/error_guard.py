#!/usr/bin/env python3
"""
error_guard.py — Pre-emptive error prevention system.

Checks tool calls against known failure patterns before execution.
"""

import sqlite3
import os
from typing import Optional, Dict, List

CEREBRUM_DB = os.path.expanduser("~/.hermes/cerebrum_memory.db")

def check_tool_call(tool_name: str, args: Dict) -> Optional[Dict]:
    """Check if a tool call matches known failure patterns. Returns warning or None."""
    
    conn = sqlite3.connect(CEREBRUM_DB)
    c = conn.cursor()
    
    # Get patterns for this tool
    c.execute("""
        SELECT pattern_name, trigger_condition, predicted_error, prevention_strategy
        FROM error_patterns_predictive
        WHERE trigger_tool = ?
    """, (tool_name,))
    
    patterns = c.fetchall()
    conn.close()
    
    for pattern_name, condition, predicted_error, prevention in patterns:
        # Check if condition matches args
        if _matches_condition(args, condition):
            return {
                'pattern': pattern_name,
                'predicted_error': predicted_error,
                'prevention': prevention,
                'severity': 'HIGH' if 'abort' in predicted_error or 'failure' in predicted_error else 'MEDIUM'
            }
    
    return None

def _matches_condition(args: Dict, condition: str) -> bool:
    """Check if args match the trigger condition."""
    args_str = str(args).lower()
    condition_lower = condition.lower()
    
    # Simple keyword matching
    keywords = condition_lower.split()
    matches = sum(1 for kw in keywords if kw in args_str)
    return matches >= len(keywords) * 0.5

def get_prevention_strategy(tool_name: str, args: Dict) -> List[str]:
    """Get prevention strategies for a tool call."""
    warning = check_tool_call(tool_name, args)
    if warning:
        return [warning['prevention']]
    
    # Default strategies
    defaults = {
        'patch': ['Read file first to verify exact text', 'Use write_file for full replacements'],
        'cronjob': ['Always specify schedule', 'Use terminal with crontab -l first'],
        'delegate_parallel': ['Use delegate_task instead', 'Break into sequential calls'],
        'execute_code': ['Check imports exist', 'Handle database errors gracefully'],
    }
    
    return defaults.get(tool_name, ['Verify args before execution'])

if __name__ == "__main__":
    import sys
    
    # Test predictions
    test_cases = [
        ('patch', {'old_string': 'foo', 'new_string': 'foo'}),
        ('cronjob', {'action': 'create'}),
        ('delegate_parallel', {'tasks': []}),
        ('execute_code', {'code': 'import psycopg2'}),
    ]
    
    for tool, args in test_cases:
        result = check_tool_call(tool, args)
        if result:
            print(f"⚠ {tool}: {result['pattern']} — {result['predicted_error']}")
            print(f"  → {result['prevention']}")
        else:
            print(f"✓ {tool}: no known issues")
