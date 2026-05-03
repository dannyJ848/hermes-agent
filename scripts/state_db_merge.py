#!/usr/bin/env python3
"""
state_db_merge.py - Surgical merge of backup state.db into current
Only imports clean sessions (pre-corruption)
"""

import sqlite3
import sys
from datetime import datetime

BACKUP_DB = "/Users/dannygomez/Desktop/hermes_backup_20260423_000344/state.db"
CURRENT_DB = "/Users/dannygomez/.hermes/state.db"

# Corruption cutoff: sessions after this are potentially corrupted
# The corrupted sessions started at 20260422_224646 (unixepoch: 1776916016)
# BUT current DB already has all sessions, so we need to check for missing ones
CUTOFF_TIMESTAMP = 1776916016  # Exact timestamp of first corrupted session

def get_session_stats(conn):
    """Get session counts"""
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sessions")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages")
    msgs = c.fetchone()[0]
    return total, msgs

def merge_clean_sessions():
    print("=== STATE.DB SURGICAL MERGE ===")
    print(f"Backup: {BACKUP_DB}")
    print(f"Current: {CURRENT_DB}")
    print(f"Cutoff: {datetime.utcfromtimestamp(CUTOFF_TIMESTAMP)}")
    print()
    
    # Connect to both databases
    backup = sqlite3.connect(BACKUP_DB)
    current = sqlite3.connect(CURRENT_DB)
    
    backup_total, backup_msgs = get_session_stats(backup)
    current_total, current_msgs = get_session_stats(current)
    
    print(f"Backup: {backup_total} sessions, {backup_msgs} messages")
    print(f"Current: {current_total} sessions, {current_msgs} messages")
    print()
    
    # Find clean sessions in backup (before corruption)
    c = backup.cursor()
    c.execute("""
        SELECT id, title, source, model, started_at, message_count 
        FROM sessions 
        WHERE started_at < ?
        ORDER BY started_at DESC
    """, (CUTOFF_TIMESTAMP,))
    
    clean_sessions = c.fetchall()
    print(f"Found {len(clean_sessions)} clean sessions to merge")
    
    # Check which already exist in current
    c2 = current.cursor()
    merged = 0
    skipped = 0
    
    for sess in clean_sessions:
        sid, title, source, model, started, msg_count = sess
        
        # Check if already exists
        c2.execute("SELECT 1 FROM sessions WHERE id = ?", (sid,))
        if c2.fetchone():
            skipped += 1
            continue
        
        # Insert session
        c2.execute("""
            INSERT INTO sessions (id, title, source, model, started_at, message_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sid, title, source, model, started, msg_count))
        
        # Copy messages for this session
        c.execute("""
            SELECT session_id, role, content, tool_call_id, tool_calls, 
                   tool_name, timestamp, token_count, finish_reason, reasoning
            FROM messages WHERE session_id = ?
        """, (sid,))
        
        messages = c.fetchall()
        c2.executemany("""
            INSERT INTO messages (session_id, role, content, tool_call_id, tool_calls,
                                tool_name, timestamp, token_count, finish_reason, reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, messages)
        
        merged += 1
        
        if merged % 100 == 0:
            print(f"  Merged {merged} sessions...")
    
    current.commit()
    
    # Update FTS index
    print("\nRebuilding FTS index...")
    try:
        c2.execute("INSERT INTO messages_fts(messages_fts) VALUES('rebuild')")
        current.commit()
        print("FTS index rebuilt")
    except:
        print("FTS rebuild skipped (may not be needed)")
    
    # Final stats
    new_total, new_msgs = get_session_stats(current)
    print(f"\n=== MERGE COMPLETE ===")
    print(f"Merged: {merged} sessions")
    print(f"Skipped (already exist): {skipped}")
    print(f"Current DB now: {new_total} sessions, {new_msgs} messages")
    
    backup.close()
    current.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        print("DRY RUN MODE - No changes will be made")
        # Just show what would be merged
        backup = sqlite3.connect(BACKUP_DB)
        c = backup.cursor()
        c.execute("SELECT COUNT(*) FROM sessions WHERE started_at < ?", (CUTOFF_TIMESTAMP,))
        count = c.fetchone()[0]
        print(f"Would merge {count} clean sessions")
        backup.close()
    else:
        merge_clean_sessions()
