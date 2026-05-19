#!/usr/bin/env python3
"""
Cerebrum Memory System — 4-tier biologically-inspired memory with automatic consolidation.

Tiers:
  1. Episodic — raw session events (short-term, high detail, 7-day TTL)
  2. Semantic — distilled facts/concepts (mid-term, confidence-scored)
  3. Procedural — how-to workflows (long-term, success-rate tracked)
  4. Distilled Tips — highest-value learnings injected into agent context

Consolidation: episodic → semantic → procedural → tips (nightly)
"""

import sqlite3
import json
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

HERMES_HOME = Path.home() / ".hermes"
DB_PATH = HERMES_HOME / "cerebrum_memory.db"


def _safe(fn):
    """Decorator: catch-all fallback for every operation."""
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            # Log silently, return safe default
            print(f"[cerebrum] {fn.__name__} failed: {e}")
            if fn.__name__.startswith("get_") or fn.__name__.startswith("query_"):
                return []
            if fn.__name__.startswith("count_"):
                return 0
            return None
    return wrapper


class CerebrumMemory:
    """4-tier memory system with automatic consolidation."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._ensure_db()

    def _ensure_db(self):
        try:
            HERMES_HOME.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            # Episodic
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context_json TEXT,
                    emotional_valence REAL DEFAULT 0.0,
                    importance_score REAL DEFAULT 0.5,
                    source TEXT DEFAULT 'session',
                    created_at REAL DEFAULT (julianday('now'))
                )
            ''')
            # Semantic
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS semantic_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concept_key TEXT UNIQUE NOT NULL,
                    category TEXT NOT NULL,
                    fact_text TEXT NOT NULL,
                    confidence REAL DEFAULT 0.8,
                    source_episodes TEXT,
                    last_verified REAL,
                    access_count INTEGER DEFAULT 0,
                    created_at REAL DEFAULT (julianday('now'))
                )
            ''')
            # Procedural
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS procedural_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_name TEXT UNIQUE NOT NULL,
                    trigger_conditions TEXT NOT NULL,
                    action_sequence TEXT NOT NULL,
                    success_rate REAL DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0,
                    last_used REAL,
                    origin_session TEXT,
                    created_at REAL DEFAULT (julianday('now'))
                )
            ''')
            # Tips
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS distilled_tips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tip_hash TEXT UNIQUE NOT NULL,
                    topic TEXT NOT NULL,
                    tip_text TEXT NOT NULL,
                    priority INTEGER DEFAULT 5,
                    source_sessions TEXT,
                    verification_status TEXT DEFAULT 'unverified',
                    created_at REAL DEFAULT (julianday('now'))
                )
            ''')
            # Consolidation log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consolidation_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_tier TEXT NOT NULL,
                    to_tier TEXT NOT NULL,
                    item_count INTEGER,
                    method TEXT,
                    timestamp REAL DEFAULT (julianday('now'))
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[cerebrum] DB init failed: {e}")

    @_safe
    def capture_episode(self, session_id: str, event_type: str, content: str,
                        context: Optional[Dict] = None, emotional_valence: float = 0.0,
                        importance: float = 0.5, source: str = "session") -> Optional[int]:
        """Store a raw episodic memory."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO episodic_memory (session_id, timestamp, event_type, content, context_json,
                                         emotional_valence, importance_score, source)
            VALUES (?, julianday('now'), ?, ?, ?, ?, ?, ?)
        ''', (session_id, event_type, content, json.dumps(context) if context else None,
              emotional_valence, importance, source))
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return row_id

    @_safe
    def get_episodes(self, session_id: Optional[str] = None, event_type: Optional[str] = None,
                     min_importance: float = 0.0, limit: int = 100) -> List[Dict]:
        """Retrieve episodic memories with filters."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM episodic_memory WHERE importance_score >= ?"
        params = [min_importance]
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @_safe
    def store_semantic(self, concept_key: str, category: str, fact_text: str,
                       confidence: float = 0.8, source_episodes: Optional[List[int]] = None) -> bool:
        """Store or update a semantic fact."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        # Upsert
        cursor.execute('''
            INSERT INTO semantic_memory (concept_key, category, fact_text, confidence, source_episodes, last_verified)
            VALUES (?, ?, ?, ?, ?, julianday('now'))
            ON CONFLICT(concept_key) DO UPDATE SET
                fact_text = excluded.fact_text,
                confidence = MAX(semantic_memory.confidence, excluded.confidence),
                last_verified = julianday('now'),
                access_count = semantic_memory.access_count + 1
        ''', (concept_key, category, fact_text, confidence,
              json.dumps(source_episodes) if source_episodes else None))
        conn.commit()
        conn.close()
        return True

    @_safe
    def get_semantic(self, concept_key: str) -> Optional[Dict]:
        """Retrieve a semantic fact."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM semantic_memory WHERE concept_key = ?", (concept_key,))
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE semantic_memory SET access_count = access_count + 1 WHERE concept_key = ?",
                          (concept_key,))
            conn.commit()
        conn.close()
        return dict(row) if row else None

    @_safe
    def search_semantic(self, query: str, category: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Search semantic memory by text match."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        sql = "SELECT * FROM semantic_memory WHERE (concept_key LIKE ? OR fact_text LIKE ?)"
        params = [f"%{query}%", f"%{query}%"]
        if category:
            sql += " AND category = ?"
            params.append(category)
        sql += " ORDER BY confidence DESC, access_count DESC LIMIT ?"
        params.append(limit)
        cursor.execute(sql, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @_safe
    def store_procedural(self, pattern_name: str, trigger_conditions: str,
                         action_sequence: str, origin_session: Optional[str] = None) -> bool:
        """Store a procedural pattern."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO procedural_memory (pattern_name, trigger_conditions, action_sequence, origin_session)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(pattern_name) DO UPDATE SET
                action_sequence = excluded.action_sequence,
                usage_count = procedural_memory.usage_count + 1,
                last_used = julianday('now')
        ''', (pattern_name, trigger_conditions, action_sequence, origin_session))
        conn.commit()
        conn.close()
        return True

    @_safe
    def get_procedural(self, pattern_name: str) -> Optional[Dict]:
        """Retrieve a procedural pattern."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM procedural_memory WHERE pattern_name = ?", (pattern_name,))
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE procedural_memory SET usage_count = usage_count + 1, last_used = julianday('now') WHERE pattern_name = ?",
                          (pattern_name,))
            conn.commit()
        conn.close()
        return dict(row) if row else None

    @_safe
    def store_tip(self, topic: str, tip_text: str, priority: int = 5,
                  source_sessions: Optional[List[str]] = None) -> bool:
        """Store a distilled tip. Deduplicates by hash."""
        tip_hash = hashlib.sha256(tip_text.encode()).hexdigest()[:16]
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO distilled_tips (tip_hash, topic, tip_text, priority, source_sessions)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(tip_hash) DO UPDATE SET
                priority = MAX(distilled_tips.priority, excluded.priority),
                source_sessions = COALESCE(distilled_tips.source_sessions, '') || ',' || COALESCE(excluded.source_sessions, '')
        ''', (tip_hash, topic, tip_text, priority,
              json.dumps(source_sessions) if source_sessions else None))
        conn.commit()
        conn.close()
        return True

    @_safe
    def get_relevant_tips(self, query: str, limit: int = 10, min_priority: int = 1) -> List[Dict]:
        """Get tips matching a query, sorted by priority."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM distilled_tips
            WHERE (topic LIKE ? OR tip_text LIKE ?) AND priority >= ? AND verification_status != 'deprecated'
            ORDER BY priority DESC, created_at DESC
            LIMIT ?
        ''', (f"%{query}%", f"%{query}%", min_priority, limit))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @_safe
    def get_all_tips(self, limit: int = 50) -> List[Dict]:
        """Get all active tips."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM distilled_tips WHERE verification_status != 'deprecated'
            ORDER BY priority DESC, created_at DESC LIMIT ?
        ''', (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @_safe
    def verify_tip(self, tip_hash: str, success: bool) -> bool:
        """Update tip verification status based on application outcome."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT verification_status FROM distilled_tips WHERE tip_hash = ?", (tip_hash,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
        status = row[0]
        # Simple state machine: unverified → verified/deprecated
        if success:
            if status == "unverified":
                new_status = "partially_verified"
            elif status == "partially_verified":
                new_status = "verified"
            else:
                new_status = status
        else:
            if status == "unverified":
                new_status = "suspect"
            elif status == "suspect":
                new_status = "deprecated"
            else:
                new_status = status
        cursor.execute("UPDATE distilled_tips SET verification_status = ? WHERE tip_hash = ?",
                      (new_status, tip_hash))
        conn.commit()
        conn.close()
        return True

    @_safe
    def consolidate_episodic_to_semantic(self, min_importance: float = 0.7,
                                        days_back: int = 1) -> int:
        """Promote high-importance episodic events to semantic facts."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM episodic_memory
            WHERE importance_score >= ? AND created_at >= julianday('now', ?)
            ORDER BY importance_score DESC
        ''', (min_importance, f"-{days_back} days"))
        episodes = cursor.fetchall()
        promoted = 0
        for ep in episodes:
            # Simple extraction: content → concept_key + fact
            content = ep["content"]
            # Extract noun phrases as concept keys
            words = re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", content)
            if words:
                concept_key = words[0].lower()
                self.store_semantic(concept_key, "auto_extracted", content,
                                    confidence=min(0.5 + ep["importance_score"] * 0.5, 0.95),
                                    source_episodes=[ep["id"]])
                promoted += 1
        # Log consolidation
        cursor.execute('''
            INSERT INTO consolidation_log (from_tier, to_tier, item_count, method)
            VALUES (?, ?, ?, ?)
        ''', ("episodic", "semantic", promoted, "importance_threshold"))
        conn.commit()
        conn.close()
        return promoted

    @_safe
    def consolidate_semantic_to_procedural(self, min_access_count: int = 3) -> int:
        """Promote frequently-accessed semantic facts to procedural patterns."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM semantic_memory WHERE access_count >= ?
            ORDER BY access_count DESC
        ''', (min_access_count,))
        facts = cursor.fetchall()
        promoted = 0
        for fact in facts:
            pattern_name = f"auto_{fact['concept_key']}"
            trigger = f"query about {fact['concept_key']}"
            action = fact["fact_text"]
            self.store_procedural(pattern_name, trigger, action)
            promoted += 1
        cursor.execute('''
            INSERT INTO consolidation_log (from_tier, to_tier, item_count, method)
            VALUES (?, ?, ?, ?)
        ''', ("semantic", "procedural", promoted, "access_frequency"))
        conn.commit()
        conn.close()
        return promoted

    @_safe
    def cleanup_old_episodes(self, days: int = 7) -> int:
        """Remove old episodic memories (they've been consolidated or are stale)."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM episodic_memory WHERE created_at < julianday('now', ?)
        ''', (f"-{days} days",))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    @_safe
    def get_stats(self) -> Dict[str, Any]:
        """Memory system statistics."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        stats = {}
        for table in ["episodic_memory", "semantic_memory", "procedural_memory", "distilled_tips"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM consolidation_log")
        stats["consolidation_runs"] = cursor.fetchone()[0]
        conn.close()
        return stats


# Singleton for easy import
_cerebrum_instance = None

def get_cerebrum() -> CerebrumMemory:
    global _cerebrum_instance
    if _cerebrum_instance is None:
        _cerebrum_instance = CerebrumMemory()
    return _cerebrum_instance
