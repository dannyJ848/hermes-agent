"""error_learning — cognitive subsystem for pattern extraction from failures.

SQLite backend using cerebrum_memory.db.
Uses ? placeholders, INTEGER PRIMARY KEY AUTOINCREMENT, CURRENT_TIMESTAMP.
"""

import hashlib
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"


class _SQLiteCursorContext:
    """Context manager for SQLite connections."""
    def __init__(self, conn):
        self.conn = conn
        self.cur = None

    def __enter__(self):
        self.cur = self.conn.cursor()
        return self.cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        if self.cur is not None:
            try:
                self.cur.close()
            except Exception:
                pass
        # Connection is pooled (agent.db_pool) — not closed here. Closing
        # would reintroduce the per-query connect/close cost.
        return False


def _cortex_cursor():
    """SQLite backend — uses ? placeholders, CURRENT_TIMESTAMP, INTEGER PRIMARY KEY AUTOINCREMENT."""
    from agent.db_pool import get_connection
    conn = get_connection(DB_PATH)
    return _SQLiteCursorContext(conn)


def _fingerprint(error_text: str) -> str:
    """Create a stable fingerprint from error text."""
    # Normalize: lowercase, strip line numbers, take first 200 chars
    normalized = error_text.lower()
    # Remove line numbers like "line 42" or "file.py:123"
    import re
    normalized = re.sub(r'\bline\s+\d+\b', 'line N', normalized)
    normalized = re.sub(r'\b\w+\.py:\d+\b', 'file.py:N', normalized)
    normalized = re.sub(r'0x[0-9a-f]+', '0xADDR', normalized)
    normalized = normalized[:200]
    return hashlib.sha256(normalized.encode()).hexdigest()[:32]


class ErrorLearningStore:
    """Database operations for error patterns and occurrences."""
    
    def __init__(self):
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Idempotent schema creation."""
        with _cortex_cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS error_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fingerprint TEXT UNIQUE NOT NULL,
                    error_type TEXT,
                    error_summary TEXT,
                    context TEXT,
                    resolution TEXT,
                    resolution_success_rate REAL DEFAULT 0.0,
                    occurrence_count INTEGER DEFAULT 0,
                    last_occurred TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    first_occurred TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS error_occurrences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id INTEGER NOT NULL,
                    session_id TEXT,
                    full_error TEXT,
                    resolution_attempted TEXT,
                    resolution_successful INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pattern_id) REFERENCES error_patterns(id)
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_err_fp ON error_patterns(fingerprint)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_err_occ_time ON error_occurrences(timestamp)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_err_occ_pattern ON error_occurrences(pattern_id)")
    
    def record_error(self, error_text: str, context: str = None, session_id: str = None) -> Dict[str, Any]:
        """Record an error. Returns pattern info including is_repeat and occurrence_count."""
        fp = _fingerprint(error_text)
        error_type = _classify_error(error_text)
        error_summary = error_text[:500] if error_text else ""
        
        with _cortex_cursor() as cur:
            # Check if pattern exists
            cur.execute("SELECT id, occurrence_count, resolution_success_rate FROM error_patterns WHERE fingerprint = ?", (fp,))
            row = cur.fetchone()
            
            if row:
                pattern_id = row["id"]
                occurrence_count = row["occurrence_count"] + 1
                is_repeat = True
                
                cur.execute("""
                    UPDATE error_patterns 
                    SET occurrence_count = ?, last_occurred = CURRENT_TIMESTAMP, error_summary = ?
                    WHERE id = ?
                """, (occurrence_count, error_summary, pattern_id))
            else:
                cur.execute("""
                    INSERT INTO error_patterns (fingerprint, error_type, error_summary, context, occurrence_count)
                    VALUES (?, ?, ?, ?, 1)
                """, (fp, error_type, error_summary, context or "",))
                pattern_id = cur.lastrowid
                occurrence_count = 1
                is_repeat = False
            
            # Record occurrence
            cur.execute("""
                INSERT INTO error_occurrences (pattern_id, session_id, full_error, resolution_successful)
                VALUES (?, ?, ?, 0)
            """, (pattern_id, session_id or "", error_text[:2000]))
            occurrence_id = cur.lastrowid
            
            return {
                "pattern_id": pattern_id,
                "occurrence_id": occurrence_id,
                "fingerprint": fp,
                "is_repeat": is_repeat,
                "occurrence_count": occurrence_count,
                "error_type": error_type,
            }
    
    def record_resolution(self, pattern_id: int, resolution: str, successful: bool = True) -> bool:
        """Record a resolution attempt for an error pattern."""
        with _cortex_cursor() as cur:
            cur.execute("""
                UPDATE error_patterns 
                SET resolution = ?, resolution_success_rate = ?
                WHERE id = ?
            """, (resolution, 1.0 if successful else 0.0, pattern_id))
            
            # Update the most recent occurrence
            cur.execute("""
                UPDATE error_occurrences 
                SET resolution_attempted = ?, resolution_successful = ?
                WHERE pattern_id = ? AND resolution_attempted IS NULL
                ORDER BY timestamp DESC LIMIT 1
            """, (resolution, 1 if successful else 0, pattern_id))
            
            return cur.rowcount > 0
    
    def get_preemptive_warning(self, action_description: str) -> Optional[str]:
        """Get a warning for an action based on past errors with similar context."""
        with _cortex_cursor() as cur:
            # Search for patterns with similar context
            words = action_description.lower().split()
            if not words:
                return None
            
            # Build a LIKE query for any word match
            like_clauses = " OR ".join(["context LIKE ?" for _ in words])
            params = [f"%{w}%" for w in words[:5]]  # Limit to 5 words
            
            cur.execute(f"""
                SELECT error_summary, occurrence_count, resolution, resolution_success_rate
                FROM error_patterns
                WHERE ({like_clauses}) AND occurrence_count >= 2
                ORDER BY occurrence_count DESC, resolution_success_rate ASC
                LIMIT 1
            """, params)
            
            row = cur.fetchone()
            if row and row["occurrence_count"] >= 2:
                msg = f"⚠️ Past error ({row['occurrence_count']}×): {row['error_summary'][:120]}"
                if row["resolution"]:
                    msg += f" | Fix: {row['resolution'][:120]}"
                return msg
            return None
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get statistics about recorded errors."""
        with _cortex_cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM error_patterns")
            total_patterns = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM error_occurrences")
            total_occurrences = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM error_patterns WHERE occurrence_count >= 3")
            frequent_patterns = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM error_patterns WHERE resolution_success_rate > 0")
            resolved_patterns = cur.fetchone()[0]
            
            return {
                "total_patterns": total_patterns,
                "total_occurrences": total_occurrences,
                "frequent_patterns": frequent_patterns,
                "resolved_patterns": resolved_patterns,
            }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent error occurrences."""
        with _cortex_cursor() as cur:
            cur.execute("""
                SELECT eo.*, ep.fingerprint, ep.error_type
                FROM error_occurrences eo
                JOIN error_patterns ep ON eo.pattern_id = ep.id
                ORDER BY eo.timestamp DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cur.fetchall()]


