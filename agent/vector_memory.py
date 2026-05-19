"""Vector memory module with SQLite backend and sentence-transformers embeddings."""

from __future__ import annotations

import json
import sqlite3
import time
import difflib
from pathlib import Path
from typing import Any


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorMemory:
    """SQLite-backed vector memory using sentence-transformers or difflib fallback."""

    def __init__(self, db_path: str | Path = "memory.db") -> None:
        self.db_path = Path(db_path)
        self._conn = sqlite3.connect(str(self.db_path))
        self._init_db()
        self._encoder = None
        try:
            from sentence_transformers import SentenceTransformer

            self._encoder = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            self._encoder = None

    def _init_db(self) -> None:
        """Create the memories table if it doesn't exist."""
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

    def add_memory(self, text: str, metadata: dict[str, Any] | None = None) -> int:
        """Add a memory and return its id."""
        embedding_json: str | None = None
        if self._encoder is not None:
            embedding = self._encoder.encode(text).tolist()
            embedding_json = json.dumps(embedding)
        metadata_json = json.dumps(metadata) if metadata else None
        timestamp = time.time()
        with self._conn:
            cur = self._conn.execute(
                """
                INSERT INTO memories (text, embedding_json, metadata_json, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (text, embedding_json, metadata_json, timestamp),
            )
            return int(cur.lastrowid)

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """Search memories by cosine similarity or difflib fallback."""
        rows = self._conn.execute(
            "SELECT id, text, embedding_json, metadata_json, timestamp FROM memories"
        ).fetchall()

        if not rows:
            return []

        results: list[tuple[float, dict[str, Any]]] = []

        if self._encoder is not None:
            query_embedding = self._encoder.encode(query).tolist()
            for row in rows:
                row_id, text, embedding_json, metadata_json, timestamp = row
                if embedding_json:
                    embedding = json.loads(embedding_json)
                    score = _cosine_similarity(query_embedding, embedding)
                else:
                    score = 0.0
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
        else:
            for row in rows:
                row_id, text, _embedding_json, metadata_json, timestamp = row
                score = difflib.SequenceMatcher(None, query.lower(), text.lower()).ratio()
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

        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:k]]

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def __del__(self) -> None:
        """Ensure connection is closed on garbage collection."""
        try:
            self._conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        vm = VectorMemory(Path(tmpdir) / "test.db")
        vm.add_memory("The quick brown fox jumps over the lazy dog.", {"tag": "pangram"})
        vm.add_memory("Python is a versatile programming language.", {"tag": "tech"})
        vm.add_memory("Machine learning models require training data.", {"tag": "ml"})
        results = vm.search("programming language", k=2)
        print(f"Found {len(results)} results")
        for r in results:
            print(f"  id={r['id']} score={r['score']:.4f} text={r['text']!r}")
        vm.close()
