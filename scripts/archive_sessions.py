#!/usr/bin/env python3
"""
Hermes Session Archiver

Archives old sessions from state.db to Cortex documents.
Runs as a cron job or can be called manually.

Strategy:
- Sessions older than N days get their messages archived to cortex_documents
- After archiving, messages are deleted from state.db
- Sessions table keeps metadata (title, dates, counts) for search
"""

import sqlite3
import psycopg2
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Config
STATE_DB = Path.home() / ".hermes/state.db"
CORTEX_DB = "dbname=cortex user=hindsight host=localhost port=5432"
ARCHIVE_DAYS = 7  # Archive sessions older than this
BATCH_SIZE = 1000  # Messages per batch


def get_db_size(path: Path) -> int:
    """Get SQLite DB size in bytes."""
    return path.stat().st_size if path.exists() else 0


def archive_sessions():
    """Archive old sessions to Cortex."""
    if not STATE_DB.exists():
        print(f"State DB not found: {STATE_DB}")
        return 0, 0
    
    # Connect to state.db
    state_conn = sqlite3.connect(str(STATE_DB))
    state_cursor = state_conn.cursor()
    
    # Connect to Cortex
    cortex_conn = psycopg2.connect(CORTEX_DB)
    cortex_cursor = cortex_conn.cursor()
    
    # Find sessions to archive (older than ARCHIVE_DAYS, completed)
    cutoff = datetime.now() - timedelta(days=ARCHIVE_DAYS)
    cutoff_ts = cutoff.timestamp()
    
    state_cursor.execute("""
        SELECT id, source, started_at, ended_at, message_count, title
        FROM sessions
        WHERE started_at < ? AND (ended_at IS NOT NULL OR end_reason IS NOT NULL)
        ORDER BY started_at
    """, (cutoff_ts,))
    
    sessions = state_cursor.fetchall()
    print(f"Found {len(sessions)} sessions to archive (older than {ARCHIVE_DAYS} days)")
    
    archived_count = 0
    deleted_messages = 0
    
    for session in sessions:
        session_id, source, started_at, ended_at, msg_count, title = session
        
        # Skip cron/test sessions with 0-1 messages
        if msg_count <= 1:
            continue
        
        # Get messages for this session
        state_cursor.execute("""
            SELECT role, content, timestamp, tool_name, tool_calls
            FROM messages
            WHERE session_id = ?
            ORDER BY timestamp
        """, (session_id,))
        
        messages = state_cursor.fetchall()
        
        # Build conversation text
        conversation_lines = []
        for msg in messages:
            role, content, timestamp, tool_name, tool_calls = msg
            ts = datetime.fromtimestamp(timestamp).isoformat() if timestamp else ""
            prefix = f"[{ts}] {role.upper()}"
            if tool_name:
                prefix += f" (tool: {tool_name})"
            conversation_lines.append(f"{prefix}: {content or ''}")
        
        conversation_text = "\n\n".join(conversation_lines)
        
        # Archive to Cortex
        tags = ["session_archive", source or "unknown"]
        if msg_count > 100:
            tags.append("long-session")
        
        cortex_cursor.execute("""
            INSERT INTO cortex_documents (
                id, original_text, content_hash, doc_type, domain, 
                source_url, metadata, tags, created_at, updated_at
            ) VALUES (
                gen_random_uuid(),
                %s,
                md5(%s)::text,
                'session_archive',
                'hermes-session',
                '',
                jsonb_build_object(
                    'session_id', %s,
                    'source', %s,
                    'started_at', %s,
                    'ended_at', %s,
                    'message_count', %s,
                    'title', %s,
                    'archived_at', %s
                ),
                %s,
                to_timestamp(%s),
                NOW()
            )
        """, (
            conversation_text, conversation_text,
            session_id, source, started_at, ended_at, msg_count, title,
            datetime.now().isoformat(), tags, started_at or datetime.now().timestamp()
        ))
        
        # Delete messages for this session
        state_cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        deleted_messages += state_cursor.rowcount
        
        archived_count += 1
        
        if archived_count % 10 == 0:
            print(f"  Archived {archived_count} sessions, {deleted_messages} messages...")
            cortex_conn.commit()
            state_conn.commit()
    
    # Final commit
    cortex_conn.commit()
    state_conn.commit()
    
    # Vacuum state.db to reclaim space
    state_cursor.execute("VACUUM")
    state_conn.commit()
    
    # Get new size
    new_size = get_db_size(STATE_DB)
    
    state_conn.close()
    cortex_conn.close()
    
    print(f"\nDone! Archived {archived_count} sessions ({deleted_messages} messages)")
    print(f"State DB size: {new_size / 1024 / 1024:.1f} MB")
    
    return archived_count, deleted_messages


def main():
    print(f"Hermes Session Archiver — {datetime.now().isoformat()}")
    print(f"Archive threshold: {ARCHIVE_DAYS} days")
    print(f"State DB: {STATE_DB} ({get_db_size(STATE_DB) / 1024 / 1024:.1f} MB)")
    print()
    
    archived, deleted = archive_sessions()
    
    if archived == 0:
        print("No sessions needed archiving.")
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
