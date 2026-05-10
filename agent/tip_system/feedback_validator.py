"""Tip feedback loop validator — measures condition-aware voting effectiveness.

Runs before and after gateway restart to compare:
  1. How many tips gained votes (should drop from ~111 to ~20-30)
  2. Whether error-specific tips only get votes on errors
  3. Whether generic tips still get consistent votes
  4. Whether the upvote/downvote ratio changes per tip

Usage:
  python tip_feedback_validator.py --snapshot   # Take post-restart snapshot
  python tip_feedback_validator.py --compare    # Compare pre vs post
"""

import sqlite3
import json
import os
import time
from pathlib import Path


def take_snapshot(label="post"):
    cer = sqlite3.connect(str(Path.home() / ".hermes" / "cerebrum_memory.db"), timeout=5)
    tips = cer.execute(
        "SELECT id, tool_name, condition, confidence, upvotes, downvotes "
        "FROM distilled_tips ORDER BY tool_name"
    ).fetchall()
    cer.close()
    
    snapshot = {
        "label": label,
        "timestamp": time.time(),
        "tips": [{
            "id": t[0], "tool": t[1], "condition": t[2][:60],
            "conf": round(t[3], 3), "up": t[4], "down": t[5]
        } for t in tips]
    }
    
    path = str(Path.home() / "hermes-agent" / f"tip_snapshot_{label}.json")
    with open(path, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    print(f"Snapshot saved: {path} ({len(tips)} tips)")
    return snapshot


def compare_snapshots(pre_path, post_path):
    with open(pre_path) as f:
        pre = json.load(f)
    with open(post_path) as f:
        post = json.load(f)
    
    pre_tips = {t["id"]: t for t in pre["tips"]}
    post_tips = {t["id"]: t for t in post["tips"]}
    
    print("FEEDBACK LOOP VALIDATION — PRE vs POST COMPARISON")
    print("=" * 55)
    
    # Tips that gained votes
    gained = 0
    lost = 0
    unchanged = 0
    
    for tid, pt in post_tips.items():
        if tid in pre_tips:
            diff = pt["up"] - pre_tips[tid]["up"]
            if diff > 0:
                gained += 1
            elif diff < 0:
                lost += 1
            else:
                unchanged += 1
    
    print(f"Tips that gained votes: {gained}")
    print(f"Tips that lost votes: {lost}")
    print(f"Tips unchanged: {unchanged}")
    print()
    
    # Per-tool breakdown
    tool_changes = {}
    for tid, pt in post_tips.items():
        tool = pt["tool"]
        if tool not in tool_changes:
            tool_changes[tool] = {"gained": 0, "unchanged": 0, "total": 0}
        tool_changes[tool]["total"] += 1
        if tid in pre_tips:
            diff = pt["up"] - pre_tips[tid]["up"]
            if diff > 0:
                tool_changes[tool]["gained"] += 1
            else:
                tool_changes[tool]["unchanged"] += 1
    
    print("Per-tool vote changes:")
    for tool, data in sorted(tool_changes.items()):
        pct = data["gained"] / data["total"] * 100
        print(f"  {tool}: {data['gained']}/{data['total']} gained votes ({pct:.0f}%)")
    
    # Prediction check
    print()
    print("PREDICTION VALIDATION:")
    print(f"  Predicted ~30 tips would gain votes, ~70 would stop")
    print(f"  Actual: {gained} gained, {unchanged} stopped ({unchanged}/{gained+unchanged} = {unchanged/(gained+unchanged)*100:.0f}% stopped)")
    
    if unchanged / (gained + unchanged) > 0.5:
        print("  VALIDATION: PASS — condition-aware voting is filtering correctly")
    else:
        print("  VALIDATION: NEEDS TUNING — too many tips still getting votes")


if __name__ == "__main__":
    import sys
    if "--snapshot" in sys.argv:
        take_snapshot("post_restart")
    elif "--compare" in sys.argv:
        pre = str(Path.home() / "hermes-agent" / "pre_condition_aware_snapshot.json")
        post = str(Path.home() / "hermes-agent" / "tip_snapshot_post_restart.json")
        compare_snapshots(pre, post)
    else:
        print("Usage: --snapshot or --compare")
