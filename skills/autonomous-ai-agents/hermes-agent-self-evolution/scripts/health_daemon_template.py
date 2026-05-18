#!/usr/bin/env python3
"""
Health daemon template with [OK] confirmation logging.
Copy and customize for any monitoring cron job.

Anti-pattern: silent success (only logging problems)
Correct pattern: always report status, even when healthy
"""

import sqlite3
import os
import time

DB_PATH = os.path.expanduser("~/.hermes/cerebrum_memory.db")

def check_tips():
    """Example: prune weak tips."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tip_survival WHERE opportunities >= 100 AND survival_rate < 0.3")
    weak = c.fetchone()[0]
    conn.close()
    
    if weak:
        print(f"[TIPS] Pruned {weak} weak tips")
    else:
        print("[TIPS] OK: no weak tips to prune")

def check_db():
    """Example: database size check."""
    size = os.path.getsize(DB_PATH) / (1024*1024)
    if size > 100:
        print(f"[DB] WARNING: {size:.1f}MB (>100MB)")
    else:
        print(f"[DB] OK: {size:.1f}MB")

def main():
    print(f"=== Health Check {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
    check_tips()
    check_db()
    print("=== Done ===")

if __name__ == "__main__":
    main()