class ErrorLearningEngine:
    """Error learning engine for pattern extraction from failures."""
    
    def __init__(self):
        self.store = ErrorLearningStore()
        self._batch_buffer = []
        self._batch_size = 5
        self._flush_interval = 60
        self._last_flush = time.time()
    
    def on_error(self, error_text: str, context: str = None, session_id: str = None) -> Dict[str, Any]:
        """Record an error occurrence. Called from the agent loop on tool failure."""
        return self.store.record_error(error_text, context, session_id)
    
    def get_preemptive_warning(self, action_description: str) -> Optional[str]:
        """Get warning before executing an action."""
        return self.store.get_preemptive_warning(action_description)
    
    def learn_fix(self, error_pattern_id: int, fix: str, successful: bool = True) -> bool:
        """Learn a fix for an error pattern."""
        return self.store.record_resolution(error_pattern_id, fix, successful)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return self.store.get_error_stats()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify_error(error_text: str) -> str:
    """Classify an error into a type."""
    text = error_text.lower()
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "connection" in text or "connect" in text:
        return "connection"
    if "permission" in text or "access denied" in text or "unauthorized" in text:
        return "permission"
    if "not found" in text or "does not exist" in text or "no such file" in text:
        return "not_found"
    if "memory" in text or "oom" in text or "out of memory" in text:
        return "memory"
    if "syntax" in text or "parse" in text or "invalid" in text:
        return "syntax"
    if "import" in text or "module" in text or "no module" in text:
        return "import"
    if "api" in text or "rate limit" in text or "429" in text:
        return "api"
    if "json" in text or "decode" in text or "parse" in text:
        return "json"
    return "unknown"


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_error_engine = None

def get_error_engine() -> ErrorLearningEngine:
    """Get the singleton error learning engine."""
    global _error_engine
    if _error_engine is None:
        _error_engine = ErrorLearningEngine()
    return _error_engine
