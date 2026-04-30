"""
Cortex Learning Engine — Kimi Harness v2.0

Integrates with the Cortex PostgreSQL database to track memory usefulness,
learn from usage patterns, and predict which memories/skills will be
relevant to future queries.

Uses the enhanced memory_units schema:
  - usefulness_score: Bayesian-updated probability of being useful
  - success_count/failure_count: Usage statistics
  - last_accessed: When it was last used
  - usage_contexts: JSONB array of contexts where it was useful

Plus the memory_usage_log table for detailed event tracking.

Author: Kimi
Date: 2026-04-26
"""

from __future__ import annotations

import json
import logging
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cortex integration — uses centralized cortex_access module
# ---------------------------------------------------------------------------

def _cortex_cursor():
    """Get a Cortex database cursor (backward-compatible wrapper)."""
    from agent.cortex_access import cortex_cursor
    return cortex_cursor()


# ---------------------------------------------------------------------------
# Learning engine
# ---------------------------------------------------------------------------

class CortexLearningEngine:
    """Analyzes memory usage patterns and updates usefulness scores in Cortex."""
    
    def __init__(self):
        self._bank_id = "hermes_memory_archive"
        self._schema_ensured = False
        self.store = _CortexLearningStore()  # Expose store for adaptive_injection.py
    
    def _ensure_schema(self):
        """Create missing tables if they don't exist."""
        if self._schema_ensured:
            return
        with _cortex_cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS memory_units (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    bank_id TEXT NOT NULL DEFAULT 'hermes_memory_archive',
                    content TEXT NOT NULL,
                    content_hash TEXT UNIQUE,
                    memory_type TEXT DEFAULT 'fact',
                    usefulness_score FLOAT DEFAULT 0.5,
                    success_count INT DEFAULT 0,
                    failure_count INT DEFAULT 0,
                    access_count INT DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    last_accessed TIMESTAMPTZ,
                    last_evaluated TIMESTAMPTZ,
                    usage_contexts JSONB DEFAULT '[]',
                    metadata JSONB DEFAULT '{}'
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_units_bank 
                ON memory_units(bank_id, usefulness_score DESC)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_units_hash 
                ON memory_units(content_hash)
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS memory_usage_log (
                    id SERIAL PRIMARY KEY,
                    memory_id UUID REFERENCES memory_units(id) ON DELETE SET NULL,
                    session_id TEXT,
                    action TEXT NOT NULL,
                    was_useful BOOLEAN,
                    query_context TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_log_memory 
                ON memory_usage_log(memory_id, created_at DESC)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_log_session 
                ON memory_usage_log(session_id, created_at DESC)
            """)
        self._schema_ensured = True
    
    def record_memory_injected(
        self,
        memory_id: str,
        session_id: str,
        query_context: str = "",
    ):
        """Record that a memory was injected into the system prompt."""
        self._ensure_schema()
        with _cortex_cursor() as cur:
            cur.execute("""
                INSERT INTO memory_usage_log (memory_id, session_id, action, query_context)
                VALUES (%s, %s, 'injected', %s)
            """, (memory_id, session_id, query_context))
            
            cur.execute("""
                UPDATE memory_units 
                SET access_count = access_count + 1,
                    last_accessed = NOW()
                WHERE id = %s
            """, (memory_id,))
    
    def record_memory_useful(
        self,
        memory_id: str,
        session_id: str,
        query_context: str = "",
        was_useful: bool = True,
    ):
        """Record whether an injected memory was actually useful."""
        with _cortex_cursor() as cur:
            # Log the event (memory_id might be a hash string, not UUID)
            try:
                uuid_val = str(memory_id)
                # Validate it's a UUID format
                from uuid import UUID
                UUID(uuid_val)
            except ValueError:
                # Not a valid UUID — find the memory by content hash or skip
                # For now, just log without FK constraint
                cur.execute("""
                    INSERT INTO memory_usage_log (memory_id, session_id, action, was_useful, query_context)
                    VALUES (NULL, %s, 'evaluated', %s, %s)
                """, (session_id, was_useful, query_context))
                return
            
            # Update counts
            if was_useful:
                cur.execute("""
                    UPDATE memory_units 
                    SET success_count = success_count + 1,
                        usefulness_score = LEAST(1.0, (success_count + 1)::float / NULLIF(success_count + failure_count + 2, 0)),
                        usage_contexts = usage_contexts || jsonb_build_array(%s)
                    WHERE id = %s
                """, (query_context[:200], memory_id))
            else:
                cur.execute("""
                    UPDATE memory_units 
                    SET failure_count = failure_count + 1,
                        usefulness_score = GREATEST(0.0, success_count::float / NULLIF(success_count + failure_count + 2, 0))
                    WHERE id = %s
                """, (memory_id,))
    
    def record_skill_loaded(
        self,
        skill_name: str,
        session_id: str,
        was_followed: bool = True,
        query_context: str = "",
    ):
        """Record skill usage. Skills are stored as memory_units with skill: prefix."""
        with _cortex_cursor() as cur:
            # Find or create skill memory
            cur.execute("""
                SELECT id FROM memory_units 
                WHERE bank_id = %s AND metadata->>'skill_name' = %s
            """, (self._bank_id, skill_name))
            
            row = cur.fetchone()
            if row:
                memory_id = row['id']
            else:
                # Create skill memory entry
                cur.execute("""
                    INSERT INTO memory_units (
                        id, bank_id, text, fact_type, metadata, tags, created_at
                    ) VALUES (
                        gen_random_uuid(), %s, %s, 'world',
                        jsonb_build_object('skill_name', %s, 'type', 'skill'),
                        ARRAY['skill', %s], NOW()
                    )
                    RETURNING id
                """, (self._bank_id, f"Skill: {skill_name}", skill_name, skill_name))
                memory_id = cur.fetchone()['id']
            
            # Log usage
            action = 'followed' if was_followed else 'loaded_not_followed'
            cur.execute("""
                INSERT INTO memory_usage_log (memory_id, session_id, action, was_useful, query_context)
                VALUES (%s, %s, %s, %s, %s)
            """, (memory_id, session_id, action, was_followed, query_context))
            
            # Update score
            if was_followed:
                cur.execute("""
                    UPDATE memory_units 
                    SET success_count = success_count + 1,
                        access_count = access_count + 1,
                        usefulness_score = LEAST(1.0, (success_count + 1)::float / NULLIF(success_count + failure_count + 2, 0)),
                        last_accessed = NOW()
                    WHERE id = %s
                """, (memory_id,))
            else:
                cur.execute("""
                    UPDATE memory_units 
                    SET failure_count = failure_count + 1,
                        access_count = access_count + 1,
                        last_accessed = NOW()
                    WHERE id = %s
                """, (memory_id,))
    
    def predict_relevant_memories(
        self,
        query: str,
        limit: int = 20,
        min_score: float = 0.1,
    ) -> List[Dict[str, Any]]:
        """
        Predict which memories will be relevant to a query.
        Combines full-text search with learned usefulness scores.
        """
        with _cortex_cursor() as cur:
            # Query with combined scoring: ts_rank * usefulness_score
            cur.execute("""
                SELECT 
                    id,
                    text,
                    fact_type,
                    metadata->>'key' as key,
                    access_count,
                    usefulness_score,
                    success_count,
                    failure_count,
                    ts_rank(search_vector, plainto_tsquery('english', %s)) * 
                        COALESCE(usefulness_score, 0.5) as combined_score,
                    created_at
                FROM memory_units
                WHERE bank_id = %s
                  AND search_vector @@ plainto_tsquery('english', %s)
                ORDER BY combined_score DESC
                LIMIT %s
            """, (query, self._bank_id, query, limit))
            
            results = []
            for row in cur.fetchall():
                if row['combined_score'] < min_score:
                    continue
                results.append({
                    "id": str(row['id']),
                    "key": row['key'],
                    "text": row['text'][:300] + "..." if len(row['text']) > 300 else row['text'],
                    "fact_type": row['fact_type'],
                    "usefulness_score": round(row['usefulness_score'] or 0.5, 3),
                    "access_count": row['access_count'],
                    "success_count": row['success_count'],
                    "failure_count": row['failure_count'],
                    "combined_score": round(row['combined_score'], 4),
                    "date": row['created_at'].isoformat() if row['created_at'] else None,
                })
            
            return results
    
    def predict_relevant_skills(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Predict which skills will be relevant to a query."""
        with _cortex_cursor() as cur:
            cur.execute("""
                SELECT 
                    id,
                    metadata->>'skill_name' as skill_name,
                    text,
                    usefulness_score,
                    success_count,
                    failure_count,
                    ts_rank(search_vector, plainto_tsquery('english', %s)) * 
                        COALESCE(usefulness_score, 0.5) as combined_score
                FROM memory_units
                WHERE bank_id = %s
                  AND tags @> ARRAY['skill']::varchar[]
                  AND search_vector @@ plainto_tsquery('english', %s)
                ORDER BY combined_score DESC
                LIMIT %s
            """, (query, self._bank_id, query, limit))
            
            return [{
                "id": str(r['id']),
                "skill_name": r['skill_name'],
                "usefulness_score": round(r['usefulness_score'] or 0.5, 3),
                "success_count": r['success_count'],
                "failure_count": r['failure_count'],
                "combined_score": round(r['combined_score'], 4),
            } for r in cur.fetchall()]
    
    def get_learning_report(self) -> Dict[str, Any]:
        """Generate report on what the system has learned."""
        with _cortex_cursor() as cur:
            # Overall stats
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(usefulness_score) as avg_usefulness,
                    SUM(success_count) as total_successes,
                    SUM(failure_count) as total_failures,
                    COUNT(*) FILTER (WHERE success_count + failure_count > 0) as learned_items
                FROM memory_units
                WHERE bank_id = %s
            """, (self._bank_id,))
            
            overall = cur.fetchone()
            
            # Top performing memories
            cur.execute("""
                SELECT text, usefulness_score, success_count, failure_count
                FROM memory_units
                WHERE bank_id = %s AND success_count + failure_count > 2
                ORDER BY usefulness_score DESC
                LIMIT 10
            """, (self._bank_id,))
            
            top_memories = [{
                "text": r['text'][:100] + "...",
                "score": round(r['usefulness_score'], 3),
                "success": r['success_count'],
                "failure": r['failure_count'],
            } for r in cur.fetchall()]
            
            # Top skills
            cur.execute("""
                SELECT metadata->>'skill_name' as name, usefulness_score, success_count
                FROM memory_units
                WHERE bank_id = %s AND tags @> ARRAY['skill']::varchar[]
                ORDER BY usefulness_score DESC
                LIMIT 10
            """, (self._bank_id,))
            
            top_skills = [{
                "name": r['name'],
                "score": round(r['usefulness_score'], 3),
                "success": r['success_count'],
            } for r in cur.fetchall()]
            
            return {
                "total_memories": overall['total'],
                "learned_items": overall['learned_items'],
                "average_usefulness": round(overall['avg_usefulness'] or 0, 3),
                "total_successes": overall['total_successes'],
                "total_failures": overall['total_failures'],
                "success_rate": round(
                    overall['total_successes'] / max(1, overall['total_successes'] + overall['total_failures']),
                    3
                ),
                "top_memories": top_memories,
                "top_skills": top_skills,
            }
    
    def process_session_feedback(
        self,
        session_id: str,
        injected_memory_ids: List[str],
        referenced_memory_ids: List[str],
        loaded_skills: List[str],
        followed_skills: List[str],
        query_summary: str = "",
    ):
        """
        Process a completed session to update all learned scores.
        Call this at session end or compression time.
        """
        # Update memory usefulness
        for mem_id in injected_memory_ids:
            was_useful = mem_id in referenced_memory_ids
            self.record_memory_useful(mem_id, session_id, query_summary, was_useful)
        
        # Update skill usefulness
        for skill in loaded_skills:
            was_followed = skill in followed_skills
            self.record_skill_loaded(skill, session_id, was_followed, query_summary)
        
        logger.info(
            "Cortex learning: processed session %s — %d memories, %d skills",
            session_id, len(injected_memory_ids), len(loaded_skills)
        )


# ---------------------------------------------------------------------------
# Store adapter — exposes get_usage_stats() for adaptive_injection.py
# ---------------------------------------------------------------------------

class _CortexLearningStore:
    """Lightweight adapter that exposes the interface adaptive_injection expects.
    
    Reads from cerebrum_memory.db (local SQLite) for tips, and from
    cortex PostgreSQL for memory usage stats. This avoids per-turn
    PostgreSQL queries for tip injection — the hot path stays local.
    """
    
    def __init__(self):
        self._tip_cache: List[Dict] = []
        self._tip_cache_time = 0.0
        self._TIP_CACHE_TTL = 300  # 5 minutes
        self._cerebrum_path = Path.home() / ".hermes" / "cerebrum_memory.db"
    
    def get_usage_stats(self, memory_ids: List[str]) -> Dict[str, Dict]:
        """Return usage stats for given memory IDs from cortex.
        
        Called by adaptive_injection.py every turn — keep it fast.
        """
        if not memory_ids:
            return {}
        
        stats = {}
        try:
            with _cortex_cursor() as cur:
                # Batch query all at once
                placeholders = ','.join(['%s'] * len(memory_ids))
                cur.execute(f"""
                    SELECT id, usefulness_score, success_count, failure_count, access_count
                    FROM memory_units
                    WHERE id IN ({placeholders})
                """, tuple(memory_ids))
                for row in cur.fetchall():
                    stats[str(row[0])] = {
                        "usefulness_score": row[1] or 0.5,
                        "success_count": row[2] or 0,
                        "failure_count": row[3] or 0,
                        "access_count": row[4] or 0,
                    }
        except Exception as e:
            logger.debug("get_usage_stats failed: %s", e)
        
        return stats
    
    def get_distilled_tips(self, limit: int = 50) -> List[Dict]:
        """Read distilled tips from local cerebrum_memory.db.
        
        This is the HOT PATH — called every turn during system prompt building.
        Uses local SQLite with caching to avoid PostgreSQL round-trips.
        """
        now = time.time()
        if self._tip_cache and (now - self._tip_cache_time) < self._TIP_CACHE_TTL:
            return self._tip_cache[:limit]
        
        tips = []
        try:
            import sqlite3
            conn = sqlite3.connect(str(self._cerebrum_path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT tip_type, condition, recommendation, rationale, tool_name, domain, confidence, frequency, upvotes, downvotes
                FROM distilled_tips
                WHERE confidence >= 0.6
                ORDER BY frequency DESC, confidence DESC, upvotes DESC
                LIMIT ?
            """, (limit,))
            for row in cur.fetchall():
                # Build content from condition + recommendation + rationale
                parts = []
                if row["condition"]:
                    parts.append(f"Condition: {row['condition']}")
                if row["recommendation"]:
                    parts.append(f"Action: {row['recommendation']}")
                if row["rationale"]:
                    parts.append(f"Why: {row['rationale']}")
                content = " | ".join(parts) if parts else ""
                tips.append({
                    "content": content,
                    "category": row["domain"] or row["tip_type"] or "general",
                    "confidence": row["confidence"],
                    "usage_count": row["frequency"] or 0,
                    "tool_name": row["tool_name"] or "",
                })
            conn.close()
        except Exception as e:
            logger.debug("get_distilled_tips failed: %s", e)
        
        self._tip_cache = tips
        self._tip_cache_time = now
        return tips[:limit]


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_learning_engine: Optional[CortexLearningEngine] = None

def get_learning_engine() -> CortexLearningEngine:
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = CortexLearningEngine()
    return _learning_engine
