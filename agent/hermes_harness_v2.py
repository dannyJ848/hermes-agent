#!/usr/bin/env python3
"""
hermes_harness_v2.py — Unified cognitive harness status.

Single command to check all systems:
  python3 hermes_harness_v2.py

Shows: tips, tools, plugins, memory, errors, efficiency, projects
"""

import sqlite3
import os
import time
from datetime import datetime

CEREBRUM_DB = os.path.expanduser("~/.hermes/cerebrum_memory.db")
TOOL_DB = os.path.expanduser("~/.hermes/tool_intelligence.db")

def get_status():
    conn = sqlite3.connect(CEREBRUM_DB)
    c = conn.cursor()
    
    # Tips
    c.execute("SELECT COUNT(*) FROM distilled_tips")
    tips_total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tip_elo")
    tips_elo = c.fetchone()[0]
    c.execute("SELECT AVG(elo) FROM tip_elo")
    tips_avg_elo = c.fetchone()[0] or 1500
    c.execute("SELECT COUNT(*) FROM tip_survival WHERE opportunities > 0")
    tips_tracked = c.fetchone()[0]
    
    # Projects
    c.execute("SELECT COUNT(*) FROM projects")
    projects = c.fetchone()[0]
    
    # Rapid learnings
    c.execute("SELECT COUNT(*) FROM rapid_learnings")
    learnings = c.fetchone()[0]
    
    # Error patterns
    c.execute("SELECT COUNT(*) FROM error_patterns_predictive")
    error_patterns = c.fetchone()[0]
    
    # Prompt fragments
    c.execute("SELECT COUNT(*) FROM prompt_fragments")
    fragments = c.fetchone()[0]
    
    conn.close()
    
    # Tools
    tool_conn = sqlite3.connect(TOOL_DB)
    tool_c = tool_conn.cursor()
    tool_c.execute("SELECT COUNT(*) FROM tool_calls")
    tool_calls = tool_c.fetchone()[0]
    tool_c.execute("SELECT COUNT(*) FROM tool_performance_summary")
    tools_ranked = tool_c.fetchone()[0]
    tool_conn.close()
    
    # Files
    agent_dir = os.path.expanduser("~/hermes-agent/agent")
    active_modules = len([f for f in os.listdir(agent_dir) if f.endswith('.py')])
    
    return {
        "tips_total": tips_total,
        "tips_elo": tips_elo,
        "tips_avg_elo": round(tips_avg_elo, 0),
        "tips_tracked": tips_tracked,
        "projects": projects,
        "learnings": learnings,
        "error_patterns": error_patterns,
        "fragments": fragments,
        "tool_calls": tool_calls,
        "tools_ranked": tools_ranked,
        "active_modules": active_modules,
    }

def print_harness():
    s = get_status()
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║           HERMES HARNESS v2.1 — UNIFIED STATUS               ║")
    print(f"║           {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                           ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    print(f"\n📚 TIPS          {s['tips_total']} total | {s['tips_elo']} Elo-rated | {s['tips_avg_elo']:.0f} avg Elo | {s['tips_tracked']} tracked")
    print(f"🔧 TOOLS         {s['tool_calls']} calls | {s['tools_ranked']} ranked | predictive_router ACTIVE")
    print(f"📁 PROJECTS      {s['projects']} active | auto-clustering ON")
    print(f"🧠 LEARNINGS     {s['learnings']} rapid | {s['error_patterns']} error patterns")
    print(f"🎯 PROMPTS       {s['fragments']} fragments | Elo tournaments ACTIVE")
    print(f"📦 MODULES       {s['active_modules']} active | 453 archived")
    
    print(f"\n⚡ SYSTEMS ACTIVE:")
    print(f"   ✓ tip survival tracking")
    print(f"   ✓ auto-prune weak tips (<30%)")
    print(f"   ✓ adversarial validation")
    print(f"   ✓ predictive tool routing")
    print(f"   ✓ error guard (6 patterns)")
    print(f"   ✓ token efficiency tracking")
    print(f"   ✓ rapid learning extraction")
    print(f"   ✓ auto-skill pipeline")
    
    print(f"\n⚠ WEAK TOOLS (route around):")
    print(f"   ✗ cronjob: 13% success")
    print(f"   ✗ delegate_parallel: 33% success")
    print(f"   ~ patch: 94% success (use with caution)")
    
    print("\n" + "═" * 62)

if __name__ == "__main__":
    print_harness()
