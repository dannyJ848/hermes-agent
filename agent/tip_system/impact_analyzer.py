#!/usr/bin/env python3
"""Tip Impact Analyzer — measures which distilled tips actually improve outcomes.

Uses the skill_rewards.db to compute per-tip impact scores:
- How many times was this tip injected before a success?
- How many times was it injected before a failure?
- What's the net impact (success rate when present)?

This is the AgentPRM-inspired evaluation layer on top of SAGE skill rewards.
"""
import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime

CEREBRUM = Path.home() / ".hermes" / "cerebrum_memory.db"
REWARDS = Path.home() / ".hermes" / "skill_rewards.db"


def analyze():
    if not REWARDS.exists():
        print("No skill_rewards.db yet — need at least one session with SAGE rewards active.")
        return

    rewards = sqlite3.connect(str(REWARDS), timeout=5)
    cerebrum = sqlite3.connect(str(CEREBRUM), timeout=5)

    # Per-tip impact
    tip_stats = rewards.execute("""
        SELECT tip_id, tool_name,
               SUM(CASE WHEN outcome='success' THEN 1 ELSE 0 END) as successes,
               SUM(CASE WHEN outcome='error' THEN 1 ELSE 0 END) as failures,
               COUNT(*) as total
        FROM skill_rewards
        GROUP BY tip_id
        ORDER BY total DESC
    """).fetchall()

    print(f"{'TIP_ID':>6} {'TOOL':<20} {'SUCC':>5} {'FAIL':>5} {'TOTAL':>6} {'IMPACT':>8} {'REC (first 50 chars)':<52}")
    print("-" * 110)

    high_impact = []
    low_impact = []

    for tip_id, tool, succ, fail, total in tip_stats:
        impact = succ / total if total > 0 else 0
        row = cerebrum.execute("SELECT recommendation FROM distilled_tips WHERE id=?", (tip_id,)).fetchone()
        rec = row[0][:50] if row else "<deleted>"
        marker = ""
        if impact >= 0.8:
            marker = " ★"
            high_impact.append((tip_id, tool, impact))
        elif impact < 0.5 and total >= 3:
            marker = " ✗"
            low_impact.append((tip_id, tool, impact))

        print(f"{tip_id:>6} {tool:<20} {succ:>5} {fail:>5} {total:>6} {impact:>7.1%}{marker} {rec}")

    print(f"\n--- Summary ---")
    print(f"Total tips with reward data: {len(tip_stats)}")
    print(f"High impact (≥80% success): {len(high_impact)}")
    print(f"Low impact (<50% success, ≥3 samples): {len(low_impact)}")

    if low_impact:
        print(f"\nTips to review (low impact):")
        for tip_id, tool, impact in low_impact:
            print(f"  Tip #{tip_id} ({tool}): {impact:.1%} success rate")

    # Per-tool aggregate
    print(f"\n--- Per-Tool Impact ---")
    tool_stats = rewards.execute("""
        SELECT tool_name,
               SUM(CASE WHEN outcome='success' THEN 1 ELSE 0 END),
               SUM(CASE WHEN outcome='error' THEN 1 ELSE 0 END),
               COUNT(*)
        FROM skill_rewards GROUP BY tool_name ORDER BY COUNT(*) DESC
    """).fetchall()
    for tool, succ, fail, total in tool_stats:
        impact = succ / total if total > 0 else 0
        print(f"  {tool:<20} {succ:>4}/{total:<4} = {impact:.1%}")

    rewards.close()
    cerebrum.close()


if __name__ == "__main__":
    if "--help" in sys.argv:
        print("Tip Impact Analyzer — measures which distilled tips actually improve outcomes.")
        print("Usage: python3 tip_impact_analyzer.py [--reset]")
        print("  --reset: Clear all reward data (start fresh)")
        sys.exit(0)
    if "--reset" in sys.argv:
        if REWARDS.exists():
            os.remove(str(REWARDS))
            print("Reward data cleared.")
        sys.exit(0)
    analyze()
