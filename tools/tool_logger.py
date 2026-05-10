#!/usr/bin/env python3
"""
hermes_tool_logger.py — Universal tool-use logging and analysis.

Logs every tool call with:
- tool_name, args, result, success/failure, duration, timestamp
- auto-analyzes patterns: "what tools work for X?"
- integrates with existing tool_intelligence.db

Usage:
  from hermes_tool_logger import log_tool_call, analyze_tool_patterns
  
  # In any tool wrapper:
  result = log_tool_call("web_search", {"query": "AI agents"}, actual_result)
  
  # Analyze:
  patterns = analyze_tool_patterns("file operations")
"""

import sqlite3
import json
import time
import hashlib
from pathlib import Path

TOOL_LOG_DB = Path.home() / ".hermes" / "tool_intelligence.db"

def _ensure_db():
    conn = sqlite3.connect(str(TOOL_LOG_DB))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tool_calls_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_name TEXT NOT NULL,
            args_hash TEXT,
            args_preview TEXT,
            result_preview TEXT,
            success INTEGER DEFAULT 1,
            error_type TEXT,
            duration_ms INTEGER,
            context_tags TEXT,
            timestamp REAL DEFAULT (strftime('%s', 'now'))
        )
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_tool_name ON tool_calls_v2(tool_name)
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp ON tool_calls_v2(timestamp)
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_success ON tool_calls_v2(success)
    """)
    conn.commit()
    conn.close()

def log_tool_call(tool_name: str, args: dict, result, success: bool = True, 
                  error: str = None, duration_ms: int = None, context: str = ""):
    """Log a tool call with full metadata."""
    _ensure_db()
    
    args_hash = hashlib.md5(json.dumps(args, sort_keys=True, default=str).encode()).hexdigest()[:16]
    args_preview = json.dumps(args, default=str)[:500]
    result_preview = str(result)[:500] if result else ""
    error_type = error.split(":")[0] if error else None
    
    conn = sqlite3.connect(str(TOOL_LOG_DB))
    c = conn.cursor()
    c.execute("""
        INSERT INTO tool_calls_v2 
        (tool_name, args_hash, args_preview, result_preview, success, error_type, duration_ms, context_tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (tool_name, args_hash, args_preview, result_preview, 
          1 if success else 0, error_type, duration_ms, context))
    conn.commit()
    conn.close()
    
    return result

def analyze_tool_patterns(query: str = None, tool_name: str = None, 
                          time_window_hours: int = 24):
    """Analyze tool usage patterns."""
    _ensure_db()
    conn = sqlite3.connect(str(TOOL_LOG_DB))
    c = conn.cursor()
    
    since = time.time() - (time_window_hours * 3600)
    
    if tool_name:
        # Analyze specific tool
        c.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(success) as successes,
                AVG(duration_ms) as avg_duration,
                error_type,
                COUNT(*) as error_count
            FROM tool_calls_v2
            WHERE tool_name = ? AND timestamp > ?
            GROUP BY error_type
            ORDER BY total DESC
        """, (tool_name, since))
        rows = c.fetchall()
        total = sum(r[0] for r in rows)
        successes = sum(r[1] for r in rows if r[1])
        return {
            "tool": tool_name,
            "total_calls": total,
            "success_rate": successes / total if total else 0,
            "avg_duration_ms": rows[0][2] if rows else 0,
            "error_breakdown": {r[3]: r[4] for r in rows if r[3]},
            "recommendation": "USE" if (successes/total if total else 0) > 0.8 else "CAUTION" if (successes/total if total else 0) > 0.5 else "AVOID"
        }
    
    elif query:
        # Find tools matching context query
        c.execute("""
            SELECT tool_name, COUNT(*) as cnt, SUM(success) as successes
            FROM tool_calls_v2
            WHERE context_tags LIKE ? AND timestamp > ?
            GROUP BY tool_name
            ORDER BY cnt DESC
        """, (f"%{query}%", since))
        rows = c.fetchall()
        return {
            "query": query,
            "matching_tools": [
                {
                    "tool": r[0], 
                    "calls": r[1], 
                    "success_rate": r[2]/r[1] if r[1] else 0,
                    "recommendation": "USE" if r[2]/r[1] > 0.8 else "CAUTION"
                }
                for r in rows[:5]
            ]
        }
    
    else:
        # Overall health report
        c.execute("""
            SELECT tool_name, COUNT(*) as cnt, SUM(success) as successes
            FROM tool_calls_v2
            WHERE timestamp > ?
            GROUP BY tool_name
            ORDER BY cnt DESC
        """, (since,))
        rows = c.fetchall()
        return {
            "time_window_hours": time_window_hours,
            "tools_tracked": len(rows),
            "top_tools": [
                {"tool": r[0], "calls": r[1], "success_rate": r[2]/r[1] if r[1] else 0}
                for r in rows[:10]
            ],
            "weak_tools": [
                {"tool": r[0], "calls": r[1], "success_rate": r[2]/r[1] if r[1] else 0}
                for r in rows if r[1] >= 5 and r[2]/r[1] < 0.5
            ]
        }
    
    conn.close()

def get_tool_recommendation(task_description: str):
    """Get tool recommendation for a task based on historical performance."""
    _ensure_db()
    
    # Extract keywords from task
    keywords = task_description.lower().split()
    
    # Find best tools for similar tasks
    conn = sqlite3.connect(str(TOOL_LOG_DB))
    c = conn.cursor()
    
    since = time.time() - (7 * 24 * 3600)  # Last week
    
    c.execute("""
        SELECT tool_name, COUNT(*) as cnt, SUM(success) as successes, AVG(duration_ms) as avg_dur
        FROM tool_calls_v2
        WHERE context_tags LIKE ? AND timestamp > ?
        GROUP BY tool_name
        HAVING cnt >= 3
        ORDER BY (successes * 1.0 / cnt) DESC, cnt DESC
        LIMIT 5
    """, (f"%{task_description[:30]}%", since))
    
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        return {"recommendation": "NO_DATA", "suggested_tools": []}
    
    best = rows[0]
    return {
        "recommendation": "USE" if best[2]/best[1] > 0.8 else "CAUTION",
        "suggested_tools": [
            {
                "tool": r[0],
                "success_rate": r[2]/r[1] if r[1] else 0,
                "avg_duration_ms": r[3] or 0,
                "confidence": "HIGH" if r[2]/r[1] > 0.9 and r[1] > 10 else "MEDIUM"
            }
            for r in rows
        ]
    }

if __name__ == "__main__":
    # Test
    print("=== Tool Logger Test ===")
    log_tool_call("web_search", {"query": "AI agents"}, {"results": 5}, success=True, context="research")
    log_tool_call("cronjob", {"action": "list"}, None, success=False, error="KeyError: 'id'", context="health")
    
    print("\nOverall health:")
    health = analyze_tool_patterns(time_window_hours=1)
    print(f"Tools tracked: {health['tools_tracked']}")
    for t in health['top_tools'][:3]:
        print(f"  {t['tool']}: {t['calls']} calls, {t['success_rate']*100:.0f}% success")
    
    print("\nRecommendation for 'research':")
    rec = get_tool_recommendation("research")
    for t in rec['suggested_tools']:
        print(f"  {t['tool']}: {t['success_rate']*100:.0f}% ({t['confidence']})")
    
    print("\n=== Tool Logger Ready ===")
