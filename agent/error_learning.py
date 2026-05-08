"""
Error Pattern Learning System — Kimi Harness v2.1

Tracks errors I make, categorizes them, and learns to avoid repeating them.
Uses the Cortex database to store error patterns and their resolutions.

Features:
- Error fingerprinting: Hash errors by type + context to detect repeats
- Resolution tracking: What fixed the error last time?
- Pre-emptive warnings: Alert before making a known mistake
- Success validation: Confirm the fix worked

Author: Kimi
Date: 2026-04-26
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _cortex_cursor():
    """Get a Cortex database cursor (backward-compatible wrapper).
    
    NOTE: This now uses local SQLite instead of PostgreSQL for the error
    learning store. The cerebrum_memory.db is local and fast.
    """
    # Use local SQLite for error patterns (fast, no network, no PostgreSQL needed)
    import sqlite3
    from pathlib import Path
    db_path = Path.home() / ".hermes" / "cerebrum_memory.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return _SQLiteCursorContext(conn)

class _SQLiteCursorContext:
    """Context manager that mimics the cortex_cursor() interface but uses SQLite."""
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
        self.cur.close()
        self.conn.close()
        return False  # Don't suppress exceptions


# ---------------------------------------------------------------------------
# Error fingerprinting
# ---------------------------------------------------------------------------

def fingerprint_error(error_text: str, context: str = "") -> str:
    """
    Create a stable fingerprint of an error.
    Normalizes variable content (paths, IDs, timestamps) to detect
    the same error pattern even with different specifics.
    """
    # Normalize the error text
    normalized = error_text.lower()
    
    # Replace variable content with placeholders
    normalized = re.sub(r'/[\w/.-]+', '<PATH>', normalized)
    normalized = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '<UUID>', normalized)
    normalized = re.sub(r'\d+\.\d+\.\d+\.\d+', '<IP>', normalized)
    normalized = re.sub(r'0x[0-9a-f]+', '<ADDR>', normalized)
    normalized = re.sub(r'\d{4}-\d{2}-\d{2}', '<DATE>', normalized)
    normalized = re.sub(r'\d{2}:\d{2}:\d{2}', '<TIME>', normalized)
    normalized = re.sub(r'proc_[a-z0-9]+', '<PROC>', normalized)
    normalized = re.sub(r'\d+', '<NUM>', normalized)
    
    # Include context hash
    context_hash = hashlib.md5(context[:200].encode()).hexdigest()[:8]
    
    # Create fingerprint
    fp = hashlib.md5(f"{normalized}:{context_hash}".encode()).hexdigest()[:16]
    return fp


# ---------------------------------------------------------------------------
# Error pattern storage
# ---------------------------------------------------------------------------

class ErrorPatternStore:
    """Stores and retrieves error patterns from Cortex."""
    
    def __init__(self):
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Ensure error patterns table exists (SQLite-compatible schema)."""
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
                    occurrence_count INTEGER DEFAULT 1,
                    last_occurred TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    first_occurred TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS error_occurrences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id INTEGER REFERENCES error_patterns(id) ON DELETE CASCADE,
                    session_id TEXT,
                    full_error TEXT,
                    resolution_attempted TEXT,
                    resolution_successful INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_error_patterns_fingerprint 
                ON error_patterns(fingerprint)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_error_occurrences_pattern 
                ON error_occurrences(pattern_id)
            """)
    
    def record_error(
        self,
        error_text: str,
        context: str = "",
        resolution: str = "",
        session_id: str = "",
        resolution_successful: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Record an error occurrence. If the pattern exists, update it.
        Returns the pattern info.
        """
        fingerprint = fingerprint_error(error_text, context)
        error_type = self._classify_error(error_text)
        error_summary = error_text[:200]
        
        with _cortex_cursor() as cur:
            # Check if pattern exists
            cur.execute(
                "SELECT id, occurrence_count, resolution_success_rate FROM error_patterns WHERE fingerprint = ?",
                (fingerprint,)
            )
            row = cur.fetchone()
            
            if row:
                # Existing pattern — update counts
                pattern_id = row[0]
                new_count = row[1] + 1
                
                # Update success rate if we have new data
                if resolution_successful is not None:
                    # Bayesian update
                    old_success = row[2] or 0.0
                    old_count = row[1]
                    if old_count > 0:
                        new_rate = (old_success * old_count + (1.0 if resolution_successful else 0.0)) / (old_count + 1)
                    else:
                        new_rate = 1.0 if resolution_successful else 0.0
                    
                    cur.execute("""
                        UPDATE error_patterns 
                        SET occurrence_count = ?,
                            last_occurred = CURRENT_TIMESTAMP,
                            resolution_success_rate = ?,
                            resolution = COALESCE(NULLIF(?, ''), resolution)
                        WHERE id = ?
                    """, (new_count, new_rate, resolution, pattern_id))
                else:
                    cur.execute("""
                        UPDATE error_patterns 
                        SET occurrence_count = ?,
                            last_occurred = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (new_count, pattern_id))
            else:
                # Create new pattern
                new_count = 1
                cur.execute("""
                    INSERT INTO error_patterns (
                        fingerprint, error_type, error_summary, context,
                        resolution, resolution_success_rate, occurrence_count
                    ) VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (fingerprint, error_type, error_summary, context[:500], 
                      resolution, 1.0 if resolution_successful else 0.0))
                pattern_id = cur.lastrowid
            
            # Record occurrence
            cur.execute("""
                INSERT INTO error_occurrences (
                    pattern_id, session_id, full_error, resolution_attempted, resolution_successful
                ) VALUES (?, ?, ?, ?, ?)
            """, (pattern_id, session_id, error_text[:2000], resolution, 
                  1 if resolution_successful else 0 if resolution_successful is not None else None))
            
            return {
                "pattern_id": str(pattern_id),
                "fingerprint": fingerprint,
                "error_type": error_type,
                "is_repeat": row is not None,
                "occurrence_count": new_count,
            }
    
    def _classify_error(self, error_text: str) -> str:
        """Classify error by type."""
        text = error_text.lower()
        
        if 'syntaxerror' in text or 'unexpected eof' in text:
            return 'syntax'
        elif 'importerror' in text or 'modulenotfound' in text:
            return 'import'
        elif 'connection' in text or 'timeout' in text or 'refused' in text:
            return 'network'
        elif 'permission' in text or 'access denied' in text:
            return 'permission'
        elif 'memory' in text or 'oom' in text or 'out of memory' in text:
            return 'memory'
        elif 'disk' in text or 'space' in text or 'no space' in text:
            return 'disk'
        elif 'undefined' in text or 'not found' in text or 'does not exist' in text:
            return 'not_found'
        elif 'assertion' in text or 'assert' in text:
            return 'assertion'
        elif 'keyerror' in text or 'indexerror' in text or 'typeerror' in text:
            return 'runtime'
        elif 'docker' in text or 'container' in text:
            return 'docker'
        elif 'ssh' in text or 'remote' in text:
            return 'remote'
        elif 'git' in text:
            return 'git'
        elif 'api' in text or '401' in text or '403' in text or '429' in text or '500' in text:
            return 'api'
        else:
            return 'unknown'
    
    def check_for_known_error(
        self,
        error_text: str,
        context: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        Check if this error has occurred before and has a known resolution.
        Returns pattern info if found, None otherwise.
        """
        fingerprint = fingerprint_error(error_text, context)
        
        with _cortex_cursor() as cur:
            cur.execute("""
                SELECT 
                    id, fingerprint, error_type, error_summary,
                    resolution, resolution_success_rate, occurrence_count,
                    last_occurred
                FROM error_patterns
                WHERE fingerprint = ?
            """, (fingerprint,))
            
            row = cur.fetchone()
            if not row:
                return None
            
            last_occurred = row[7]
            if last_occurred and hasattr(last_occurred, 'isoformat'):
                last_occurred = last_occurred.isoformat()
            elif last_occurred:
                last_occurred = str(last_occurred)
            
            return {
                "pattern_id": str(row[0]),
                "fingerprint": row[1],
                "error_type": row[2],
                "error_summary": row[3],
                "resolution": row[4],
                "resolution_success_rate": round(row[5] or 0, 3),
                "occurrence_count": row[6],
                "last_occurred": last_occurred,
                "is_known": True,
            }
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get statistics on error patterns."""
        with _cortex_cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_patterns,
                    SUM(CASE WHEN occurrence_count > 1 THEN 1 ELSE 0 END) as repeats,
                    AVG(resolution_success_rate) as avg_success_rate,
                    SUM(CASE WHEN resolution_success_rate > 0.8 THEN 1 ELSE 0 END) as well_solved
                FROM error_patterns
            """)
            
            row = cur.fetchone()
            
            cur.execute("""
                SELECT error_type, COUNT(*) as count
                FROM error_patterns
                GROUP BY error_type
                ORDER BY count DESC
            """)
            
            by_type = {r[0]: r[1] for r in cur.fetchall()}
            
            return {
                "total_patterns": row[0],
                "repeat_patterns": row[1],
                "average_success_rate": round(row[2] or 0, 3),
                "well_solved_count": row[3],
                "by_type": by_type,
            }
    
    def get_top_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequent error patterns."""
        with _cortex_cursor() as cur:
            cur.execute("""
                SELECT 
                    fingerprint, error_type, error_summary,
                    resolution, resolution_success_rate, occurrence_count
                FROM error_patterns
                ORDER BY occurrence_count DESC
                LIMIT ?
            """, (limit,))
            
            return [{
                "fingerprint": r[0],
                "error_type": r[1],
                "summary": r[2][:100],
                "resolution": r[3][:100] if r[3] else None,
                "success_rate": round(r[4] or 0, 3),
                "occurrences": r[5],
            } for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# Error learning engine
# ---------------------------------------------------------------------------

class ErrorLearningEngine:
    """High-level interface for error learning."""
    
    def __init__(self):
        self.store = ErrorPatternStore()
        self._batch_buffer: List[Dict] = []
        self._batch_size = 5  # Flush every 5 errors
        self._last_flush = time.time()
        self._flush_interval = 60  # Or every 60 seconds
    
    def _flush_batch(self):
        """Flush batched error writes to cortex."""
        if not self._batch_buffer:
            return
        
        try:
            with _cortex_cursor() as cur:
                for item in self._batch_buffer:
                    cur.execute("""
                        INSERT INTO error_occurrences (pattern_id, resolution_attempted, resolution_successful, context)
                        VALUES (?, ?, ?, ?)
                    """, (item['pattern_id'], item.get('resolution', ''), 
                          1 if item.get('successful', False) else 0, item.get('context', '')))
            self._batch_buffer.clear()
            self._last_flush = time.time()
        except Exception as e:
            logger.debug("Error batch flush failed: %s", e)
    
    def on_error(
        self,
        error_text: str,
        context: str = "",
        session_id: str = "",
    ) -> Dict[str, Any]:
        """
        Call this when an error occurs.
        Returns info about whether this is a known error and what the resolution was.
        """
        # Check if known
        known = self.store.check_for_known_error(error_text, context)
        
        if known and known.get('resolution'):
            logger.warning(
                "Known error detected (occurred %d times before). Last resolution: %s (success rate: %.1f%%)",
                known['occurrence_count'],
                known['resolution'][:100],
                known['resolution_success_rate'] * 100
            )
        
        # Record it (always sync for pattern table — small, fast)
        result = self.store.record_error(
            error_text=error_text,
            context=context,
            resolution=known.get('resolution', '') if known else '',
            session_id=session_id,
        )
        
        # Batch the occurrence write
        self._batch_buffer.append({
            'pattern_id': result['pattern_id'],
            'context': context,
            'session_id': session_id,
        })
        
        # Flush if batch full or interval elapsed
        if len(self._batch_buffer) >= self._batch_size or (time.time() - self._last_flush) > self._flush_interval:
            self._flush_batch()
        
        return {
            "is_known": known is not None,
            "known_info": known,
            "pattern_id": result['pattern_id'],
            "is_repeat": result['is_repeat'],
            "occurrence_count": result['occurrence_count'],
        }
    
    def on_resolution_attempt(
        self,
        pattern_id: str,
        resolution: str,
        successful: bool,
    ):
        """Call this after attempting to fix an error."""
        with _cortex_cursor() as cur:
            cur.execute("""
                UPDATE error_patterns
                SET resolution = ?,
                    resolution_success_rate = (
                        (resolution_success_rate * occurrence_count + ?) / (occurrence_count + 1)
                    ),
                    occurrence_count = occurrence_count + 1
                WHERE id = ?
            """, (resolution, 1.0 if successful else 0.0, pattern_id))
            
            cur.execute("""
                INSERT INTO error_occurrences (
                    pattern_id, resolution_attempted, resolution_successful
                ) VALUES (?, ?, ?)
            """, (pattern_id, resolution, 1 if successful else 0))
    
    def get_preemptive_warning(
        self,
        action_description: str,
    ) -> Optional[str]:
        """
        Check if a planned action has caused errors before.
        Returns a warning message if relevant.
        """
        # Search for similar errors
        with _cortex_cursor() as cur:
            cur.execute("""
                SELECT error_summary, resolution, occurrence_count, resolution_success_rate
                FROM error_patterns
                WHERE context LIKE ? AND occurrence_count > 1
                ORDER BY occurrence_count DESC
                LIMIT 3
            """, (f"%{action_description[:50]}%",))
            
            rows = cur.fetchall()
            if not rows:
                return None
            
            warnings = []
            for row in rows:
                if row[3] and row[3] > 0.5:
                    warnings.append(
                        f"- This action has caused errors {row[2]} times before. "
                        f"Known fix: {row[1][:80]}"
                    )
                else:
                    warnings.append(
                        f"- This action has caused errors {row[2]} times before. "
                        f"No reliable fix known yet."
                    )
            
            return "⚠️ PREEMPTIVE WARNING:\n" + "\n".join(warnings)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_error_engine: Optional[ErrorLearningEngine] = None

def get_error_engine() -> ErrorLearningEngine:
    global _error_engine
    if _error_engine is None:
        _error_engine = ErrorLearningEngine()
    return _error_engine
