#!/usr/bin/env python3
# Adaptive Timeout Calculator
# Adjusts timeouts based on historical tool performance

import sqlite3
import json

class AdaptiveTimeout:
    """Adaptive timeout calculator for tool execution."""
    
    def __init__(self, default_timeout=30.0):
        self.default_timeout = default_timeout
    
    def get_timeout(self, tool_name):
        """Get adaptive timeout for a tool."""
        return get_adaptive_timeout(tool_name, self.default_timeout)

def get_adaptive_timeout(tool_name, default_timeout=30.0):
    """Calculate adaptive timeout for a tool."""
    conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
    c = conn.cursor()
    
    # Get average successful execution time
    c.execute("""
        SELECT AVG(speed_ms), COUNT(*)
        FROM tool_call_log
        WHERE tool_name = ? AND status = 'success'
        AND created_at > strftime('%s', 'now', '-7 days')
    """, (tool_name,))
    avg_ms, count = c.fetchone()
    
    conn.close()
    
    if avg_ms and count >= 3:
        # Timeout = 3x average + 20% buffer, min 5s, max 300s
        timeout = (avg_ms * 3 * 1.2) / 1000.0
        return max(5.0, min(timeout, 300.0))
    
    return default_timeout

def get_all_adaptive_timeouts():
    """Get adaptive timeouts for all tools."""
    conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT tool_name FROM tool_call_log
        WHERE created_at > strftime('%s', 'now', '-7 days')
    """)
    tools = [row[0] for row in c.fetchall()]
    conn.close()
    
    result = {}
    for tool in tools:
        result[tool] = get_adaptive_timeout(tool)
    
    return json.dumps(result, indent=2)

if __name__ == '__main__':
    print(get_all_adaptive_timeouts())
