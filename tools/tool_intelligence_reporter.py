#!/usr/bin/env python3
# Tool Success Rate Reporter
# Provides real-time tool performance metrics

import sqlite3
import json

def get_tool_success_rates():
    """Get success rates for all tools."""
    conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
    c = conn.cursor()
    c.execute("""
        SELECT 
            tool_name,
            COUNT(*) as total,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
            AVG(elapsed_ms) as avg_ms,
            MAX(timestamp) as last_used
        FROM tool_call_log
        WHERE timestamp > datetime('now', '-7 days')
        GROUP BY tool_name
        ORDER BY successes DESC
    """)
    results = []
    for row in c.fetchall():
        results.append({
            'tool': row[0],
            'total': row[1],
            'successes': row[2],
            'rate': row[2] / row[1] if row[1] > 0 else 0,
            'avg_ms': round(row[3], 1) if row[3] else None,
            'last_used': row[4]
        })
    conn.close()
    return json.dumps(results, indent=2)

def get_weak_tools(threshold=0.5):
    """Get tools below success threshold."""
    rates = json.loads(get_tool_success_rates())
    weak = [t for t in rates if t['rate'] < threshold and t['total'] > 5]
    return json.dumps(weak, indent=2)

if __name__ == '__main__':
    print(get_tool_success_rates())
