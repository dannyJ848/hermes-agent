"""Tip Condition Rewriter — generalizes dead tip conditions for better matching.

Problem: 78% of tips have conditions that never match during real tool use.
Root cause: conditions are too specific (from exercise descriptions, not real patterns).

Solution: Rewrite dead tip conditions using patterns from actual tool call logs.
  1. Find tips with 0 votes despite their tool having 50+ calls
  2. Generalize the condition to match on tool_name + status
  3. Keep the recommendation (the actual advice is fine, just the trigger is wrong)
"""

import sqlite3
import os
from pathlib import Path


def find_dead_tips(min_tool_calls=50):
    """Find tips whose conditions never match despite ample opportunity."""
    cer_path = str(Path.home() / ".hermes" / "cerebrum_memory.db")
    db = sqlite3.connect(cer_path, timeout=5)
    
    # Get tool call counts from tool_stats
    tool_calls_path = str(Path.home() / ".hermes" / "tool_stats.db")
    active_tools = {}
    if os.path.exists(tool_calls_path):
        tc = sqlite3.connect(tool_calls_path, timeout=5)
        rows = tc.execute(
            "SELECT tool_name, total_calls FROM tool_capability WHERE total_calls >= ?",
            (min_tool_calls,)
        ).fetchall()
        active_tools = {r[0]: r[1] for r in rows}
        tc.close()
    
    # Find dead tips for active tools
    dead = []
    tips = db.execute(
        "SELECT id, tool_name, condition, recommendation, confidence, tip_type "
        "FROM distilled_tips WHERE upvotes <= 1 AND downvotes = 0"
    ).fetchall()
    
    for tid, tool, cond, rec, conf, ttype in tips:
        call_count = active_tools.get(tool, 0)
        if call_count >= min_tool_calls:
            dead.append({
                "id": tid,
                "tool": tool,
                "condition": cond,
                "recommendation": rec,
                "confidence": conf,
                "type": ttype,
                "tool_calls": call_count,
            })
    
    db.close()
    return dead


def rewrite_condition(tool_name, old_condition):
    """Generalize a tip condition from specific to matchable.
    
    Rules:
    - "When X encounters errors during: Y" → "When X fails"
    - "When using X for: Y" → "When using X"
    - "When performing Y" → "When using X for complex operations"
    - "When analyzing X" → "When working with X data"
    """
    import re
    
    # Pattern 1: "When TOOL encounters errors during: SPECIFIC"
    m = re.match(r"When (\w+) encounters errors during:.*", old_condition)
    if m:
        return f"When {tool_name} fails with an error"
    
    # Pattern 2: "When using TOOL for: SPECIFIC"
    m = re.match(r"When using (\w+) for:.*", old_condition)
    if m:
        return f"When using {tool_name}"
    
    # Pattern 3: "When performing X"
    if old_condition.startswith("When performing "):
        return f"When using {tool_name} for complex operations"
    
    # Pattern 4: "When TOOL fails with SPECIFIC"
    m = re.match(r"When (\w+) fails with (.*)", old_condition)
    if m:
        return f"When {tool_name} fails"
    
    # Pattern 5: "When accessing X with TOOL"
    m = re.match(r"When (.*) with (\w+)", old_condition)
    if m:
        return f"When using {tool_name}"
    
    # Fallback: just use tool name
    return f"When using {tool_name}"


def rewrite_dead_tips(min_tool_calls=50, dry_run=True):
    """Rewrite dead tip conditions to be more matchable."""
    dead = find_dead_tips(min_tool_calls)
    
    cer_path = str(Path.home() / ".hermes" / "cerebrum_memory.db")
    db = sqlite3.connect(cer_path, timeout=5)
    
    rewritten = []
    for tip in dead:
        old_cond = tip["condition"]
        new_cond = rewrite_condition(tip["tool"], old_cond)
        
        if old_cond != new_cond:
            rewritten.append({
                "id": tip["id"],
                "tool": tip["tool"],
                "old": old_cond,
                "new": new_cond,
                "tool_calls": tip["tool_calls"],
            })
            
            if not dry_run:
                db.execute(
                    "UPDATE distilled_tips SET condition = ? WHERE id = ?",
                    (new_cond, tip["id"])
                )
    
    if not dry_run:
        db.commit()
    db.close()
    
    return rewritten


if __name__ == "__main__":
    print("=== Dead Tip Condition Rewriter ===\n")
    
    # Preview
    dead = find_dead_tips(min_tool_calls=20)
    print(f"Found {len(dead)} dead tips (tool has 20+ calls but tip has 0 votes):\n")
    for tip in dead[:10]:
        print(f"  {tip['tool']} ({tip['tool_calls']} calls): {tip['condition'][:60]}")
    
    print()
    
    # Preview rewrites
    rewritten = rewrite_dead_tips(min_tool_calls=20, dry_run=True)
    print(f"\nWould rewrite {len(rewritten)} conditions:\n")
    for r in rewritten[:5]:
        print(f"  {r['tool']} ({r['tool_calls']} calls):")
        print(f"    OLD: {r['old'][:60]}")
        print(f"    NEW: {r['new'][:60]}")
        print()
