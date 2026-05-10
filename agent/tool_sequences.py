"""
R213b — Tool Sequence Frequency Tracker
Inspired by AWO (2601.22037): track recurring tool call sequences to identify
candidates for meta-tools (composite operations that bypass intermediate LLM steps).
"""
import sqlite3, json, time
from pathlib import Path
from collections import Counter

DB_PATH = str(Path.home() / "hermes-agent" / "tool_sequences.db")

MIN_SEQUENCE_LEN = 2
MAX_SEQUENCE_LEN = 4
FREQUENCY_THRESHOLD = 5  # Sequences appearing this often are meta-tool candidates


def _get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _ensure_schema():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS call_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            success INTEGER DEFAULT 1,
            timestamp REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sequence_counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sequence TEXT NOT NULL,
            sequence_hash TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            avg_success_rate REAL DEFAULT 1.0,
            meta_tool_candidate INTEGER DEFAULT 0,
            last_seen REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS meta_tool_candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sequence TEXT NOT NULL,
            frequency INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 1.0,
            suggested_name TEXT DEFAULT '',
            status TEXT DEFAULT 'discovered',
            discovered_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_call_log_session ON call_log(session_id);
        CREATE INDEX IF NOT EXISTS idx_sequence_hash ON sequence_counts(sequence_hash);
    """)
    conn.commit()
    conn.close()


def record_call(session_id, tool_name, success=True):
    """Record a tool call and check for recurring sequences."""
    _ensure_schema()
    conn = _get_conn()
    
    conn.execute(
        "INSERT INTO call_log (session_id, tool_name, success, timestamp) "
        "VALUES (?, ?, ?, ?)",
        (session_id, tool_name, 1 if success else 0, time.time())
    )
    
    # Get recent calls in this session
    recent = conn.execute(
        "SELECT tool_name, success FROM call_log WHERE session_id = ? "
        "ORDER BY timestamp DESC LIMIT ?",
        (session_id, MAX_SEQUENCE_LEN)
    ).fetchall()
    recent = list(reversed(recent))  # Chronological order
    
    # Extract and count sequences of length 2-4
    for length in range(MIN_SEQUENCE_LEN, min(MAX_SEQUENCE_LEN + 1, len(recent) + 1)):
        seq = tuple(r[0] for r in recent[-length:])
        seq_str = " → ".join(seq)
        import hashlib
        seq_hash = hashlib.md5(seq_str.encode()).hexdigest()[:16]
        
        existing = conn.execute(
            "SELECT id, count, avg_success_rate FROM sequence_counts "
            "WHERE sequence_hash = ?", (seq_hash,)
        ).fetchone()
        
        if existing:
            eid, count, avg_sr = existing
            new_count = count + 1
            new_sr = (avg_sr * count + (1.0 if success else 0.0)) / new_count
            
            is_candidate = new_count >= FREQUENCY_THRESHOLD
            
            conn.execute(
                "UPDATE sequence_counts SET count=?, avg_success_rate=?, "
                "meta_tool_candidate=?, last_seen=? WHERE id=?",
                (new_count, round(new_sr, 3), 1 if is_candidate else 0, time.time(), eid)
            )
            
            if is_candidate and existing[1] < FREQUENCY_THRESHOLD:
                # Newly discovered meta-tool candidate
                suggested_name = "_".join(seq) + "_macro"
                conn.execute(
                    "INSERT OR IGNORE INTO meta_tool_candidates "
                    "(sequence, frequency, success_rate, suggested_name, status, discovered_at) "
                    "VALUES (?,?,?,?,?,?)",
                    (seq_str, new_count, round(new_sr, 3), suggested_name, "discovered", time.time())
                )
        else:
            conn.execute(
                "INSERT INTO sequence_counts (sequence, sequence_hash, count, "
                "avg_success_rate, meta_tool_candidate, last_seen) VALUES (?,?,?,?,?,?)",
                (seq_str, seq_hash, 1, 1.0 if success else 0.0, 0, time.time())
            )
    
    conn.commit()
    conn.close()
    return {"recorded": True}


def get_meta_tool_candidates():
    """Get sequences that qualify as meta-tool candidates."""
    _ensure_schema()
    conn = _get_conn()
    rows = conn.execute(
        "SELECT sequence, frequency, success_rate, suggested_name, status "
        "FROM meta_tool_candidates ORDER BY frequency DESC"
    ).fetchall()
    conn.close()
    return [{
        "sequence": r[0],
        "frequency": r[1],
        "success_rate": r[2],
        "suggested_name": r[3],
        "status": r[4]
    } for r in rows]


def get_top_sequences(limit=10):
    """Get most frequent tool sequences."""
    _ensure_schema()
    conn = _get_conn()
    rows = conn.execute(
        "SELECT sequence, count, avg_success_rate FROM sequence_counts "
        "ORDER BY count DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [{
        "sequence": r[0],
        "count": r[1],
        "success_rate": r[2]
    } for r in rows]


def get_stats():
    _ensure_schema()
    conn = _get_conn()
    total_calls = conn.execute("SELECT COUNT(*) FROM call_log").fetchone()[0]
    unique_sequences = conn.execute("SELECT COUNT(*) FROM sequence_counts").fetchone()[0]
    candidates = conn.execute("SELECT COUNT(*) FROM meta_tool_candidates").fetchone()[0]
    top_seq = conn.execute(
        "SELECT sequence, count FROM sequence_counts ORDER BY count DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return {
        "total_calls": total_calls,
        "unique_sequences": unique_sequences,
        "meta_tool_candidates": candidates,
        "top_sequence": {"seq": top_seq[0], "count": top_seq[1]} if top_seq else None
    }


if __name__ == "__main__":
    _ensure_schema()
    sid = "test-session"
    
    # Simulate recurring code edit workflow
    for _ in range(6):
        record_call(sid, "read_file", True)
        record_call(sid, "search_files", True)
        record_call(sid, "patch", True)
    
    # Simulate research workflow
    for _ in range(3):
        record_call(sid, "web_research", True)
        record_call(sid, "web_extract", True)
    
    print(f"Top sequences: {get_top_sequences()}")
    print(f"Meta-tool candidates: {get_meta_tool_candidates()}")
    print(f"Stats: {get_stats()}")
