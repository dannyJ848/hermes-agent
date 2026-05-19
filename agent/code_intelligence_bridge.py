import sqlite3
from pathlib import Path
from typing import List, Dict


class CodeIntelligenceBridge:
    """Bridge to the code intelligence SQLite database."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path.home() / ".hermes" / "code_intelligence.db")
        self.db_path = db_path

    def get_relevant_code(self, query: str) -> List[Dict]:
        """Search flow_nodes and code_chunks tables for relevant code.

        Args:
            query: Search term to look for in code intelligence tables.

        Returns:
            Top 5 matching results with file_path, chunk_text, node_name.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        like_pattern = f"%{query}%"

        # Search flow_nodes (name, description)
        cursor.execute(
            """
            SELECT name AS node_name, description AS chunk_text, NULL AS file_path
            FROM flow_nodes
            WHERE name LIKE ? OR description LIKE ?
            """,
            (like_pattern, like_pattern),
        )
        flow_results = cursor.fetchall()

        # Search code_chunks (file_path, chunk_text)
        cursor.execute(
            """
            SELECT file_path, chunk_text, NULL AS node_name
            FROM code_chunks
            WHERE file_path LIKE ? OR chunk_text LIKE ?
            """,
            (like_pattern, like_pattern),
        )
        chunk_results = cursor.fetchall()

        conn.close()

        # Combine and format results
        results = []
        for row in flow_results:
            results.append({
                "file_path": row["file_path"],
                "chunk_text": row["chunk_text"],
                "node_name": row["node_name"],
            })
        for row in chunk_results:
            results.append({
                "file_path": row["file_path"],
                "chunk_text": row["chunk_text"],
                "node_name": row["node_name"],
            })

        # Return top 5
        return results[:5]
