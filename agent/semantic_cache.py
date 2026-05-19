"""SQLite-backed semantic response cache with similarity matching."""

import difflib
import hashlib
import sqlite3
import time
from pathlib import Path
from typing import Optional


class SemanticCache:
    """Caches responses keyed by query text with fuzzy similarity lookup."""

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

    def __init__(self, db_path: str = ":memory:", similarity_threshold: float = 0.60):
        self.db_path = db_path
        self.similarity_threshold = similarity_threshold
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()
        self._prune_old_entries()

    def _init_db(self) -> None:
        with self._conn:
            self._conn.executescript(self.SCHEMA)

    def _prune_old_entries(self) -> None:
        cutoff = time.time() - (7 * 24 * 60 * 60)
        with self._conn:
            cursor = self._conn.execute(
                "DELETE FROM cache_entries WHERE timestamp < ?",
                (cutoff,),
            )
            if cursor.rowcount:
                self._conn.commit()

    @staticmethod
    def _hash_query(query_text: str) -> str:
        return hashlib.sha256(query_text.encode("utf-8")).hexdigest()

    def get(self, query_text: str) -> Optional[str]:
        """Return cached response if exact or fuzzy match exceeds threshold."""
        query_hash = self._hash_query(query_text)

        # Exact match
        row = self._conn.execute(
            "SELECT id, response_text FROM cache_entries WHERE query_hash = ?",
            (query_hash,),
        ).fetchone()

        if row:
            self._conn.execute(
                "UPDATE cache_entries SET hit_count = hit_count + 1 WHERE id = ?",
                (row["id"],),
            )
            self._conn.commit()
            return row["response_text"]

        # Fuzzy match
        rows = self._conn.execute(
            "SELECT id, query_text, response_text FROM cache_entries"
        ).fetchall()

        best_match: Optional[sqlite3.Row] = None
        best_ratio = 0.0

        for row in rows:
            ratio = difflib.SequenceMatcher(None, query_text, row["query_text"]).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = row

        if best_match and best_ratio >= self.similarity_threshold:
            self._conn.execute(
                "UPDATE cache_entries SET hit_count = hit_count + 1 WHERE id = ?",
                (best_match["id"],),
            )
            self._conn.commit()
            return best_match["response_text"]

        return None

    def put(self, query_text: str, response_text: str) -> None:
        """Store or replace a cached response for the given query."""
        query_hash = self._hash_query(query_text)
        now = time.time()

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

    def close(self) -> None:
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
