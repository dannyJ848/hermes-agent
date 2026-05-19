"""Vector memory module with SQLite backend and sentence-transformers embeddings.

ZERO-FAILURE GUARANTEE:
- Every method catches ALL exceptions and returns safe defaults
- DB connection failures → in-memory fallback
- sentence-transformers missing → difflib fallback
- Invalid JSON → None metadata
- Empty DB → empty list
"""

from __future__ import annotations

import json
import sqlite3
import time
import difflib
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    try:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
    except Exception:
        return 0.0


class VectorMemory:
    """SQLite-backed vector memory using sentence-transformers or difflib fallback.
    
    ZERO-FAILURE: Every operation has a safe fallback.
    """

    def __init__(self, db_path: str | Path = None) -> None:
        # Default to ~/.hermes/vector_memory.db
        if db_path is None:
            db_path = Path.home() / ".hermes" / "vector_memory.db"
        self.db_path = Path(db_path)
        
        # Ensure parent dir exists
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        
        # Try SQLite, fallback to in-memory
        self._conn = None
        self._in_memories: list[dict] = []  # In-memory fallback
        try:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._init_db()
        except Exception as e:
            logger.warning("[VectorMemory] SQLite failed (%s), using in-memory fallback", e)
            self._conn = None
        
        # Try sentence-transformers, fallback to difflib
        self._encoder = None
        try:
            from sentence_transformers import SentenceTransformer
            self._encoder = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            self._encoder = None

    def _init_db(self) -> None:
        """Create the memories table if it doesn't exist."""
        if self._conn is None:
            return
        try:
            with self._conn:
                self._conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        text TEXT NOT NULL,
                        embedding_json TEXT,
                        metadata_json TEXT,
                        timestamp REAL NOT NULL
                    )
                    """
                )
        except Exception as e:
            logger.warning("[VectorMemory] DB init failed: %s", e)
            self._conn = None

    def add_memory(self, text: str, metadata: dict[str, Any] | None = None) -> int:
        """Add a memory and return its id. Returns -1 on any failure."""
        if not text or not isinstance(text, str):
            return -1
        
        timestamp = time.time()
        
        # Try SQLite first
        if self._conn is not None:
            try:
                embedding_json = None
                if self._encoder is not None:
                    try:
                        embedding = self._encoder.encode(text).tolist()
                        embedding_json = json.dumps(embedding)
                    except Exception:
                        pass
                
                metadata_json = None
                try:
                    metadata_json = json.dumps(metadata) if metadata else None
                except Exception:
                    pass
                
                with self._conn:
                    cur = self._conn.execute(
                        """
                        INSERT INTO memories (text, embedding_json, metadata_json, timestamp)
                        VALUES (?, ?, ?, ?)
                        """,
                        (text, embedding_json, metadata_json, timestamp),
                    )
                    return int(cur.lastrowid)
            except Exception as e:
                logger.debug("[VectorMemory] SQLite insert failed: %s", e)
        
        # In-memory fallback
        self._in_memories.append({
            "id": len(self._in_memories) + 1,
            "text": text,
            "metadata": metadata,
            "timestamp": timestamp,
            "score": 0.0,
        })
        return len(self._in_memories)

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """Search memories by cosine similarity or difflib fallback.
        
        NEVER FAILS: Returns empty list on any error.
        """
        if not query or not isinstance(query, str):
            return []
        
        k = max(1, int(k))
        
        # Try SQLite first
        if self._conn is not None:
            try:
                rows = self._conn.execute(
                    "SELECT id, text, embedding_json, metadata_json, timestamp FROM memories"
                ).fetchall()
                
                if not rows:
                    return []
                
                results: list[tuple[float, dict[str, Any]]] = []
                
                if self._encoder is not None:
                    try:
                        query_embedding = self._encoder.encode(query).tolist()
                        for row in rows:
                            row_id, text, embedding_json, metadata_json, timestamp = row
                            score = 0.0
                            if embedding_json:
                                try:
                                    embedding = json.loads(embedding_json)
                                    score = _cosine_similarity(query_embedding, embedding)
                                except Exception:
                                    pass
                            results.append(
                                (
                                    score,
                                    {
                                        "id": row_id,
                                        "text": text,
                                        "metadata": json.loads(metadata_json) if metadata_json else None,
                                        "timestamp": timestamp,
                                        "score": score,
                                    },
                                )
                            )
                    except Exception:
                        # Fallback to difflib on encoder failure
                        pass
                    else:
                        results.sort(key=lambda x: x[0], reverse=True)
                        return [r[1] for r in results[:k]]
                
                # difflib fallback (no encoder or encoder failed)
                for row in rows:
                    row_id, text, _embedding_json, metadata_json, timestamp = row
                    try:
                        meta = json.loads(metadata_json) if metadata_json else None
                    except Exception:
                        meta = None
                    score = difflib.SequenceMatcher(None, query.lower(), text.lower()).ratio()
                    results.append(
                        (
                            score,
                            {
                                "id": row_id,
                                "text": text,
                                "metadata": meta,
                                "timestamp": timestamp,
                                "score": score,
                            },
                        )
                    )
                
                results.sort(key=lambda x: x[0], reverse=True)
                return [r[1] for r in results[:k]]
            
            except Exception as e:
                logger.debug("[VectorMemory] SQLite search failed: %s", e)
        
        # In-memory fallback search
        try:
            results = []
            for mem in self._in_memories:
                score = difflib.SequenceMatcher(None, query.lower(), mem["text"].lower()).ratio()
                results.append((score, {**mem, "score": score}))
            results.sort(key=lambda x: x[0], reverse=True)
            return [r[1] for r in results[:k]]
        except Exception:
            return []

    def close(self) -> None:
        """Close the database connection."""
        try:
            if self._conn:
                self._conn.close()
        except Exception:
            pass
        self._conn = None

    def __del__(self) -> None:
        """Ensure connection is closed on garbage collection."""
        self.close()
