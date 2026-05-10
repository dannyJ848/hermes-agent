#!/usr/bin/env python3
"""
Token Consumption Tracker — Tracks and optimizes token/tool usage per task.

Based on Jenius-Agent research: optimize both token consumption and tool calls
for maximum efficiency. Tracks per-task-type token budgets, identifies waste,
and suggests optimizations.

Usage:
  tracker = TokenTracker()
  tracker.record_turn(task_type="code", tool="execute_code", tokens_in=500, tokens_out=300)
  report = tracker.get_report()
"""

import json
import sqlite3
import time
from pathlib import Path
from collections import defaultdict

DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"


class TokenTracker:
    """Track token consumption per task type and tool."""
    
    def __init__(self):
        self._ensure_table()
    
    def _ensure_table(self):
        db = sqlite3.connect(str(DB_PATH), timeout=5)
        db.execute("""
            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                tokens_in INTEGER DEFAULT 0,
                tokens_out INTEGER DEFAULT 0,
                speed_ms REAL DEFAULT 0,
                success INTEGER DEFAULT 1,
                created_at REAL
            )
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_token_task ON token_usage(task_type)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_token_tool ON token_usage(tool_name)")
        db.commit()
        db.close()
    
    def record(self, task_type, tool_name, tokens_in=0, tokens_out=0, speed_ms=0, success=True):
        """Record a single tool usage."""
        db = sqlite3.connect(str(DB_PATH), timeout=5)
        db.execute(
            "INSERT INTO token_usage (task_type, tool_name, tokens_in, tokens_out, speed_ms, success, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (task_type, tool_name, tokens_in, tokens_out, speed_ms, 1 if success else 0, time.time())
        )
        db.commit()
        db.close()
    
    def get_report(self, hours=24):
        """Get comprehensive token usage report."""
        db = sqlite3.connect(str(DB_PATH), timeout=5)
        cutoff = time.time() - (hours * 3600)
        
        report = {
            "period_hours": hours,
            "total_tokens_in": 0,
            "total_tokens_out": 0,
            "total_calls": 0,
            "by_tool": [],
            "by_task_type": [],
            "efficiency_tips": [],
        }
        
        # Overall stats
        row = db.execute(
            "SELECT SUM(tokens_in), SUM(tokens_out), COUNT(*) "
            "FROM token_usage WHERE created_at > ?",
            (cutoff,)
        ).fetchone()
        if row:
            report["total_tokens_in"] = row[0] or 0
            report["total_tokens_out"] = row[1] or 0
            report["total_calls"] = row[2] or 0
        
        # Per-tool breakdown
        rows = db.execute(
            "SELECT tool_name, SUM(tokens_in), SUM(tokens_out), COUNT(*), "
            "AVG(speed_ms), SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as failures "
            "FROM token_usage WHERE created_at > ? "
            "GROUP BY tool_name ORDER BY SUM(tokens_in + tokens_out) DESC",
            (cutoff,)
        ).fetchall()
        
        for tool, tin, tout, cnt, avg_speed, failures in rows:
            report["by_tool"].append({
                "tool": tool,
                "tokens_in": tin or 0,
                "tokens_out": tout or 0,
                "total_tokens": (tin or 0) + (tout or 0),
                "calls": cnt,
                "avg_speed_ms": round(avg_speed or 0, 1),
                "failure_rate": round((failures or 0) / max(cnt, 1), 2),
            })
        
        # Per-task-type breakdown
        rows = db.execute(
            "SELECT task_type, SUM(tokens_in), SUM(tokens_out), COUNT(*), "
            "SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as failures "
            "FROM token_usage WHERE created_at > ? "
            "GROUP BY task_type ORDER BY SUM(tokens_in + tokens_out) DESC",
            (cutoff,)
        ).fetchall()
        
        for task, tin, tout, cnt, failures in rows:
            report["by_task_type"].append({
                "task_type": task,
                "tokens_in": tin or 0,
                "tokens_out": tout or 0,
                "total_tokens": (tin or 0) + (tout or 0),
                "calls": cnt,
                "avg_tokens_per_call": round(((tin or 0) + (tout or 0)) / max(cnt, 1), 1),
                "failure_rate": round((failures or 0) / max(cnt, 1), 2),
            })
        
        db.close()
        
        # Generate efficiency tips
        report["efficiency_tips"] = self._generate_tips(report)
        
        return report
    
    def _generate_tips(self, report):
        """Generate optimization tips based on usage patterns."""
        tips = []
        
        # Find high-failure tools
        for tool_data in report.get("by_tool", []):
            if tool_data["failure_rate"] > 0.3:
                tips.append(
                    "HIGH FAILURE: {} has {:.0f}% failure rate — consider pre-checking or using alternatives".format(
                        tool_data["tool"], tool_data["failure_rate"] * 100
                    )
                )
        
        # Find token-heavy tools
        for tool_data in report.get("by_tool", []):
            if tool_data["total_tokens"] > 10000 and tool_data["calls"] > 5:
                avg = tool_data["total_tokens"] / tool_data["calls"]
                tips.append(
                    "TOKEN HEAVY: {} uses ~{:.0f} tokens/call — consider batching or caching".format(
                        tool_data["tool"], avg
                    )
                )
        
        # Find slow tools
        for tool_data in report.get("by_tool", []):
            if tool_data["avg_speed_ms"] > 10000:
                tips.append(
                    "SLOW: {} averages {:.0f}s per call — check for timeouts or alternatives".format(
                        tool_data["tool"], tool_data["avg_speed_ms"] / 1000
                    )
                )
        
        return tips
    
    def get_budget_recommendation(self, task_type, budget_tokens=5000):
        """Recommend optimal tool sequence for a task type within token budget."""
        db = sqlite3.connect(str(DB_PATH), timeout=5)
        
        rows = db.execute(
            "SELECT tool_name, AVG(tokens_in + tokens_out) as avg_tokens, "
            "AVG(CASE WHEN success=1 THEN 1.0 ELSE 0.0 END) as success_rate "
            "FROM token_usage WHERE task_type=? AND created_at > ? "
            "GROUP BY tool_name HAVING COUNT(*) > 2 "
            "ORDER BY success_rate DESC, avg_tokens ASC",
            (task_type, time.time() - 86400 * 7)
        ).fetchall()
        
        db.close()
        
        # Greedy knapsack: pick highest success tools that fit in budget
        selected = []
        remaining = budget_tokens
        for tool, avg_tok, succ_rate in rows:
            if avg_tok <= remaining:
                selected.append({
                    "tool": tool,
                    "avg_tokens": round(avg_tok),
                    "success_rate": round(succ_rate, 2),
                })
                remaining -= avg_tok
        
        return {
            "task_type": task_type,
            "budget": budget_tokens,
            "recommended_sequence": selected,
            "remaining_budget": round(remaining),
        }


def get_token_summary(hours=24):
    """Quick summary for injection into pre_llm_call."""
    try:
        tracker = TokenTracker()
        report = tracker.get_report(hours=hours)
        
        if report["total_calls"] == 0:
            return None
        
        total = report["total_tokens_in"] + report["total_tokens_out"]
        
        # Find top 3 tools by usage
        top_tools = report["by_tool"][:3]
        tool_summary = ", ".join(
            "{}({} calls)".format(t["tool"], t["calls"]) for t in top_tools
        )
        
        # Tips
        tips = report["efficiency_tips"][:2]
        
        parts = [
            "[TOKEN TRACKER — {} calls, ~{} tokens in {}h]".format(
                report["total_calls"], total, hours
            ),
            "Top tools: {}".format(tool_summary),
        ]
        if tips:
            parts.append("Optimization: " + "; ".join(tips))
        
        return " | ".join(parts)
    except Exception:
        return None


if __name__ == "__main__":
    tracker = TokenTracker()
    
    # Record some sample data
    tracker.record("code", "execute_code", 500, 300, 1500, True)
    tracker.record("code", "terminal", 200, 100, 500, True)
    tracker.record("research", "web_research", 300, 800, 2000, True)
    tracker.record("code", "execute_code", 500, 300, 1200, True)
    tracker.record("code", "terminal", 200, 100, 300, False)
    
    report = tracker.get_report(hours=1)
    print("=== Token Tracker Report ===")
    print("Total: {} calls, {} tokens".format(report["total_calls"], report["total_tokens_in"] + report["total_tokens_out"]))
    print("\nBy tool:")
    for t in report["by_tool"]:
        print("  {} — {} tokens, {} calls, {:.0f}% fail".format(
            t["tool"], t["total_tokens"], t["calls"], t["failure_rate"] * 100
        ))
    
    if report["efficiency_tips"]:
        print("\nTips:")
        for tip in report["efficiency_tips"]:
            print("  -", tip)
    
    print("\nBudget recommendation for 'code' (5000 tokens):")
    rec = tracker.get_budget_recommendation("code", 5000)
    for r in rec["recommended_sequence"]:
        print("  {} — {} tokens, {} success".format(r["tool"], r["avg_tokens"], r["success_rate"]))
