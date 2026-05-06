#!/usr/bin/env python3
# Instant Context Viewer
# Shows everything a new CLI needs to know

import sqlite3
import json
from datetime import datetime

def show_context():
    conn = sqlite3.connect('/Users/dannygomez/.hermes/unified_context.db')
    c = conn.cursor()
    
    print("=" * 70)
    print("HERMES INSTANT CONTEXT — " + datetime.now().isoformat())
    print("=" * 70)
    
    # Critical info first
    print("\n[CRITICAL]")
    c.execute('''
        SELECT key, value FROM cli_context
        WHERE priority = 1
        ORDER BY category, key
    ''')
    for row in c.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # Tool intelligence
    print("\n[TOOL INTELLIGENCE — ROUTE AROUND WEAK]")
    c.execute('''
        SELECT tool_name, success_rate, total_calls, circuit_state, recommendation
        FROM tool_intelligence_snapshot
        ORDER BY success_rate DESC
    ''')
    for row in c.fetchall():
        state = "✓" if row[3] == 'CLOSED' else "✗ AVOID"
        print(f"  {state} {row[0]}: {row[1]*100:.0f}% ({row[2]} calls) — {row[4]}")
    
    # Recent errors
    print("\n[RECENT ERRORS — LEARN FROM]")
    c.execute('''
        SELECT tool_name, signature, fix, occurrences
        FROM error_registry
        ORDER BY last_seen DESC
        LIMIT 5
    ''')
    for row in c.fetchall():
        print(f"  ! {row[0]}: {row[1][:60]}...")
        print(f"    → {row[2]}")
    
    # Active session
    print("\n[ACTIVE SESSION]")
    c.execute('''
        SELECT session_id, active_tasks, decisions_made, files_modified
        FROM session_continuity
        WHERE status = 'active'
        ORDER BY last_activity DESC
        LIMIT 1
    ''')
    row = c.fetchone()
    if row:
        print(f"  Session: {row[0]}")
        tasks = json.loads(row[1]) if row[1] else []
        print(f"  Tasks: {', '.join(tasks)}")
        decisions = json.loads(row[2]) if row[2] else []
        for d in decisions:
            print(f"  → {d}")
    
    print("\n" + "=" * 70)
    print("To update: python3 hermes_cli/context_updater.py")
    print("=" * 70)

if __name__ == '__main__':
    show_context()
