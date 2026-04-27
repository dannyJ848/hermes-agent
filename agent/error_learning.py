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
    """Get a Cortex database cursor."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path.home() / "subconscious"))
    from cortex_access import cortex_cursor
    return cortex_cursor()


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
        """Ensure error patterns table exists."""
        with _cortex_cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS error_patterns (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    fingerprint TEXT UNIQUE NOT NULL,
                    error_type TEXT,
                    error_summary TEXT,
                    context TEXT,
                    resolution TEXT,
                    resolution_success_rate FLOAT DEFAULT 0.0,
                    occurrence_count INTEGER DEFAULT 1,
                    last_occurred TIMESTAMP DEFAULT NOW(),
                    first_occurred TIMESTAMP DEFAULT NOW(),
                    metadata JSONB DEFAULT '{}'::jsonb
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS error_occurrences (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    pattern_id UUID REFERENCES error_patterns(id) ON DELETE CASCADE,
                    session_id TEXT,
                    full_error TEXT,
                    resolution_attempted TEXT,
                    resolution_successful BOOLEAN,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_error_patterns_fingerprint 
                ON error_patterns(fingerprint)
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
                "SELECT id, occurrence_count, resolution_success_rate FROM error_patterns WHERE fingerprint = %s",
                (fingerprint,)
            )
            row = cur.fetchone()
            
            if row:
                # Update existing pattern
                pattern_id = row['id']
                new_count = row['occurrence_count'] + 1
                
                # Update success rate if we have new data
                if resolution_successful is not None:
                    # Bayesian update
                    old_success = row['resolution_success_rate'] or 0.0
                    old_count = row['occurrence_count']
                    if old_count > 0:
                        new_rate = (old_success * old_count + (1.0 if resolution_successful else 0.0)) / (old_count + 1)
                    else:
                        new_rate = 1.0 if resolution_successful else 0.0
                    
                    cur.execute("""
                        UPDATE error_patterns 
                        SET occurrence_count = %s,
                            last_occurred = NOW(),
                            resolution_success_rate = %s,
                            resolution = COALESCE(NULLIF(%s, ''), resolution)
                        WHERE id = %s
                    """, (new_count, new_rate, resolution, pattern_id))
                else:
                    cur.execute("""
                        UPDATE error_patterns 
                        SET occurrence_count = %s,
                            last_occurred = NOW()
                        WHERE id = %s
                    """, (new_count, pattern_id))
            else:
                # Create new pattern
                cur.execute("""
                    INSERT INTO error_patterns (
                        fingerprint, error_type, error_summary, context,
                        resolution, resolution_success_rate, occurrence_count
                    ) VALUES (%s, %s, %s, %s, %s, %s, 1)
                    RETURNING id
                """, (fingerprint, error_type, error_summary, context[:500], 
                      resolution, 1.0 if resolution_successful else 0.0))
                pattern_id = cur.fetchone()['id']
            
            # Record occurrence
            cur.execute("""
                INSERT INTO error_occurrences (
                    pattern_id, session_id, full_error, resolution_attempted, resolution_successful
                ) VALUES (%s, %s, %s, %s, %s)
            """, (pattern_id, session_id, error_text[:2000], resolution, resolution_successful))
            
            return {
                "pattern_id": str(pattern_id),
                "fingerprint": fingerprint,
                "error_type": error_type,
                "is_repeat": row is not None,
                "occurrence_count": new_count if row else 1,
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
                WHERE fingerprint = %s
            """, (fingerprint,))
            
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                "pattern_id": str(row['id']),
                "fingerprint": row['fingerprint'],
                "error_type": row['error_type'],
                "error_summary": row['error_summary'],
                "resolution": row['resolution'],
                "resolution_success_rate": round(row['resolution_success_rate'] or 0, 3),
                "occurrence_count": row['occurrence_count'],
                "last_occurred": row['last_occurred'].isoformat() if row['last_occurred'] else None,
                "is_known": True,
            }
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get statistics on error patterns."""
        with _cortex_cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_patterns,
                    COUNT(*) FILTER (WHERE occurrence_count > 1) as repeats,
                    AVG(resolution_success_rate) as avg_success_rate,
                    COUNT(*) FILTER (WHERE resolution_success_rate > 0.8) as well_solved
                FROM error_patterns
            """)
            
            row = cur.fetchone()
            
            cur.execute("""
                SELECT error_type, COUNT(*) as count
                FROM error_patterns
                GROUP BY error_type
                ORDER BY count DESC
            """)
            
            by_type = {r['error_type']: r['count'] for r in cur.fetchall()}
            
            return {
                "total_patterns": row['total_patterns'],
                "repeat_patterns": row['repeats'],
                "average_success_rate": round(row['avg_success_rate'] or 0, 3),
                "well_solved_count": row['well_solved'],
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
                LIMIT %s
            """, (limit,))
            
            return [{
                "fingerprint": r['fingerprint'],
                "error_type": r['error_type'],
                "summary": r['error_summary'][:100],
                "resolution": r['resolution'][:100] if r['resolution'] else None,
                "success_rate": round(r['resolution_success_rate'] or 0, 3),
                "occurrences": r['occurrence_count'],
            } for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# Error learning engine
# ---------------------------------------------------------------------------

class ErrorLearningEngine:
    """High-level interface for error learning."""
    
    def __init__(self):
        self.store = ErrorPatternStore()
    
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
        
        # Record it
        result = self.store.record_error(
            error_text=error_text,
            context=context,
            resolution=known.get('resolution', '') if known else '',
            session_id=session_id,
        )
        
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
                SET resolution = %s,
                    resolution_success_rate = (
                        (resolution_success_rate * occurrence_count + %s) / (occurrence_count + 1)
                    ),
                    occurrence_count = occurrence_count + 1
                WHERE id = %s
            """, (resolution, 1.0 if successful else 0.0, pattern_id))
            
            cur.execute("""
                INSERT INTO error_occurrences (
                    pattern_id, resolution_attempted, resolution_successful
                ) VALUES (%s, %s, %s)
            """, (pattern_id, resolution, successful))
    
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
                WHERE context ILIKE %s AND occurrence_count > 1
                ORDER BY occurrence_count DESC
                LIMIT 3
            """, (f"%{action_description[:50]}%",))
            
            rows = cur.fetchall()
            if not rows:
                return None
            
            warnings = []
            for row in rows:
                if row['resolution_success_rate'] and row['resolution_success_rate'] > 0.5:
                    warnings.append(
                        f"- This action has caused errors {row['occurrence_count']} times before. "
                        f"Known fix: {row['resolution'][:80]}"
                    )
                else:
                    warnings.append(
                        f"- This action has caused errors {row['occurrence_count']} times before. "
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
