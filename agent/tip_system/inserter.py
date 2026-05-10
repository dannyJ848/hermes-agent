#!/usr/bin/env python3
"""Background tip inserter daemon — handles DB lock contention gracefully.

Watches a queue directory for tip insertion requests and processes them
when the DB is available. Eliminates the need to kill the gateway for
every tip insertion.
"""

import sqlite3, json, time, os, sys, hashlib
from pathlib import Path
from datetime import datetime

QUEUE_DIR = str(Path.home() / ".hermes" / "tip_queue")
DB_PATH = str(Path.home() / ".hermes" / "cerebrum_memory.db")
POLL_INTERVAL = 5  # seconds
MAX_RETRIES = 60
LOCK_TIMEOUT = 120

def _ensure_queue_dir():
    os.makedirs(QUEUE_DIR, exist_ok=True)

def enqueue_tips(tips: list, round_label: str = ""):
    """Write tips to a queue file for background insertion."""
    _ensure_queue_dir()
    ts = int(time.time() * 1000)
    fname = f"tips_{round_label or 'misc'}_{ts}.json"
    path = os.path.join(QUEUE_DIR, fname)
    with open(path, "w") as f:
        json.dump({"tips": tips, "round": round_label, "enqueued_at": time.time()}, f)
    return fname

def process_queue():
    """Process all pending tip files in the queue."""
    _ensure_queue_dir()
    files = sorted([f for f in os.listdir(QUEUE_DIR) if f.endswith(".json")])
    if not files:
        return {"processed": 0, "inserted": 0, "remaining": 0}
    
    total_inserted = 0
    processed = 0
    
    try:
        db = sqlite3.connect(DB_PATH, timeout=LOCK_TIMEOUT)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute(f"PRAGMA busy_timeout={LOCK_TIMEOUT * 1000}")
        now = time.time()
        
        for fname in files:
            fpath = os.path.join(QUEUE_DIR, fname)
            try:
                with open(fpath) as f:
                    data = json.load(f)
                
                tips = data.get("tips", [])
                n = 0
                for t in tips:
                    try:
                        db.execute(
                            "INSERT OR IGNORE INTO distilled_tips "
                            "(tip_type,condition,recommendation,rationale,tool_name,"
                            "domain,confidence,upvotes,downvotes,frequency,"
                            "created_at,last_seen,source_ids) "
                            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (t[0], t[1], t[2], t[3], t[4], t[5], t[6],
                             0, 0, 1, now, now,
                             json.dumps({"round": data.get("round", "unknown")}))
                        )
                        n += 1
                    except Exception:
                        pass
                
                db.commit()
                total_inserted += n
                processed += 1
                os.remove(fpath)  # Clean up processed file
                
            except Exception as e:
                print(f"Error processing {fname}: {e}")
        
        db.close()
    except Exception as e:
        print(f"DB connection error: {e}")
        return {"processed": 0, "inserted": 0, "remaining": len(files), "error": str(e)}
    
    remaining = len([f for f in os.listdir(QUEUE_DIR) if f.endswith(".json")])
    return {"processed": processed, "inserted": total_inserted, "remaining": remaining}

def run_daemon():
    """Run as a continuous daemon processing the queue."""
    print(f"Tip inserter daemon started. Watching {QUEUE_DIR}")
    while True:
        result = process_queue()
        if result["processed"] > 0:
            p = result.get("processed", 0)
            i = result.get("inserted", 0)
            r = result.get("remaining", 0)
            ts = datetime.now().isoformat()
            print(f"[{ts}] Processed {p} files, inserted {i} tips, {r} remaining")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        run_daemon()
    else:
        result = process_queue()
        print(json.dumps(result, indent=2))
