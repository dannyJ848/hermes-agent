#!/usr/bin/env python3
"""Tip Decay Monitor — snapshot tip confidences to track FadeMem over time.

Usage:
  python3 tip_decay_monitor.py snap    — take a snapshot
  python3 tip_decay_monitor.py diff    — compare latest two snapshots
  python3 tip_decay_monitor.py history — show all snapshots
"""
import sqlite3
import json
import sys
import time
from pathlib import Path

CEREBRUM = Path.home() / ".hermes" / "cerebrum_memory.db"
SNAP_DB = Path.home() / ".hermes" / "tip_decay_snapshots.db"


def ensure_snap_db():
    SNAP_DB.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(SNAP_DB), timeout=5)
    db.execute("""CREATE TABLE IF NOT EXISTS snapshots (
        snap_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp REAL,
        total_tips INTEGER,
        avg_confidence REAL,
        snapshot_data TEXT
    )""")
    db.commit()
    db.close()


def snap():
    ensure_snap_db()
    cer = sqlite3.connect(str(CEREBRUM), timeout=5)
    tips = cer.execute(
        "SELECT id, tool_name, confidence, upvotes, downvotes, frequency FROM distilled_tips"
    ).fetchall()
    cer.close()
    
    avg_conf = sum(t[2] for t in tips) / len(tips) if tips else 0
    snap_data = json.dumps([
        {"id": t[0], "tool": t[1], "conf": round(t[2], 4), 
         "up": t[3], "down": t[4], "freq": t[5]}
        for t in tips
    ])
    
    sdb = sqlite3.connect(str(SNAP_DB), timeout=5)
    sdb.execute(
        "INSERT INTO snapshots (timestamp, total_tips, avg_confidence, snapshot_data) VALUES (?,?,?,?)",
        (time.time(), len(tips), avg_conf, snap_data)
    )
    sdb.commit()
    sdb.close()
    print(f"Snapshot taken: {len(tips)} tips, avg confidence {avg_conf:.4f}")


def diff():
    ensure_snap_db()
    sdb = sqlite3.connect(str(SNAP_DB), timeout=5)
    rows = sdb.execute(
        "SELECT snap_id, timestamp, total_tips, avg_confidence, snapshot_data "
        "FROM snapshots ORDER BY snap_id DESC LIMIT 2"
    ).fetchall()
    sdb.close()
    
    if len(rows) < 2:
        print("Need at least 2 snapshots to diff. Run 'snap' twice.")
        return
    
    newer = json.loads(rows[0][4])
    older = json.loads(rows[1][4])
    
    older_map = {t["id"]: t for t in older}
    
    print(f"Diff: snap #{rows[1][0]} → #{rows[0][0]}")
    print(f"{'ID':>4} {'TOOL':<18} {'OLD':>7} {'NEW':>7} {'DELTA':>8} {'DIR':>4}")
    print("-" * 55)
    
    grew = shrunk = same = 0
    for t in newer:
        old_t = older_map.get(t["id"])
        if old_t:
            delta = t["conf"] - old_t["conf"]
            if delta > 0.001:
                dir_str = "↑"
                grew += 1
            elif delta < -0.001:
                dir_str = "↓"
                shrunk += 1
            else:
                dir_str = "="
                same += 1
            if abs(delta) > 0.001:
                print(f"{t['id']:>4} {t['tool']:<18} {old_t['conf']:>7.4f} {t['conf']:>7.4f} {delta:>+8.4f} {dir_str}")
    
    print(f"\nGrew: {grew}, Shrunk: {shrunk}, Same: {same}")
    avg_delta = rows[0][3] - rows[1][3]
    print(f"Avg confidence change: {avg_delta:+.4f}")


def history():
    ensure_snap_db()
    sdb = sqlite3.connect(str(SNAP_DB), timeout=5)
    rows = sdb.execute(
        "SELECT snap_id, datetime(timestamp, 'unixepoch', 'localtime'), total_tips, avg_confidence "
        "FROM snapshots ORDER BY snap_id"
    ).fetchall()
    sdb.close()
    
    print(f"{'ID':>4} {'TIME':<22} {'TIPS':>6} {'AVG CONF':>10}")
    print("-" * 45)
    for sid, ts, total, avg in rows:
        print(f"{sid:>4} {ts:<22} {total:>6} {avg:>10.4f}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("snap", "diff", "history"):
        print("Usage: python3 tip_decay_monitor.py [snap|diff|history]")
        sys.exit(1)
    {"snap": snap, "diff": diff, "history": history}[sys.argv[1]]()
