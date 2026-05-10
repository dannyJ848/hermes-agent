#!/usr/bin/env python3
"""
tool_intelligence_tracker.py — Track and analyze tool usage patterns.

Records every tool call: success/failure, duration, token cost, error type.
Provides insights for routing decisions and self-improvement.

Usage:
    from tool_intelligence_tracker import ToolIntelligenceTracker
    tracker = ToolIntelligenceTracker()
    tracker.record_call("web_search", success=True, duration_ms=1200, tokens=150)
    
    # Get recommendations
    intel = tracker.get_intelligence()
    print(intel['weak_tools'])  # Tools to avoid
    print(intel['proven_tools'])  # Reliable tools

Wiring:
    - Call from post_tool_call hook
    - Or wrap tool dispatch in model_tools.py
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

HERMES_HOME = Path.home() / ".hermes"
INTEL_DB = HERMES_HOME / "tool_intelligence.db"

@dataclass
class ToolCall:
    tool_name: str
    success: bool
    duration_ms: float
    tokens_in: int = 0
    tokens_out: int = 0
    error_type: str = ""
    error_message: str = ""
    context: str = ""  # What was the agent trying to do
    timestamp: float = 0.0

class ToolIntelligenceTracker:
    """Track tool performance and provide routing recommendations."""
    
    def __init__(self):
        self._ensure_db()
    
    def _ensure_db(self):
        INTEL_DB.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(INTEL_DB)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT,
                    success BOOLEAN,
                    duration_ms REAL,
                    tokens_in INTEGER,
                    tokens_out INTEGER,
                    error_type TEXT,
                    error_message TEXT,
                    context TEXT,
                    session_id TEXT,
                    timestamp REAL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tool_name_time 
                ON tool_calls(tool_name, timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_success 
                ON tool_calls(success, tool_name)
            """)
            
            # Aggregated stats table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_stats (
                    tool_name TEXT PRIMARY KEY,
                    total_calls INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    avg_duration_ms REAL DEFAULT 0,
                    avg_tokens_in REAL DEFAULT 0,
                    avg_tokens_out REAL DEFAULT 0,
                    last_used REAL,
                    failure_rate REAL DEFAULT 0,
                    confidence_score REAL DEFAULT 0.5
                )
            """)
    
    def record_call(self, tool_name: str, success: bool, duration_ms: float = 0,
                    tokens_in: int = 0, tokens_out: int = 0,
                    error_type: str = "", error_message: str = "",
                    context: str = "", session_id: str = ""):
        """Record a tool call outcome."""
        now = time.time()
        
        with sqlite3.connect(str(INTEL_DB)) as conn:
            conn.execute("""
                INSERT INTO tool_calls
                (tool_name, success, duration_ms, tokens_in, tokens_out,
                 error_type, error_message, context, session_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (tool_name, success, duration_ms, tokens_in, tokens_out,
                  error_type, error_message, context, session_id, now))
            
            # Update aggregated stats
            conn.execute("""
                INSERT INTO tool_stats (tool_name, total_calls, success_count, failure_count,
                                       avg_duration_ms, last_used, failure_rate)
                VALUES (?, 1, ?, ?, ?, ?, ?)
                ON CONFLICT(tool_name) DO UPDATE SET
                    total_calls = total_calls + 1,
                    success_count = success_count + excluded.success_count,
                    failure_count = failure_count + excluded.failure_count,
                    avg_duration_ms = (avg_duration_ms * total_calls + excluded.avg_duration_ms) / (total_calls + 1),
                    last_used = excluded.last_used,
                    failure_rate = CAST(failure_count AS REAL) / total_calls
            """, (tool_name, 1 if success else 0, 0 if success else 1, 
                  duration_ms, now, 0 if success else 1))
            
            conn.commit()
    
    def get_intelligence(self, lookback_hours: int = 24) -> Dict:
        """Get comprehensive tool intelligence."""
        cutoff = time.time() - (lookback_hours * 3600)
        
        with sqlite3.connect(str(INTEL_DB)) as conn:
            conn.row_factory = sqlite3.Row
            
            # Overall stats
            total = conn.execute("SELECT COUNT(*) FROM tool_calls WHERE timestamp > ?", (cutoff,)).fetchone()[0]
            
            # Per-tool stats
            cur = conn.execute("""
                SELECT tool_name, total_calls, success_count, failure_count,
                       avg_duration_ms, failure_rate
                FROM tool_stats
                WHERE last_used > ?
                ORDER BY total_calls DESC
            """, (cutoff,))
            
            tools = []
            weak_tools = []
            proven_tools = []
            
            for row in cur.fetchall():
                tool_data = dict(row)
                tools.append(tool_data)
                
                if tool_data['failure_rate'] > 0.3 and tool_data['total_calls'] >= 5:
                    weak_tools.append({
                        'tool': tool_data['tool_name'],
                        'failure_rate': round(tool_data['failure_rate'] * 100, 1),
                        'calls': tool_data['total_calls'],
                        'recommendation': 'Avoid or use with fallback'
                    })
                elif tool_data['failure_rate'] < 0.1 and tool_data['total_calls'] >= 5:
                    proven_tools.append({
                        'tool': tool_data['tool_name'],
                        'success_rate': round((1 - tool_data['failure_rate']) * 100, 1),
                        'calls': tool_data['total_calls'],
                        'avg_duration_ms': round(tool_data['avg_duration_ms'], 0),
                        'recommendation': 'Reliable - use freely'
                    })
            
            # Recent error patterns
            cur = conn.execute("""
                SELECT error_type, COUNT(*) as freq, tool_name
                FROM tool_calls
                WHERE timestamp > ? AND success = 0 AND error_type != ''
                GROUP BY error_type
                ORDER BY freq DESC
                LIMIT 10
            """, (cutoff,))
            
            error_patterns = [dict(row) for row in cur.fetchall()]
            
            return {
                'total_calls_24h': total,
                'tools_analyzed': len(tools),
                'weak_tools': weak_tools,
                'proven_tools': proven_tools,
                'error_patterns': error_patterns,
                'lookback_hours': lookback_hours
            }
    
    def get_tool_recommendation(self, tool_name: str) -> Dict:
        """Get specific recommendation for a tool."""
        with sqlite3.connect(str(INTEL_DB)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM tool_stats WHERE tool_name = ?
            """, (tool_name,)).fetchone()
            
            if not row:
                return {'tool': tool_name, 'known': False, 'recommendation': 'No data - use with caution'}
            
            data = dict(row)
            failure_rate = data['failure_rate']
            
            if failure_rate > 0.5:
                rec = 'DANGER: High failure rate. Avoid or find alternative.'
            elif failure_rate > 0.3:
                rec = 'WARNING: Unreliable. Use only with fallback plan.'
            elif failure_rate > 0.1:
                rec = 'CAUTION: Moderate failure rate. Verify results.'
            else:
                rec = 'SAFE: Low failure rate. Reliable tool.'
            
            return {
                'tool': tool_name,
                'known': True,
                'total_calls': data['total_calls'],
                'failure_rate': round(failure_rate * 100, 1),
                'avg_duration_ms': round(data['avg_duration_ms'], 0),
                'recommendation': rec
            }


# Hook integration
def post_tool_call_tracker(tool_name: str, result: str, duration_ms: float = 0, **kwargs):
    """Hook to track every tool call."""
    success = not ('error' in result.lower() or 'failed' in result.lower() or 'Traceback' in result)
    
    error_type = ""
    error_message = ""
    if not success:
        # Extract error type from result
        if 'Traceback' in result:
            error_type = "python_exception"
        elif 'timeout' in result.lower():
            error_type = "timeout"
        elif 'permission' in result.lower():
            error_type = "permission_denied"
        elif 'not found' in result.lower():
            error_type = "not_found"
        else:
            error_type = "unknown"
        error_message = result[:200]
    
    tracker = ToolIntelligenceTracker()
    tracker.record_call(
        tool_name=tool_name,
        success=success,
        duration_ms=duration_ms,
        error_type=error_type,
        error_message=error_message,
        context=kwargs.get('args', {})
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Tool Intelligence Tracker")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--tool", type=str, help="Get recommendation for specific tool")
    
    args = parser.parse_args()
    
    tracker = ToolIntelligenceTracker()
    
    if args.tool:
        print(json.dumps(tracker.get_tool_recommendation(args.tool), indent=2))
    else:
        print(json.dumps(tracker.get_intelligence(), indent=2))
