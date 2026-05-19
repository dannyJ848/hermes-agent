#!/usr/bin/env python3
"""
Knowledge Graph — Structured relationship memory.

Nodes: concept, tool, error, solution, session, skill
Edges: causes, solved_by, related_to, used_in, produces, depends_on
"""

import sqlite3
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

HERMES_HOME = Path.home() / ".hermes"
DB_PATH = HERMES_HOME / "knowledge_graph.db"


def _safe(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            print(f"[knowledge_graph] {fn.__name__} failed: {e}")
            if fn.__name__.startswith("query_") or fn.__name__.startswith("get_") or fn.__name__.startswith("find_"):
                return []
            return None
    return wrapper


class KnowledgeGraph:
    """Structured knowledge graph for concepts, tools, errors, and solutions."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._ensure_db()

    def _ensure_db(self):
        try:
            HERMES_HOME.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_type TEXT NOT NULL,
                    label TEXT NOT NULL,
                    properties TEXT,
                    embedding BLOB,
                    created_at REAL DEFAULT (julianday('now'))
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER NOT NULL,
                    target_id INTEGER NOT NULL,
                    relation_type TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    properties TEXT,
                    created_at REAL DEFAULT (julianday('now'))
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_label ON nodes(label)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_relation ON edges(relation_type)')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[knowledge_graph] DB init failed: {e}")

    @_safe
    def add_node(self, node_type: str, label: str, properties: Optional[Dict] = None) -> int:
        """Add a node. Returns node ID."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        # Check for existing
        cursor.execute("SELECT id FROM nodes WHERE node_type = ? AND label = ?", (node_type, label))
        row = cursor.fetchone()
        if row:
            node_id = row[0]
            # Update properties
            if properties:
                cursor.execute("UPDATE nodes SET properties = ? WHERE id = ?",
                              (json.dumps(properties), node_id))
                conn.commit()
            conn.close()
            return node_id
        cursor.execute('''
            INSERT INTO nodes (node_type, label, properties)
            VALUES (?, ?, ?)
        ''', (node_type, label, json.dumps(properties) if properties else None))
        node_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return node_id

    @_safe
    def add_edge(self, source_id: int, relation_type: str, target_id: int,
                 weight: float = 1.0, properties: Optional[Dict] = None) -> int:
        """Add an edge between nodes."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        # Check for existing
        cursor.execute('''
            SELECT id FROM edges WHERE source_id = ? AND target_id = ? AND relation_type = ?
        ''', (source_id, target_id, relation_type))
        row = cursor.fetchone()
        if row:
            edge_id = row[0]
            # Update weight
            cursor.execute("UPDATE edges SET weight = MAX(weight, ?) WHERE id = ?",
                          (weight, edge_id))
            conn.commit()
            conn.close()
            return edge_id
        cursor.execute('''
            INSERT INTO edges (source_id, target_id, relation_type, weight, properties)
            VALUES (?, ?, ?, ?, ?)
        ''', (source_id, target_id, relation_type, weight,
              json.dumps(properties) if properties else None))
        edge_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return edge_id

    @_safe
    def get_node(self, node_id: int) -> Optional[Dict]:
        """Get node by ID."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @_safe
    def find_node(self, node_type: Optional[str] = None, label: Optional[str] = None) -> List[Dict]:
        """Find nodes by type and/or label."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM nodes WHERE 1=1"
        params = []
        if node_type:
            query += " AND node_type = ?"
            params.append(node_type)
        if label:
            query += " AND label LIKE ?"
            params.append(f"%{label}%")
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @_safe
    def query_neighbors(self, node_id: int, relation_type: Optional[str] = None,
                        direction: str = "both") -> List[Dict]:
        """Get neighbors of a node."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        results = []
        if direction in ("out", "both"):
            query = "SELECT e.*, n.label as target_label, n.node_type as target_type FROM edges e JOIN nodes n ON e.target_id = n.id WHERE e.source_id = ?"
            params = [node_id]
            if relation_type:
                query += " AND e.relation_type = ?"
                params.append(relation_type)
            cursor.execute(query, params)
            results.extend([dict(r) for r in cursor.fetchall()])
        if direction in ("in", "both"):
            query = "SELECT e.*, n.label as source_label, n.node_type as source_type FROM edges e JOIN nodes n ON e.source_id = n.id WHERE e.target_id = ?"
            params = [node_id]
            if relation_type:
                query += " AND e.relation_type = ?"
                params.append(relation_type)
            cursor.execute(query, params)
            results.extend([dict(r) for r in cursor.fetchall()])
        conn.close()
        return results

    @_safe
    def query_causes(self, concept_label: str) -> List[str]:
        """What causes this concept/error?"""
        nodes = self.find_node(label=concept_label)
        if not nodes:
            return []
        causes = []
        for node in nodes:
            neighbors = self.query_neighbors(node["id"], relation_type="causes", direction="in")
            for n in neighbors:
                causes.append(n.get("source_label", "unknown"))
        return causes

    @_safe
    def query_solutions(self, problem_label: str) -> List[str]:
        """What solves this problem?"""
        nodes = self.find_node(label=problem_label)
        if not nodes:
            return []
        solutions = []
        for node in nodes:
            neighbors = self.query_neighbors(node["id"], relation_type="solved_by", direction="out")
            for n in neighbors:
                solutions.append(n.get("target_label", "unknown"))
        return solutions

    @_safe
    def query_related(self, label: str, node_type: Optional[str] = None) -> List[str]:
        """What relates to this?"""
        nodes = self.find_node(label=label)
        if not nodes:
            return []
        related = []
        for node in nodes:
            neighbors = self.query_neighbors(node["id"], relation_type="related_to")
            for n in neighbors:
                lbl = n.get("target_label") or n.get("source_label")
                if lbl and lbl != label:
                    related.append(lbl)
        return related

    @_safe
    def query_path(self, from_label: str, to_label: str, max_depth: int = 3) -> Optional[List[Dict]]:
        """Find path between two nodes (BFS)."""
        from_nodes = self.find_node(label=from_label)
        to_nodes = self.find_node(label=to_label)
        if not from_nodes or not to_nodes:
            return None
        start_id = from_nodes[0]["id"]
        target_id = to_nodes[0]["id"]
        # BFS
        visited = {start_id}
        queue = [(start_id, [])]
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        while queue:
            current_id, path = queue.pop(0)
            if current_id == target_id:
                conn.close()
                return path
            if len(path) >= max_depth:
                continue
            cursor.execute('''
                SELECT e.*, n.label, n.node_type FROM edges e
                JOIN nodes n ON e.target_id = n.id
                WHERE e.source_id = ?
                UNION
                SELECT e.*, n.label, n.node_type FROM edges e
                JOIN nodes n ON e.source_id = n.id
                WHERE e.target_id = ?
            ''', (current_id, current_id))
            for row in cursor.fetchall():
                next_id = row["target_id"] if row["source_id"] == current_id else row["source_id"]
                if next_id not in visited:
                    visited.add(next_id)
                    new_path = path + [dict(row)]
                    queue.append((next_id, new_path))
        conn.close()
        return None

    @_safe
    def get_stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM nodes")
        node_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM edges")
        edge_count = cursor.fetchone()[0]
        cursor.execute("SELECT node_type, COUNT(*) FROM nodes GROUP BY node_type")
        type_counts = {r[0]: r[1] for r in cursor.fetchall()}
        conn.close()
        return {"nodes": node_count, "edges": edge_count, "by_type": type_counts}


# Singleton
_kg_instance = None

def get_knowledge_graph() -> KnowledgeGraph:
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = KnowledgeGraph()
    return _kg_instance
