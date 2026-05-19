#!/usr/bin/env python3
"""
Autobrowse pipeline health check — detects if the distillation plugin
has stopped capturing tool calls after the hook fix.

Checks BOTH databases:
- tool_intelligence.db (live capture from hooks)
- cerebrum_memory.db (old cortex sync path)

Usage: python3 scripts/stale-pipeline-check.py
"""
import sqlite3
import time
from pathlib import Path
from datetime import datetime

TIDB_PATH = Path.home() / ".hermes" / "tool_intelligence.db"
CDB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"

def check():
    now = time.time()
    warnings = []
    
    # ── tool_intelligence.db (LIVE capture) ──
    if TIDB_PATH.exists():
        tidb = sqlite3.connect(TIDB_PATH)
        c = tidb.cursor()
        
        c.execute("SELECT COUNT(*) FROM tool_calls WHERE timestamp > ?", (now - 86400,))
        live_calls_24h = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM tool_calls")
        live_calls_total = c.fetchone()[0]
        
        c.execute("SELECT tool_name, timestamp FROM tool_calls ORDER BY timestamp DESC LIMIT 3")
        recent_live = c.fetchall()
        
        tidb.close()
        
        print(f"=== LIVE CAPTURE (tool_intelligence.db) ===")
        print(f"  tool calls 24h:     {live_calls_24h}")
        print(f"  tool calls total:   {live_calls_total}")
        print(f"  latest calls:")
        for tool, ts in recent_live:
            print(f"    {tool}: {datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')}")
        
        if live_calls_24h == 0:
            warnings.append("LIVE CAPTURE STALE — no tool calls in 24h")
    else:
        print(f"=== LIVE CAPTURE (tool_intelligence.db) ===")
        print(f"  DATABASE NOT FOUND — pipeline may be completely dead")
        warnings.append("tool_intelligence.db missing")
    
    # ── cerebrum_memory.db (sync path) ──
    if CDB_PATH.exists():
        conn = sqlite3.connect(CDB_PATH)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM tool_call_log WHERE created_at > datetime('now', '-24 hours')")
        cerebrum_calls_24h = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM tool_call_log")
        cerebrum_calls_total = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM distilled_tips WHERE created_at > datetime('now', '-24 hours')")
        tips_24h = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM distilled_tips")
        tips_total = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM tip_elo")
        elo_entries = c.fetchone()[0]
        
        conn.close()
        
        print(f"\n=== CEREBRUM SYNC (cerebrum_memory.db) ===")
        print(f"  tool calls 24h:     {cerebrum_calls_24h}")
        print(f"  tool calls total:   {cerebrum_calls_total}")
        print(f"  new tips 24h:       {tips_24h}")
        print(f"  tips total:         {tips_total}")
        print(f"  elo entries:        {elo_entries}")
        
        if cerebrum_calls_24h == 0 and tips_24h == 0:
            warnings.append("Cerebrum sync stale — no activity in 24h (may be normal if live capture active)")
    else:
        print(f"\n=== CEREBRUM SYNC (cerebrum_memory.db) ===")
        print(f"  DATABASE NOT FOUND")
    
    # ── Summary ──
    print(f"\n=== VERDICT ===")
    if not warnings:
        print("[OK] Pipeline active — live capture working")
        return 0
    elif "LIVE CAPTURE STALE" in str(warnings):
        print("[FAIL] Pipeline dead — hook not firing")
        print("  → Re-run hook signature audit:")
        print("     grep -A 5 'invoke_hook.*post_tool_call' ~/.hermes/model_tools.py")
        print("  → Check plugin status:")
        print("     hermes plugins list | grep distillation")
        print("  → Verify hook signature has **kwargs:")
        print("     grep 'def _on_post_tool_call' ~/.hermes/plugins/distillation/__init__.py")
        return 1
    else:
        print(f"[WARNING] {warnings[0]}")
        return 1

if __name__ == "__main__":
    exit(check())
