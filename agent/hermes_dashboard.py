#!/usr/bin/env python3
"""
hermes_dashboard.py — Real-time Hermes cognitive dashboard.

Shows: tip quality trends, tool success rates, cost tracking, 
plugin health, memory stats, active projects.

Usage: python3 hermes_dashboard.py [--refresh 5]
"""

import sqlite3
import time
import os
from datetime import datetime

CEREBRUM_DB = os.path.expanduser("~/.hermes/cerebrum_memory.db")
TOOL_DB = os.path.expanduser("~/.hermes/tool_intelligence.db")

def get_tip_stats():
    conn = sqlite3.connect(CEREBRUM_DB)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM distilled_tips")
    total_tips = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM tip_elo")
    elo_rated = c.fetchone()[0]
    
    c.execute("SELECT AVG(elo) FROM tip_elo")
    avg_elo = c.fetchone()[0] or 1500
    
    c.execute("SELECT COUNT(*) FROM tip_survival WHERE opportunities > 0")
    tracked = c.fetchone()[0]
    
    c.execute("SELECT AVG(survival_rate) FROM tip_survival WHERE opportunities > 0")
    avg_survival = c.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "total": total_tips,
        "elo_rated": elo_rated,
        "avg_elo": round(avg_elo, 0),
        "tracked": tracked,
        "avg_survival": round(avg_survival * 100, 1)
    }

def get_tool_stats():
    conn = sqlite3.connect(TOOL_DB)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM tool_calls")
    total_calls = c.fetchone()[0]
    
    c.execute("SELECT tool_name, success_rate, total_calls FROM tool_performance_summary ORDER BY success_rate DESC LIMIT 10")
    top_tools = c.fetchall()
    
    c.execute("SELECT tool_name, success_rate, total_calls FROM tool_performance_summary ORDER BY success_rate ASC LIMIT 5")
    weak_tools = c.fetchall()
    
    conn.close()
    
    return {
        "total_calls": total_calls,
        "top_tools": top_tools,
        "weak_tools": weak_tools
    }

def get_project_stats():
    conn = sqlite3.connect(CEREBRUM_DB)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM projects")
    total_projects = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM projects WHERE status='active'")
    active_projects = c.fetchone()[0]
    
    conn.close()
    
    return {
        "total": total_projects,
        "active": active_projects
    }

def print_dashboard():
    os.system('clear' if os.name != 'nt' else 'cls')
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║           HERMES COGNITIVE DASHBOARD                         ║")
    print("║           " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "                           ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    tips = get_tip_stats()
    print("\n📚 TIP QUALITY")
    print(f"   Total tips:      {tips['total']}")
    print(f"   Elo-rated:       {tips['elo_rated']} ({tips['avg_elo']} avg)")
    print(f"   Survival tracked:{tips['tracked']}")
    print(f"   Avg survival:     {tips['avg_survival']}%")
    
    tools = get_tool_stats()
    print("\n🔧 TOOL PERFORMANCE")
    print(f"   Total calls:     {tools['total_calls']}")
    print("   Top performers:")
    for t in tools['top_tools'][:5]:
        print(f"     {t[0]:20s} {t[1]*100:5.1f}% ({t[2]} calls)")
    print("   Weak tools:")
    for t in tools['weak_tools']:
        print(f"     {t[0]:20s} {t[1]*100:5.1f}% ({t[2]} calls)")
    
    projects = get_project_stats()
    print("\n📁 PROJECTS")
    print(f"   Total:     {projects['total']}")
    print(f"   Active:    {projects['active']}")
    
    print("\n" + "═" * 62)
    print("Refresh: Ctrl+C to exit")

if __name__ == "__main__":
    import sys
    refresh = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--refresh" else 30
    
    try:
        while True:
            print_dashboard()
            time.sleep(refresh)
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
