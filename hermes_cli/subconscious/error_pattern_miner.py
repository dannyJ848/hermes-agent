#!/usr/bin/env python3
"""
error_pattern_miner.py — Mine error patterns from tool execution history.

Analyzes recent failures to extract recurring error signatures,
classifies by root cause, and generates preventive tips.

Usage:
    from error_pattern_miner import ErrorPatternMiner
    miner = ErrorPatternMiner()
    patterns = miner.mine_recent(hours=24)
    for p in patterns:
        print(p['signature'], p['frequency'], p['preventive_tip'])

Wiring:
    - Call from post_tool_call hook when result contains 'error'
    - Or run as daily cron to analyze error_registry table
"""

import re
import json
import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict

HERMES_HOME = Path.home() / ".hermes"
ERROR_DB = HERMES_HOME / "error_patterns.db"

class ErrorPatternMiner:
    """Mine and classify error patterns from tool execution."""
    
    # Error signature extraction patterns
    PATTERNS = [
        (r"Could not find a match for old_string", "patch_match_failure"),
        (r"No process with ID", "process_not_found"),
        (r"Memory at \d+/\d+ chars", "memory_full"),
        (r"CUDA out of memory", "cuda_oom"),
        (r"OOM killer", "oom_killed"),
        (r"SSH.*Connection refused", "ssh_unreachable"),
        (r"DNS.*not known", "dns_failure"),
        (r"JSONDecodeError", "json_parse_error"),
        (r"IndentationError", "syntax_indentation"),
        (r"sqlite3\.IntegrityError", "sqlite_duplicate"),
        (r"timeout after \d+ seconds", "tool_timeout"),
        (r"No such file or directory", "file_not_found"),
        (r"Permission denied", "permission_denied"),
        (r"Connection reset by peer", "connection_reset"),
        (r"Rate limit exceeded", "rate_limited"),
    ]
    
    def __init__(self):
        self._ensure_db()
    
    def _ensure_db(self):
        ERROR_DB.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(ERROR_DB)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS error_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT,
                    error_text TEXT,
                    signature TEXT,
                    category TEXT,
                    root_cause TEXT,
                    preventive_tip TEXT,
                    context TEXT,
                    session_id TEXT,
                    created_at REAL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_error_signature 
                ON error_events(signature, created_at)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS error_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signature TEXT UNIQUE,
                    category TEXT,
                    frequency INTEGER DEFAULT 0,
                    first_seen REAL,
                    last_seen REAL,
                    preventive_tip TEXT,
                    confidence REAL DEFAULT 0.5
                )
            """)
    
    def extract_signature(self, error_text: str) -> Tuple[str, str]:
        """Extract error signature and category. Returns (signature, category)."""
        for pattern, category in self.PATTERNS:
            if re.search(pattern, error_text, re.IGNORECASE):
                # Normalize: extract the specific variant
                match = re.search(pattern, error_text, re.IGNORECASE)
                if match:
                    # Create a normalized signature
                    context = error_text[max(0, match.start()-50):match.end()+50]
                    signature = hashlib.md5(context.encode()).hexdigest()[:16]
                    return signature, category
        
        # Fallback: generic signature from first 100 chars
        generic = error_text[:100].strip()
        signature = hashlib.md5(generic.encode()).hexdigest()[:16]
        return signature, "unknown"
    
    def generate_tip(self, category: str, error_text: str) -> str:
        """Generate preventive tip based on error category."""
        tips = {
            "patch_match_failure": "When using patch tool, always read the exact current file content first. Use sed or terminal for complex multi-line replacements.",
            "process_not_found": "Process IDs expire quickly. Use process(action='list') before referencing specific PIDs.",
            "memory_full": "Memory approaching limit. Call memory_cortex_bridge.offload_if_needed() before adding new entries.",
            "cuda_oom": "GPU OOM imminent. Reduce batch size, enable gradient checkpointing, or offload to CPU before save.",
            "oom_killed": "System OOM killer triggered. Monitor RAM usage, avoid large CPU tensor moves during checkpoint save.",
            "ssh_unreachable": "DGX SSH unresponsive during heavy training. Use process_poll instead of SSH for status checks.",
            "dns_failure": "DNS resolution failed. Check network connectivity, verify hostname, use IP if DNS unstable.",
            "json_parse_error": "JSON parsing failed. Validate output format, handle control chars, use json.loads(strict=False).",
            "syntax_indentation": "Python indentation error. Use consistent spaces (4), avoid tabs, verify with python -m py_compile.",
            "sqlite_duplicate": "SQLite unique constraint violation. Check for existing records before INSERT, use INSERT OR IGNORE.",
            "tool_timeout": "Tool call timed out. Increase timeout parameter, use background=True for long operations.",
            "file_not_found": "File not found. Verify path exists, use absolute paths, create parent directories first.",
            "permission_denied": "Permission denied. Check file ownership, use chmod/chown, verify write access.",
            "connection_reset": "Connection reset. Retry with exponential backoff, check server health, verify network stability.",
            "rate_limited": "Rate limit hit. Implement exponential backoff, reduce request frequency, check API quotas.",
        }
        return tips.get(category, f"Error category '{category}': Review error context and implement preventive check.")
    
    def record_error(self, tool_name: str, error_text: str, context: str = "", session_id: str = "") -> Dict:
        """Record an error event. Returns mined pattern info."""
        signature, category = self.extract_signature(error_text)
        tip = self.generate_tip(category, error_text)
        now = datetime.now().timestamp()
        
        with sqlite3.connect(str(ERROR_DB)) as conn:
            # Record event
            conn.execute("""
                INSERT INTO error_events 
                (tool_name, error_text, signature, category, root_cause, preventive_tip, context, session_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (tool_name, error_text[:500], signature, category, category, tip,                context[:500] if isinstance(context, str) else str(context)[:500],session_id, now))
            
            # Update pattern frequency
            conn.execute("""
                INSERT INTO error_patterns (signature, category, frequency, first_seen, last_seen, preventive_tip, confidence)
                VALUES (?, ?, 1, ?, ?, ?, 0.5)
                ON CONFLICT(signature) DO UPDATE SET
                    frequency = frequency + 1,
                    last_seen = ?,
                    confidence = min(0.95, confidence + 0.05)
            """, (signature, category, now, now, tip, now))
            
            conn.commit()
        
        return {
            "signature": signature,
            "category": category,
            "preventive_tip": tip,
            "recorded": True
        }
    
    def mine_recent(self, hours: int = 24) -> List[Dict]:
        """Mine patterns from recent errors."""
        cutoff = (datetime.now() - timedelta(hours=hours)).timestamp()
        
        with sqlite3.connect(str(ERROR_DB)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("""
                SELECT signature, category, COUNT(*) as freq, MAX(preventive_tip) as tip
                FROM error_events
                WHERE created_at > ?
                GROUP BY signature
                HAVING freq >= 2
                ORDER BY freq DESC
            """, (cutoff,))
            
            patterns = []
            for row in cur.fetchall():
                patterns.append({
                    "signature": row["signature"],
                    "category": row["category"],
                    "frequency": row["freq"],
                    "preventive_tip": row["tip"],
                    "action": "Add to pre_tool_call validation"
                })
            
            return patterns
    
    def get_top_patterns(self, limit: int = 10) -> List[Dict]:
        """Get most frequent patterns across all time."""
        with sqlite3.connect(str(ERROR_DB)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("""
                SELECT * FROM error_patterns
                ORDER BY frequency DESC, confidence DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cur.fetchall()]
    
    def get_stats(self) -> Dict:
        """Get mining statistics."""
        with sqlite3.connect(str(ERROR_DB)) as conn:
            total_events = conn.execute("SELECT COUNT(*) FROM error_events").fetchone()[0]
            total_patterns = conn.execute("SELECT COUNT(*) FROM error_patterns").fetchone()[0]
            recent_24h = conn.execute(
                "SELECT COUNT(*) FROM error_events WHERE created_at > ?",
                ((datetime.now() - timedelta(hours=24)).timestamp(),)
            ).fetchone()[0]
            
            return {
                "total_events": total_events,
                "total_patterns": total_patterns,
                "recent_24h": recent_24h,
                "db_path": str(ERROR_DB)
            }


# Hook integration for post_tool_call
def post_tool_call_hook(tool_name: str, result: str, **kwargs):
    """Hook to call after every tool call. Records errors if present."""
    if "error" in result.lower() or "failed" in result.lower() or "Traceback" in result:
        miner = ErrorPatternMiner()
        miner.record_error(
            tool_name=tool_name,
            error_text=result,
            context=kwargs.get("args", {}),
            session_id=kwargs.get("session_id", "")
        )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Error Pattern Miner")
    parser.add_argument("--mine", action="store_true", help="Mine recent patterns")
    parser.add_argument("--hours", type=int, default=24, help="Hours to look back")
    parser.add_argument("--top", action="store_true", help="Show top patterns")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    miner = ErrorPatternMiner()
    
    if args.stats:
        print(json.dumps(miner.get_stats(), indent=2))
    elif args.top:
        patterns = miner.get_top_patterns()
        print(json.dumps(patterns, indent=2))
    elif args.mine:
        patterns = miner.mine_recent(hours=args.hours)
        print(json.dumps(patterns, indent=2))
    else:
        print(json.dumps(miner.get_stats(), indent=2))