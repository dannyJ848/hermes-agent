#!/usr/bin/env python3
"""save_finding — Save a finding to the knowledge base.

Usage:
  python3 save_finding.py <source> <topic> <raw_text_file>
  echo '{"source":"X","topic":"AI","raw_text":"..."}' | python3 save_finding.py --stdin
"""

import sqlite3
import sys
import json
import time
from pathlib import Path

DB_PATH = str(Path.home() / "hermes-agent" / "knowledge_compiler.db")

def save_finding(source: str, topic: str, raw_text: str, status: str = "saved"):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS raw_findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            topic TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            rules_extracted INTEGER DEFAULT 0,
            created_at REAL NOT NULL
        );
    """)
    conn.commit()
    conn.execute(
        "INSERT INTO raw_findings (source, topic, raw_text, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (source, topic, raw_text, status, time.time())
    )
    conn.commit()
    conn.close()
    print(f"[save_finding] Saved: {topic}")

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        save_finding(sys.argv[1], sys.argv[2], sys.argv[3])
    elif "--stdin" in sys.argv:
        data = json.load(sys.stdin)
        save_finding(data.get("source", "unknown"), data.get("topic", "general"), json.dumps(data))
    else:
        print("Usage: save_finding.py <source> <topic> '<raw_text>'")
        sys.exit(1)
