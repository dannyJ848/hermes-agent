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
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cortex integration
# ---------------------------------------------------------------------------

def _cortex_cursor():
    """Get a Cortex database cursor."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path.home() / "subconscious"))
    from cortex_access import cortex_cursor
    return cortex_cursor()


# ---------------------------------------------------------------------------
# Learning engine
# ---------------------------------------------------------------------------

class CortexLearningEngine:
    """Analyzes memory usage patterns and updates usefulness scores in Cortex."""
    
    def __init__(self):
        self._bank_id = "hermes_memory_archive"
    
    def record_memory_injected(
        self,
        memory_id: str,
        session_id: str,
        query_context: str = "",
    ):
        """Record that a memory was injected into the system prompt."""
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
# Singleton
# ---------------------------------------------------------------------------

_learning_engine: Optional[CortexLearningEngine] = None

def get_learning_engine() -> CortexLearningEngine:
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = CortexLearningEngine()
    return _learning_engine
