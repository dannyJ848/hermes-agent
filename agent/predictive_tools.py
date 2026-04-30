"""
Predictive Tool Loading System — Kimi Harness v2.2

Predicts which tools will be needed based on conversation context,
pre-loading them to reduce latency and improve relevance.

Uses Cortex to learn tool usage patterns and predict needs.

Author: Kimi
Date: 2026-04-26
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


def _cortex_cursor():
    """Get a Cortex database cursor (backward-compatible wrapper).
    
    NOTE: Uses local SQLite instead of PostgreSQL for predictive tool storage.
    """
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
        return False


# Tool categories and their typical triggers
TOOL_TRIGGERS = {
    "web_search": ["research", "find", "search", "look up", "what is", "how to", "latest"],
    "web_extract": ["read", "extract", "scrape", "get content", "article", "paper"],
    "browser_navigate": ["website", "page", "login", "form", "click", "browse"],
    "terminal": ["run", "execute", "shell", "command", "script", "build", "install"],
    "execute_code": ["python", "code", "script", "calculate", "analyze", "process"],
    "read_file": ["file", "read", "content", "source", "codebase", "config"],
    "write_file": ["create", "write", "save", "generate", "output", "export"],
    "patch": ["edit", "fix", "update", "modify", "change", "replace"],
    "search_files": ["find", "grep", "search", "locate", "where is"],
    "skills_list": ["skills", "capabilities", "what can you do", "tools"],
    "skill_view": ["skill", "how to", "guide", "instructions", "pattern"],
    "delegate_task": ["help", "assist", "do this", "parallel", "subagent", "team"],
    "cronjob": ["schedule", "cron", "automate", "recurring", "periodic"],
    "send_message": ["send", "message", "notify", "alert", "telegram", "discord"],
    "mcp_biomcp_biomcp": ["medical", "biomedical", "pubmed", "clinical", "gene", "drug"],
    "vision_analyze": ["image", "picture", "photo", "screenshot", "diagram", "chart"],
    "browser_vision": ["visual", "see", "look at", "screenshot", "ui", "interface"],
    "text_to_speech": ["speak", "voice", "audio", "read aloud", "tts"],
}


class PredictiveToolLoader:
    """Predicts and pre-loads tools based on conversation context."""
    
    def __init__(self):
        self._ensure_schema()
        self._tool_usage_cache: Dict[str, Dict[str, Any]] = {}
    
    def _ensure_schema(self):
        """Ensure tool prediction tables exist (SQLite-compatible)."""
        with _cortex_cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tool_usage_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    context_keywords TEXT DEFAULT '',
                    preceding_tools TEXT DEFAULT '',
                    success_rate REAL DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 1,
                    avg_latency_ms INTEGER,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tool_sequence_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_a TEXT NOT NULL,
                    tool_b TEXT NOT NULL,
                    sequence_count INTEGER DEFAULT 1,
                    avg_gap_turns INTEGER DEFAULT 1,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_tool_usage_tool_name 
                ON tool_usage_patterns(tool_name)
            """)
    
    def predict_needed_tools(
        self,
        query: str,
        recent_tools_used: List[str] = None,
        top_k: int = 5,
    ) -> List[Tuple[str, float]]:
        """
        Predict which tools will be needed for a query.
        Returns list of (tool_name, confidence_score).
        """
        scores: Dict[str, float] = {}
        query_lower = query.lower()
        
        # Method 1: Keyword matching
        for tool, triggers in TOOL_TRIGGERS.items():
            for trigger in triggers:
                if trigger in query_lower:
                    scores[tool] = scores.get(tool, 0) + 0.3
        
        # Method 2: Sequence patterns (if tool A was used, tool B often follows)
        if recent_tools_used:
            with _cortex_cursor() as cur:
                placeholders = ','.join(['?'] * len(recent_tools_used))
                cur.execute(f"""
                    SELECT tool_b, sequence_count, avg_gap_turns
                    FROM tool_sequence_patterns
                    WHERE tool_a IN ({placeholders})
                    ORDER BY sequence_count DESC
                    LIMIT 10
                """, tuple(recent_tools_used))
                
                for row in cur.fetchall():
                    tool_b = row['tool_b']
                    boost = min(0.5, row['sequence_count'] / 10)  # Cap at 0.5
                    scores[tool_b] = scores.get(tool_b, 0) + boost
        
        # Method 3: Cortex learned patterns
        with _cortex_cursor() as cur:
            # Find tools that were successful in similar contexts
            query_words = [w for w in query_lower.split() if len(w) > 3]
            if query_words:
                # SQLite doesn't have array operators, use LIKE matching
                conditions = ' OR '.join(['context_keywords LIKE ?'] * len(query_words))
                params = [f'%{w}%' for w in query_words]
                cur.execute(f"""
                    SELECT tool_name, success_rate, usage_count
                    FROM tool_usage_patterns
                    WHERE {conditions}
                    ORDER BY success_rate * usage_count DESC
                    LIMIT 10
                """, params)
                
                for row in cur.fetchall():
                    tool = row['tool_name']
                    learned_score = (row['success_rate'] or 0.5) * min(1.0, row['usage_count'] / 5)
                    scores[tool] = scores.get(tool, 0) + learned_score * 0.4
        
        # Sort and return top_k
        scored = [(tool, score) for tool, score in scores.items() if score > 0.2]
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]
    
    def record_tool_usage(
        self,
        tool_name: str,
        query_context: str,
        preceding_tools: List[str] = None,
        successful: bool = True,
        latency_ms: int = None,
    ):
        """Record that a tool was used. Updates learning patterns."""
        with _cortex_cursor() as cur:
            # Extract keywords from context
            keywords = [w for w in query_context.lower().split() if len(w) > 3][:10]
            keywords_str = ','.join(keywords)
            
            # Check if pattern exists (simplified for SQLite — match by tool_name + keywords LIKE)
            cur.execute("""
                SELECT id, usage_count, success_rate
                FROM tool_usage_patterns
                WHERE tool_name = ?
                  AND context_keywords LIKE ?
                LIMIT 1
            """, (tool_name, f"%{keywords_str[:30]}%"))
            
            row = cur.fetchone()
            if row:
                # Update
                new_count = row['usage_count'] + 1
                old_success = row['success_rate'] or 0.5
                new_success = (old_success * row['usage_count'] + (1.0 if successful else 0.0)) / new_count
                
                # Update avg latency (sqlite3.Row doesn't have .get())
                avg_lat = row['avg_latency_ms'] if 'avg_latency_ms' in row.keys() else None
                if latency_ms and avg_lat:
                    new_latency = (avg_lat * row['usage_count'] + latency_ms) / new_count
                elif latency_ms:
                    new_latency = latency_ms
                else:
                    new_latency = avg_lat
                
                cur.execute("""
                    UPDATE tool_usage_patterns
                    SET usage_count = ?,
                        success_rate = ?,
                        last_used = CURRENT_TIMESTAMP,
                        avg_latency_ms = ?
                    WHERE id = ?
                """, (new_count, new_success, new_latency, row['id']))
            else:
                # Create
                preceding_str = ','.join(preceding_tools or [])
                cur.execute("""
                    INSERT INTO tool_usage_patterns (
                        tool_name, context_keywords, preceding_tools,
                        success_rate, usage_count, avg_latency_ms, last_used
                    ) VALUES (?, ?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
                """, (tool_name, keywords_str, preceding_str,
                      1.0 if successful else 0.0, latency_ms or 0))
            
            # Update sequence patterns (SQLite-compatible upsert)
            if preceding_tools:
                for prev_tool in preceding_tools[-3:]:  # Last 3 tools
                    cur.execute("""
                        SELECT id, sequence_count FROM tool_sequence_patterns
                        WHERE tool_a = ? AND tool_b = ?
                    """, (prev_tool, tool_name))
                    seq_row = cur.fetchone()
                    if seq_row:
                        cur.execute("""
                            UPDATE tool_sequence_patterns
                            SET sequence_count = sequence_count + 1,
                                last_seen = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (seq_row['id'],))
                    else:
                        cur.execute("""
                            INSERT INTO tool_sequence_patterns (tool_a, tool_b, sequence_count, last_seen)
                            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                        """, (prev_tool, tool_name))
    
    def get_tool_recommendations(
        self,
        current_task: str,
        available_tools: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Get tool recommendations for a task.
        Returns list of dicts with tool info and reasoning.
        """
        predictions = self.predict_needed_tools(current_task, top_k=10)
        
        recommendations = []
        for tool, score in predictions:
            if tool in available_tools:
                # Get stats
                with _cortex_cursor() as cur:
                    cur.execute("""
                        SELECT success_rate, usage_count, avg_latency_ms
                        FROM tool_usage_patterns
                        WHERE tool_name = ?
                        ORDER BY usage_count DESC
                        LIMIT 1
                    """, (tool,))
                    
                    row = cur.fetchone()
                    if row:
                        recommendations.append({
                            "tool": tool,
                            "confidence": round(score, 3),
                            "success_rate": round(row['success_rate'] or 0, 3),
                            "usage_count": row['usage_count'],
                            "avg_latency_ms": row['avg_latency_ms'],
                            "reasoning": f"Predicted based on task context (score: {score:.2f})",
                        })
        
        return recommendations


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_predictive_loader: Optional[PredictiveToolLoader] = None

def get_predictive_loader() -> PredictiveToolLoader:
    global _predictive_loader
    if _predictive_loader is None:
        _predictive_loader = PredictiveToolLoader()
    return _predictive_loader
