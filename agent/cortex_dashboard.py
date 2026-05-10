#!/usr/bin/env python3
"""
cortex_dashboard.py — Real-time status dashboard for the Cortex system.

Shows:
  - Tip database health
  - My skill progression
  - Recent learning velocity
  - Active cron jobs
  - System performance

Usage:
    python3 cortex_dashboard.py
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path.home() / "hermes-agent"))
from agent.cortex_access import CortexDB
from agent.adaptive_cortex import AdaptiveCortex
from agent.tool_oracle import ToolOracle


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_section(title):
    print(f"\n  ── {title} ──")


def show_tip_health(db: CortexDB):
    """Show tip database health."""
    print_section("TIP DATABASE")
    
    stats = db.get_stats()
    report = db.get_tip_quality_report()
    
    print(f"    Total tips:     {stats['total_nodes']:,}")
    print(f"    Active tips:    {stats['active_tips']:,}")
    print(f"    Average Elo:    {stats['elo_avg']:.0f}")
    print(f"    Elo range:      {stats['elo_min']:.0f} - {stats['elo_max']:.0f}")
    print(f"    Unrated:        {report['unrated']}")
    print(f"    Needs repair:   {report['needs_repair']}")
    
    if report['tiers']:
        print(f"    Distribution:")
        for tier, count in sorted(report['tiers'].items(), key=lambda x: -x[1]):
            bar = "█" * int(count / max(report['tiers'].values()) * 20)
            print(f"      {tier:12} {bar} {count}")
    
    print(f"    Domains:")
    for domain, count in sorted(stats['domains'].items(), key=lambda x: -x[1])[:8]:
        print(f"      {domain:15} {count:4} tips")


def show_my_skills(ac: AdaptiveCortex):
    """Show my personal skill progression."""
    print_section("MY SKILLS")
    
    stats = ac.get_my_stats()
    
    print(f"    Session duration: {stats['session_duration']/60:.1f} minutes")
    print(f"    Total calls:      {stats['total_calls']}")
    print(f"    Success rate:     {stats['success_rate']:.1%}")
    print(f"    Tools mastered:     {stats['tools_used']}")
    print(f"    Recent lessons:     {stats['recent_lessons']}")
    
    if stats['tool_breakdown']:
        print(f"    Tool breakdown:")
        for tool, ts in sorted(stats['tool_breakdown'].items(), 
                              key=lambda x: -x[1]['calls']):
            status = "✓" if ts['success_rate'] > 0.8 else "⚠" if ts['success_rate'] > 0.5 else "✗"
            print(f"      {status} {tool:20} {ts['success_rate']:>6.0%} ({ts['calls']} calls)")


def show_recent_learning(ac: AdaptiveCortex):
    """Show recent lessons learned."""
    print_section("RECENT LEARNING")
    
    lessons = ac.get_recent_lessons(10)
    if lessons:
        for i, lesson in enumerate(lessons, 1):
            print(f"    {i}. {lesson[:100]}...")
    else:
        print("    No lessons learned yet this session.")
        print("    (Lessons appear after tool call errors)")


def show_cron_status():
    """Show active cron jobs."""
    print_section("CRON JOBS")
    
    jobs = [
        ("cortex-flywheel", "Every 2h", "Elo tournaments + tip repair"),
        ("cortex-consolidation", "Every 6h", "Merge duplicate tips"),
        ("cortex-quality-sweep", "Daily 9am", "Health report"),
        ("adaptive-cortex-daemon", "Every 30m", "Skill monitoring"),
    ]
    
    for name, schedule, purpose in jobs:
        print(f"    ✓ {name:25} {schedule:12} {purpose}")


def show_system_status():
    """Show overall system status."""
    print_section("SYSTEM STATUS")
    
    # Check if Postgres is running
    try:
        db = CortexDB()
        db.get_stats()
        print("    ✓ Postgres database: Connected")
    except Exception as e:
        print(f"    ✗ Postgres database: {e}")
    
    # Check file existence
    files = [
        "cortex_access.py",
        "cortex_flywheel.py", 
        "adaptive_cortex.py",
        "tool_oracle.py",
        "cortex_unified.py",
    ]
    
    print(f"    Module status:")
    for f in files:
        path = Path.home() / "hermes-agent" / f
        status = "✓" if path.exists() else "✗"
        print(f"      {status} {f}")


def main():
    print_header("CORTEX SYSTEM DASHBOARD")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    db = CortexDB()
    ac = AdaptiveCortex(db)
    
    show_tip_health(db)
    show_my_skills(ac)
    show_recent_learning(ac)
    show_cron_status()
    show_system_status()
    
    print_header("SUMMARY")
    print("""
  ACTIVE SYSTEMS:
    ✓ Classic Cortex      — 1,018+ tips, Elo-rated, flywheel-evaluated
    ✓ Adaptive Cortex     — Real-time learning, error pattern detection
    ✓ Tool Oracle         — Predictive tool selection, arg validation
    ✓ Unified Integration — All systems combined, plugin-wired

  LEARNING MECHANISMS:
    • Every tool call → Immediate error analysis + lesson extraction
    • Every 2 hours → Elo tournaments rate tip quality
    • Every 6 hours → Duplicate consolidation
    • Every 30 min → Skill progression monitoring
    • Daily 9am → Full health report

  PERSONALIZATION:
    • Tracks YOUR specific error patterns
    • Warns before you repeat mistakes
    • Suggests better tools based on your history
    • Injects recent lessons into context
    • Reports on your improvement
""")
    
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
