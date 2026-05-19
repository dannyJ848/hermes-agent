"""SQLite-backed semantic response cache with similarity matching.

ZERO-FAILURE GUARANTEE:
- Every method catches ALL exceptions and returns safe defaults
- DB connection failures → in-memory fallback
- Empty cache → None (cache miss, not error)
- Invalid queries → None
"""

import difflib
import hashlib
import logging
import sqlite3
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SemanticCache:
    """Caches responses keyed by query text with fuzzy similarity lookup.
    
    ZERO-FAILURE: Every operation has a safe fallback.
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS cache_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_hash TEXT UNIQUE NOT NULL,
        query_text TEXT NOT NULL,
        response_text TEXT NOT NULL,
        timestamp REAL NOT NULL,
        hit_count INTEGER NOT NULL DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS idx_query_hash ON cache_entries(query_hash);
    CREATE INDEX IF NOT EXISTS idx_timestamp ON cache_entries(timestamp);
    """

    def __init__(self, db_path: str = None, similarity_threshold: float = 0.60):
        """Initialize cache. If db_path is None, uses ~/.hermes/semantic_cache.db"""
        if db_path is None:
            db_path = str(Path.home() / ".hermes" / "semantic_cache.db")
        
        self.db_path = db_path
        self.similarity_threshold = max(0.1, min(1.0, similarity_threshold))
        self._conn = None
        self._in_memory_cache: dict[str, tuple[str, float]] = {}  # hash -> (response, timestamp)
        
        # Try SQLite
        try:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._init_db()
            self._prune_old_entries()
        except Exception as e:
            logger.warning("[SemanticCache] SQLite failed (%s), using in-memory fallback", e)
            self._conn = None

    def _init_db(self) -> None:
        if self._conn is None:
            return
        try:
            with self._conn:
                self._conn.executescript(self.SCHEMA)
        except Exception as e:
            logger.debug("[SemanticCache] DB init failed: %s", e)
            self._conn = None

    def _prune_old_entries(self) -> None:
        if self._conn is None:
            return
        try:
            cutoff = time.time() - (7 * 24 * 60 * 60)
            with self._conn:
                cursor = self._conn.execute(
                    "DELETE FROM cache_entries WHERE timestamp < ?",
                    (cutoff,),
                )
                if cursor.rowcount:
                    self._conn.commit()
        except Exception as e:
            logger.debug("[SemanticCache] Prune failed: %s", e)

    @staticmethod
    def _hash_query(query_text: str) -> str:
        try:
            return hashlib.sha256(query_text.encode("utf-8")).hexdigest()
        except Exception:
            return hashlib.sha256(str(query_text).encode("utf-8")).hexdigest()

    def get(self, query_text: str) -> Optional[str]:
        """Return cached response if exact or fuzzy match exceeds threshold.
        
        NEVER FAILS: Returns None on any error (cache miss, not failure).
        """
        if not query_text or not isinstance(query_text, str):
            return None
        
        query_hash = self._hash_query(query_text)
        
        # Try SQLite
        if self._conn is not None:
            try:
                # Exact match
                row = self._conn.execute(
                    "SELECT id, response_text FROM cache_entries WHERE query_hash = ?",
                    (query_hash,),
                ).fetchone()
                
                if row:
                    try:
                        self._conn.execute(
                            "UPDATE cache_entries SET hit_count = hit_count + 1 WHERE id = ?",
                            (row["id"],),
                        )
                        self._conn.commit()
                    except Exception:
                        pass
                    return row["response_text"]
                
                # Fuzzy match
                rows = self._conn.execute(
                    "SELECT id, query_text, response_text FROM cache_entries"
                ).fetchall()
                
                best_match = None
                best_ratio = 0.0
                
                for row in rows:
                    try:
                        ratio = difflib.SequenceMatcher(None, query_text, row["query_text"]).ratio()
                        if ratio > best_ratio:
                            best_ratio = ratio
                            best_match = row
                    except Exception:
                        continue
                
                if best_match and best_ratio >= self.similarity_threshold:
                    try:
                        self._conn.execute(
                            "UPDATE cache_entries SET hit_count = hit_count + 1 WHERE id = ?",
                            (best_match["id"],),
                        )
                        self._conn.commit()
                    except Exception:
                        pass
                    return best_match["response_text"]
                
                return None
            except Exception as e:
                logger.debug("[SemanticCache] SQLite get failed: %s", e)
        
        # In-memory fallback
        try:
            # Exact
            if query_hash in self._in_memory_cache:
                return self._in_memory_cache[query_hash][0]
            
            # Fuzzy
            best_match = None
            best_ratio = 0.0
            for h, (response, _ts) in self._in_memory_cache.items():
                try:
                    ratio = difflib.SequenceMatcher(None, query_text, h).ratio()
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_match = response
                except Exception:
                    continue
            
            if best_match and best_ratio >= self.similarity_threshold:
                return best_match
            
            return None
        except Exception:
            return None

    def put(self, query_text: str, response_text: str) -> None:
        """Store or replace a cached response. NEVER FAILS."""
        if not query_text or not response_text:
            return
        
        query_hash = self._hash_query(query_text)
        now = time.time()
        
        # Try SQLite
        if self._conn is not None:
            try:
                with self._conn:
                    self._conn.execute(
                        """
                        INSERT INTO cache_entries (query_hash, query_text, response_text, timestamp, hit_count)
                        VALUES (?, ?, ?, ?, 0)
                        ON CONFLICT(query_hash) DO UPDATE SET
                            response_text = excluded.response_text,
                            timestamp = excluded.timestamp,
                            hit_count = 0
                        """,
                        (query_hash, query_text, response_text, now),
                    )
                    self._conn.commit()
                return
            except Exception as e:
                logger.debug("[SemanticCache] SQLite put failed: %s", e)
        
        # In-memory fallback
        self._in_memory_cache[query_hash] = (response_text, now)

    def close(self) -> None:
        """Close the database connection."""
        try:
            if self._conn:
                self._conn.close()
        except Exception:
            pass
        self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
