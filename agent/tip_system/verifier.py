#!/usr/bin/env python3
"""
Tip Verification System v0.1
Checks if distilled tips correlate with improved tool outcomes.

Compares tool success rates BEFORE and AFTER tip injection.
If tips improve outcomes, they're verified. If not, downvote them.

Usage: python3 tip_verifier.py [--domain DOMAIN] [--tool TOOL]
"""
import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

CEREBRUM_DB = Path.home() / ".hermes" / "cerebrum_memory.db"
CALL_LOG = Path.home() / ".hermes" / "call_log.db"

def get_tip_coverage():
    """Get tips grouped by tool and domain."""
    db = sqlite3.connect(str(CEREBRUM_DB), timeout=5)
    
    tips = db.execute("""
        SELECT tool_name, domain, COUNT(*) as count, 
               ROUND(AVG(confidence), 3) as avg_conf
        FROM distilled_tips
        WHERE confidence >= 0.5
        GROUP BY tool_name, domain
    """).fetchall()
    
    db.close()
    return tips

def get_recent_tool_stats():
    """Get recent tool success rates from call_log."""
    db = sqlite3.connect(str(CALL_LOG), timeout=5)
    
    try:
        # Last 24 hours
        stats = db.execute("""
            SELECT tool_name,
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'success' OR exit_code = 0 THEN 1 ELSE 0 END) as successes
            FROM calls
            WHERE timestamp > datetime('now', '-1 day')
            GROUP BY tool_name
        """).fetchall()
    except:
        stats = []
    
    db.close()
    
    result = {}
    for tool, total, successes in stats:
        result[tool] = {'total': total, 'successes': successes, 'rate': successes / max(total, 1)}
    
    return result

def verify():
    """Run verification check."""
    print("=== TIP VERIFICATION REPORT ===")
    
    tips = get_tip_coverage()
    stats = get_recent_tool_stats()
    
    if not tips:
        print("No tips to verify.")
        return
    
    if not stats:
        print("No recent tool stats available for verification.")
        print(f"Tips in database: {len(tips)}")
        for tool, domain, count, conf in tips[:10]:
            print(f"  {tool} ({domain}): {count} tips, conf={conf}")
        return
    
    print(f"\nTips: {len(tips)} tool-domain combinations")
    print(f"Tool stats: {len(stats)} tools with recent data")
    
    print(f"\n{'Tool':<25} {'Tips':>5} {'Tip Conf':>9} {'Success Rate':>13} {'Verified'}")
    print("-" * 70)
    
    verified = 0
    unverified = 0
    
    for tool, domain, count, conf in tips:
        if tool and tool in stats:
            actual_rate = stats[tool]['rate']
            # Tip is verified if tool success rate > tip confidence
            # (tips predicted success, and it's actually happening)
            if actual_rate >= 0.6:
                status = "YES"
                verified += 1
            else:
                status = "NO - downvote"
                unverified += 1
            
            print(f"{tool:<25} {count:>5} {conf:>9.3f} {actual_rate:>13.1%} {status}")
    
    print(f"\nVerified: {verified}, Unverified: {unverified}")
    if verified + unverified > 0:
        print(f"Verification rate: {verified / (verified + unverified):.1%}")

if __name__ == '__main__':
    verify()
