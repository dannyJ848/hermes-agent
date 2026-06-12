#!/usr/bin/env python3
"""tool_optimizer.py — Tool-specific optimizer profiles.

Builds profiles for each frequently-used tool:
- Optimal args patterns
- Common failure modes
- Recovery strategies
- Performance characteristics

Usage:
    python3 tool_optimizer.py --build <tool_name>    # Build profile for tool
    python3 tool_optimizer.py --stats                # Show all profiles
    python3 tool_optimizer.py --recommend <tool>     # Get recommendations
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("tool_optimizer")

DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"

# Built-in profiles for high-failure tools
BUILTIN_PROFILES = {
    "terminal": {
        "optimal_patterns": [
            {"pattern": "cd <dir> && <cmd>", "success_rate": 0.85, "note": "Use && chains with cd"},
            {"pattern": "export VAR=value; <cmd>", "success_rate": 0.80, "note": "Export before command"},
        ],
        "common_failures": [
            {"pattern": "cd /path && long_command", "failure_rate": 0.44, "fix": "Split into separate calls or use script file"},
            {"pattern": "rm -rf", "failure_rate": 0.90, "fix": "Use 'trash' instead of 'rm'"},
            {"pattern": "sudo", "failure_rate": 0.70, "fix": "Avoid sudo in agent context"},
        ],
        "recovery_strategies": [
            "Check cwd with 'pwd' before running",
            "Use absolute paths when possible",
            "Write complex commands to script file first",
            "Avoid && chains longer than 2 commands",
        ],
        "performance": {"avg_latency_ms": 2500, "timeout_safe": 30}
    },
    "web_search": {
        "optimal_patterns": [
            {"pattern": "site:example.com keyword", "success_rate": 0.75, "note": "Use site: for targeted search"},
            {"pattern": '"exact phrase"', "success_rate": 0.80, "note": "Quote exact phrases"},
        ],
        "common_failures": [
            {"pattern": "vague query", "failure_rate": 0.64, "fix": "Add site: or filetype: filters"},
            {"pattern": "too many keywords", "failure_rate": 0.50, "fix": "Limit to 3-5 key terms"},
        ],
        "recovery_strategies": [
            "Add site: filter for authoritative sources",
            "Use filetype:pdf for research papers",
            "Try alternative keywords on failure",
            "Limit results to 5 for speed",
        ],
        "performance": {"avg_latency_ms": 3000, "timeout_safe": 15}
    },
    "execute_code": {
        "optimal_patterns": [
            {"pattern": "single-purpose script", "success_rate": 0.90, "note": "One task per script"},
            {"pattern": "use subprocess for shell", "success_rate": 0.85, "note": "subprocess.run > os.system"},
        ],
        "common_failures": [
            {"pattern": "complex multi-tool script", "failure_rate": 0.30, "fix": "Split into smaller scripts"},
            {"pattern": "missing imports", "failure_rate": 0.25, "fix": "Always import at top"},
        ],
        "recovery_strategies": [
            "Keep scripts under 50 lines",
            "Print final result to stdout",
            "Use try/except around tool calls",
            "Import hermes_tools at top",
        ],
        "performance": {"avg_latency_ms": 5000, "timeout_safe": 60}
    },
    "memory": {
        "optimal_patterns": [
            {"pattern": "action='add', target='memory'", "success_rate": 0.95, "note": "Always use target='memory'"},
            {"pattern": "action='replace', old_text='...'", "success_rate": 0.85, "note": "Include old_text for replace"},
        ],
        "common_failures": [
            {"pattern": "missing old_text", "failure_rate": 0.65, "fix": "Always provide old_text for replace"},
            {"pattern": "target='user' without context", "failure_rate": 0.40, "fix": "Use target='memory' for facts"},
        ],
        "recovery_strategies": [
            "Use target='memory' for environment facts",
            "Use target='user' for preferences only",
            "Keep content under 200 chars",
            "Use old_text for replace (not content alone)",
        ],
        "performance": {"avg_latency_ms": 500, "timeout_safe": 5}
    },
    "browser_navigate": {
        "optimal_patterns": [
            {"pattern": "https:// URL", "success_rate": 0.80, "note": "Always include protocol"},
            {"pattern": "wait for load", "success_rate": 0.75, "note": "Allow page to fully load"},
        ],
        "common_failures": [
            {"pattern": "missing https://", "failure_rate": 0.50, "fix": "Always prefix with https://"},
            {"pattern": "dynamic content", "failure_rate": 0.60, "fix": "Use browser_click after navigate"},
        ],
        "recovery_strategies": [
            "Always include https:// prefix",
            "Wait 2s after navigation",
            "Check for CAPTCHA after load",
            "Use browser_snapshot to verify state",
        ],
        "performance": {"avg_latency_ms": 8000, "timeout_safe": 30}
    },
}


class ToolOptimizer:
    """Build and query tool optimization profiles."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_schema()
        self._load_builtin_profiles()
    
    def _ensure_schema(self):
        """Ensure tool_profiles table exists."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tool_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT UNIQUE,
                profile_json TEXT,
                built_in INTEGER DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_builtin_profiles(self):
        """Load built-in profiles into DB."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        for tool_name, profile in BUILTIN_PROFILES.items():
            cur.execute("""
                INSERT OR REPLACE INTO tool_profiles (tool_name, profile_json, built_in)
                VALUES (?, ?, 1)
            """, (tool_name, json.dumps(profile)))
        
        conn.commit()
        conn.close()
        logger.info(f"Loaded {len(BUILTIN_PROFILES)} built-in profiles")
    
    def get_profile(self, tool_name: str) -> dict:
        """Get optimization profile for a tool."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("SELECT profile_json FROM tool_profiles WHERE tool_name = ?", (tool_name,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        
        # Return generic profile
        return {
            "optimal_patterns": [],
            "common_failures": [],
            "recovery_strategies": ["Verify args before calling", "Handle errors gracefully"],
            "performance": {"avg_latency_ms": 3000, "timeout_safe": 30}
        }
    
    def get_recommendations(self, tool_name: str, args: dict = None) -> list[str]:
        """Get actionable recommendations for a tool call."""
        profile = self.get_profile(tool_name)
        recs = []
        
        # Add recovery strategies
        recs.extend(profile.get("recovery_strategies", [])[:3])
        
        # Add pattern-specific advice
        args_json = json.dumps(args) if args else ""
        for pattern in profile.get("common_failures", []):
            if any(kw in args_json.lower() for kw in pattern["pattern"].lower().split()):
                recs.append(f"⚠️  Risk: {pattern['fix']}")
        
        return recs
    
    def record_usage(self, tool_name: str, success: bool):
        """Record tool usage for profile improvement."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO tool_profiles (tool_name, usage_count, success_count, failure_count)
            VALUES (?, 1, ?, ?)
            ON CONFLICT(tool_name) DO UPDATE SET
                usage_count = usage_count + 1,
                success_count = success_count + ?,
                failure_count = failure_count + ?,
                updated_at = CURRENT_TIMESTAMP
        """, (tool_name, 1 if success else 0, 0 if success else 1,
              1 if success else 0, 0 if success else 1))
        
        conn.commit()
        conn.close()
    
    def get_all_stats(self) -> dict:
        """Get stats for all tracked tools."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        cur.execute("""
            SELECT tool_name, usage_count, success_count, failure_count, built_in
            FROM tool_profiles
            ORDER BY usage_count DESC
        """)
        rows = cur.fetchall()
        conn.close()
        
        return {
            r[0]: {
                "usage": r[1], "successes": r[2], "failures": r[3],
                "success_rate": round(r[2] / max(r[1], 1), 3),
                "built_in": bool(r[4])
            }
            for r in rows
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", help="Build profile for tool")
    parser.add_argument("--stats", action="store_true", help="Show all stats")
    parser.add_argument("--recommend", help="Get recommendations for tool")
    parser.add_argument("--args", help="JSON args for recommendation context")
    args = parser.parse_args()
    
    optimizer = ToolOptimizer()
    
    if args.recommend:
        args_dict = json.loads(args.args) if args.args else {}
        recs = optimizer.get_recommendations(args.recommend, args_dict)
        print(f"Recommendations for {args.recommend}:")
        for rec in recs:
            print(f"  • {rec}")
    
    elif args.stats:
        stats = optimizer.get_all_stats()
        print(json.dumps(stats, indent=2))
    
    else:
        # Show all profiles
        for tool in BUILTIN_PROFILES.keys():
            profile = optimizer.get_profile(tool)
            print(f"\n=== {tool} ===")
            print(f"  Success patterns: {len(profile['optimal_patterns'])}")
            print(f"  Known failures: {len(profile['common_failures'])}")
            print(f"  Recovery strategies: {len(profile['recovery_strategies'])}")


if __name__ == "__main__":
    main()
