"""
cortex_access.py — Unified access layer for the Cortex database.
Single entry point for ALL training gym operations.
Replaces scattered SQLite/Postgres access.

Usage:
    from cortex_access import CortexDB
    db = CortexDB()
    tips = db.get_tips_for_eval(domain='terminal', limit=50)
    stats = db.get_stats()
"""

import os
import hashlib
import json
import time
import uuid
import random
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

# Try to import psycopg2, fallback to sqlite if not available
try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    import sqlite3

# Load config
_config_path = Path.home() / ".hermes" / "hindsight" / "config.json"
if _config_path.exists():
    _cfg = json.loads(_config_path.read_text())
else:
    _cfg = {}

# DSN priority: env var > config file > default
CORTEX_DSN = os.environ.get("CORTEX_DSN", _cfg.get("cortex_dsn", "postgresql://hindsight:hindsight@localhost:5432/hindsight"))

# Also support SQLite fallback
CORTEX_SQLITE = str(Path.home() / ".hermes" / "cortex.db")


@contextmanager
def cortex_cursor(commit=True, dsn=None):
    """Get a database cursor. Uses Postgres if available, else SQLite."""
    if HAS_PSYCOPG2:
        conn = psycopg2.connect(dsn or CORTEX_DSN)
        conn.autocommit = False
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            yield cur
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
    else:
        # SQLite fallback
        conn = sqlite3.connect(CORTEX_SQLITE)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            yield cur
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()


def _compute_md5(text: str) -> str:
    """Compute MD5 hash of text for deduplication."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def _generate_embedding(text: str, dim: int = 384) -> list:
    """Generate a deterministic pseudo-embedding using seeded PRNG.
    
    This is a fallback when sentence-transformers is not available.
    For production, use BAAI/bge-small-en-v1.5 or similar.
    """
    seed = int(hashlib.sha256(text.encode()).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)
    vec = [rng.uniform(-1, 1) for _ in range(dim)]
    # Normalize
    norm = sum(x**2 for x in vec) ** 0.5
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def _format_vector_for_pg(vec: list) -> str:
    """Format a vector as PostgreSQL vector literal."""
    return '[' + ','.join(f'{v:.6f}' for v in vec) + ']'


class CortexDB:
    """Unified database access for the Cortex system."""
    
    def __init__(self, dsn: Optional[str] = None):
        self.dsn = dsn or CORTEX_DSN
        self._has_pg = HAS_PSYCOPG2
        
    # ========================================================================
    # NODE OPERATIONS
    # ========================================================================
    
    def insert_node(self, text: str, node_type: str = "tip", domain: str = "general",
                    confidence: float = 0.5, elo: float = 1200.0, 
                    tip_type: Optional[str] = None, condition: Optional[str] = None,
                    recommendation: Optional[str] = None, rationale: Optional[str] = None,
                    tool_name: Optional[str] = None, provenance: Optional[str] = None,
                    source_ids: Optional[Dict] = None, metadata: Optional[Dict] = None,
                    embedding: Optional[list] = None) -> Optional[int]:
        """Insert a new node into cortex_nodes. Returns the new node ID."""
        
        md5 = _compute_md5(text)
        
        # Generate embedding if not provided
        if embedding is None:
            embedding = _generate_embedding(text)
        
        vec_str = _format_vector_for_pg(embedding) if self._has_pg else json.dumps(embedding)
        source_ids_json = json.dumps(source_ids or {})
        
        # Merge tip fields into metadata (cortex_nodes schema doesn't have dedicated columns)
        meta = metadata or {}
        if tip_type: meta["tip_type"] = tip_type
        if condition: meta["condition"] = condition
        if recommendation: meta["recommendation"] = recommendation
        if rationale: meta["rationale"] = rationale
        if tool_name: meta["tool_name"] = tool_name
        metadata_json = json.dumps(meta)
        
        now = time.time()
        
        try:
            with cortex_cursor(dsn=self.dsn) as cur:
                if self._has_pg:
                    cur.execute("""
                        INSERT INTO cortex_nodes 
                        (node_type, text, domain, confidence, elo, 
                         provenance, source_ids, metadata, content_md5, embedding,
                         created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector, NOW(), NOW())
                        ON CONFLICT (content_md5) DO NOTHING
                        RETURNING id
                    """, (node_type, text, domain, confidence, elo,
                          provenance, source_ids_json, metadata_json, md5, vec_str))
                else:
                    cur.execute("""
                        INSERT OR IGNORE INTO cortex_nodes 
                        (node_type, text, domain, confidence, elo,
                         provenance, source_ids, metadata, content_md5, embedding,
                         created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (node_type, text, domain, confidence, elo,
                          provenance, source_ids_json, metadata_json, md5, vec_str,
                          now, now))
                
                result = cur.fetchone()
                if result:
                    return result['id'] if self._has_pg else result[0]
                return None
        except Exception as e:
            # Only log non-duplicate-key errors
            if "duplicate" not in str(e).lower() and "unique" not in str(e).lower():
                print(f"CortexDB.insert_node error: {e}")
            return None
    
    def get_node(self, node_id: int) -> Optional[Dict]:
        """Get a single node by ID."""
        with cortex_cursor(dsn=self.dsn) as cur:
            if self._has_pg:
                cur.execute("SELECT * FROM cortex_nodes WHERE id = %s", (node_id,))
            else:
                cur.execute("SELECT * FROM cortex_nodes WHERE id = ?", (node_id,))
            result = cur.fetchone()
            return dict(result) if result else None
    
    def get_tips_for_eval(self, domain: Optional[str] = None, 
                          min_elo: float = 1000, limit: int = 100) -> List[Dict]:
        """Get tips that need evaluation (low matches or unrated)."""
        with cortex_cursor(dsn=self.dsn) as cur:
            if domain:
                if self._has_pg:
                    cur.execute("""
                        SELECT * FROM cortex_nodes 
                        WHERE node_type = 'tip' AND is_active = TRUE 
                          AND elo >= %s
                          AND (domain ILIKE %s OR tip_type ILIKE %s)
                        ORDER BY elo_matches ASC, created_at DESC
                        LIMIT %s
                    """, (min_elo, f'%{domain}%', f'%{domain}%', limit))
                else:
                    cur.execute("""
                        SELECT * FROM cortex_nodes 
                        WHERE node_type = 'tip' AND is_active = TRUE 
                          AND elo >= ?
                          AND (domain LIKE ? OR tip_type LIKE ?)
                        ORDER BY elo_matches ASC, created_at DESC
                        LIMIT ?
                    """, (min_elo, f'%{domain}%', f'%{domain}%', limit))
            else:
                if self._has_pg:
                    cur.execute("""
                        SELECT * FROM cortex_nodes 
                        WHERE node_type = 'tip' AND is_active = TRUE 
                          AND elo >= %s
                        ORDER BY elo_matches ASC, created_at DESC
                        LIMIT %s
                    """, (min_elo, limit))
                else:
                    cur.execute("""
                        SELECT * FROM cortex_nodes 
                        WHERE node_type = 'tip' AND is_active = TRUE 
                          AND elo >= ?
                        ORDER BY elo_matches ASC, created_at DESC
                        LIMIT ?
                    """, (min_elo, limit))
            
            return [dict(row) for row in cur.fetchall()]
    
    def update_elo(self, node_id: int, new_elo: float, won: bool = True) -> bool:
        """Update Elo rating and match count for a node."""
        with cortex_cursor(dsn=self.dsn) as cur:
            if self._has_pg:
                cur.execute("""
                    UPDATE cortex_nodes 
                    SET elo = %s, 
                        elo_matches = elo_matches + 1,
                        last_evaluated = NOW()
                    WHERE id = %s
                """, (new_elo, node_id))
            else:
                cur.execute("""
                    UPDATE cortex_nodes 
                    SET elo = ?, 
                        elo_matches = elo_matches + 1,
                        last_evaluated = ?
                    WHERE id = ?
                """, (new_elo, time.time(), node_id))
            return cur.rowcount > 0
    
    def upvote_tip(self, node_id: int) -> bool:
        """Upvote a tip."""
        with cortex_cursor(dsn=self.dsn) as cur:
            if self._has_pg:
                cur.execute("UPDATE cortex_nodes SET upvotes = upvotes + 1, frequency = frequency + 1, last_seen = NOW() WHERE id = %s", (node_id,))
            else:
                cur.execute("UPDATE cortex_nodes SET upvotes = upvotes + 1, frequency = frequency + 1, last_seen = ? WHERE id = ?", (time.time(), node_id))
            return cur.rowcount > 0
    
    def downvote_tip(self, node_id: int) -> bool:
        """Downvote a tip."""
        with cortex_cursor(dsn=self.dsn) as cur:
            if self._has_pg:
                cur.execute("UPDATE cortex_nodes SET downvotes = downvotes + 1, last_seen = NOW() WHERE id = %s", (node_id,))
            else:
                cur.execute("UPDATE cortex_nodes SET downvotes = downvotes + 1, last_seen = ? WHERE id = ?", (time.time(), node_id))
            return cur.rowcount > 0
    
    def deactivate_node(self, node_id: int, reason: str = "") -> bool:
        """Soft-delete a node."""
        with cortex_cursor(dsn=self.dsn) as cur:
            if self._has_pg:
                cur.execute("""
                    UPDATE cortex_nodes 
                    SET is_active = FALSE, 
                        metadata = metadata || jsonb_build_object('deactivation_reason', %s, 'deactivated_at', NOW())
                    WHERE id = %s
                """, (reason, node_id))
            else:
                cur.execute("""
                    UPDATE cortex_nodes 
                    SET is_active = FALSE
                    WHERE id = ?
                """, (node_id,))
            return cur.rowcount > 0
    
    def touch_node(self, node_id) -> bool:
        """Touch a node to update last_seen and frequency."""
        try:
            node_id = int(node_id)
        except (ValueError, TypeError):
            return False
        with cortex_cursor(dsn=self.dsn) as cur:
            if self._has_pg:
                cur.execute("""
                    UPDATE cortex_nodes 
                    SET frequency = frequency + 1, last_seen = NOW()
                    WHERE id = %s
                """, (node_id,))
            else:
                cur.execute("""
                    UPDATE cortex_nodes 
                    SET frequency = frequency + 1, last_seen = ?
                    WHERE id = ?
                """, (time.time(), node_id))
            return cur.rowcount > 0
    
    # ========================================================================
    # SEARCH OPERATIONS
    # ========================================================================
    
    def search_text(self, query: str, node_type: Optional[str] = None, 
                    limit: int = 10) -> List[Dict]:
        """Full-text search across nodes."""
        with cortex_cursor(dsn=self.dsn) as cur:
            if self._has_pg:
                if node_type:
                    cur.execute("""
                        SELECT *, ts_rank(to_tsvector('english', text), plainto_tsquery('english', %s)) as rank
                        FROM cortex_nodes
                        WHERE is_active = TRUE AND node_type = %s
                          AND to_tsvector('english', text) @@ plainto_tsquery('english', %s)
                        ORDER BY rank DESC, elo DESC
                        LIMIT %s
                    """, (query, node_type, query, limit))
                else:
                    cur.execute("""
                        SELECT *, ts_rank(to_tsvector('english', text), plainto_tsquery('english', %s)) as rank
                        FROM cortex_nodes
                        WHERE is_active = TRUE
                          AND to_tsvector('english', text) @@ plainto_tsquery('english', %s)
                        ORDER BY rank DESC, elo DESC
                        LIMIT %s
                    """, (query, query, limit))
            else:
                # SQLite fallback - simple LIKE search
                if node_type:
                    cur.execute("""
                        SELECT * FROM cortex_nodes
                        WHERE is_active = TRUE AND node_type = ?
                          AND text LIKE ?
                        ORDER BY elo DESC
                        LIMIT ?
                    """, (node_type, f'%{query}%', limit))
                else:
                    cur.execute("""
                        SELECT * FROM cortex_nodes
                        WHERE is_active = TRUE AND text LIKE ?
                        ORDER BY elo DESC
                        LIMIT ?
                    """, (f'%{query}%', limit))
            
            return [dict(row) for row in cur.fetchall()]
    
    def search_similar(self, text: str, node_type: str = "tip", 
                       limit: int = 10) -> List[Dict]:
        """Find semantically similar nodes using vector similarity."""
        embedding = _generate_embedding(text)
        vec_str = _format_vector_for_pg(embedding)
        
        with cortex_cursor(dsn=self.dsn) as cur:
            if self._has_pg:
                cur.execute("""
                    SELECT *, embedding <=> %s::vector as distance
                    FROM cortex_nodes
                    WHERE is_active = TRUE AND node_type = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (vec_str, node_type, vec_str, limit))
            else:
                # SQLite can't do vector similarity, fall back to text search
                return self.search_text(text, node_type, limit)
            
            return [dict(row) for row in cur.fetchall()]
    
    # ========================================================================
    # EVALUATION OPERATIONS
    # ========================================================================
    
    def record_eval(self, node_a_id: int, node_b_id: int, winner: str,
                    judge_type: str = "heuristic", confidence: float = 0.5,
                    reasoning: str = "", cycle_id: Optional[str] = None) -> bool:
        """Record an evaluation result."""
        # Map winner string to actual node UUID
        winner_id = str(node_a_id) if winner == 'a' else (str(node_b_id) if winner == 'b' else None)
        with cortex_cursor(dsn=self.dsn) as cur:
            if self._has_pg:
                # Use cycle_id as round_id (same semantic, different column name in schema)
                cur.execute("""
                    INSERT INTO cortex_eval_history 
                    (node_id_a, node_id_b, winner_id, judge_id, judge_axis, margin, domain)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (str(node_a_id), str(node_b_id), winner_id, judge_type, 'elo', int(confidence * 100), 'general'))
            else:
                cur.execute("""
                    INSERT INTO cortex_eval_history 
                    (node_id_a, node_id_b, winner_id, judge_id, judge_axis, margin, domain)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (str(node_a_id), str(node_b_id), winner_id, judge_type, 'elo', int(confidence * 100), 'general'))
            return True
    
    # ========================================================================
    # FLYWHEEL OPERATIONS
    # ========================================================================
    
    def start_flywheel_cycle(self, cycle_type: str) -> str:
        """Start a new flywheel cycle. Returns cycle_id."""
        cycle_id = str(uuid.uuid4())
        
        with cortex_cursor(dsn=self.dsn) as cur:
            if self._has_pg:
                cur.execute("""
                    INSERT INTO cortex_flywheel (cycle_id, cycle_type, status, started_at)
                    VALUES (%s, %s, 'running', NOW())
                """, (cycle_id, cycle_type))
            else:
                cur.execute("""
                    INSERT INTO cortex_flywheel (cycle_id, cycle_type, status, started_at)
                    VALUES (?, ?, 'running', ?)
                """, (cycle_id, cycle_type, time.time()))
        
        return cycle_id
    
    def complete_flywheel_cycle(self, cycle_id: str, status: str = "completed",
                                 pairs_evaluated: int = 0, tips_repaired: int = 0,
                                 tips_consolidated: int = 0, duration_ms: int = 0) -> bool:
        """Complete a flywheel cycle."""
        with cortex_cursor(dsn=self.dsn) as cur:
            if self._has_pg:
                cur.execute("""
                    UPDATE cortex_flywheel 
                    SET status = %s, 
                        pairs_evaluated = %s,
                        tips_repaired = %s,
                        tips_consolidated = %s,
                        duration_ms = %s,
                        completed_at = NOW()
                    WHERE cycle_id = %s
                """, (status, pairs_evaluated, tips_repaired, tips_consolidated, duration_ms, cycle_id))
            else:
                cur.execute("""
                    UPDATE cortex_flywheel 
                    SET status = ?, 
                        pairs_evaluated = ?,
                        tips_repaired = ?,
                        tips_consolidated = ?,
                        duration_ms = ?,
                        completed_at = ?
                    WHERE cycle_id = ?
                """, (status, pairs_evaluated, tips_repaired, tips_consolidated, duration_ms, time.time(), cycle_id))
            return cur.rowcount > 0
    
    # ========================================================================
    # STATS
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}
        
        with cortex_cursor(dsn=self.dsn) as cur:
            # Total nodes
            if self._has_pg:
                cur.execute("SELECT COUNT(*) as count FROM cortex_nodes")
            else:
                cur.execute("SELECT COUNT(*) as count FROM cortex_nodes")
            stats['total_nodes'] = cur.fetchone()['count'] if self._has_pg else cur.fetchone()[0]
            
            # Tips
            if self._has_pg:
                cur.execute("SELECT COUNT(*) as count FROM cortex_nodes WHERE node_type = 'tip'")
            else:
                cur.execute("SELECT COUNT(*) as count FROM cortex_nodes WHERE node_type = 'tip'")
            stats['total_tips'] = cur.fetchone()['count'] if self._has_pg else cur.fetchone()[0]
            
            # Active tips
            if self._has_pg:
                cur.execute("SELECT COUNT(*) as count FROM cortex_nodes WHERE node_type = 'tip' AND is_active = TRUE")
            else:
                cur.execute("SELECT COUNT(*) as count FROM cortex_nodes WHERE node_type = 'tip' AND is_active = TRUE")
            stats['active_tips'] = cur.fetchone()['count'] if self._has_pg else cur.fetchone()[0]
            
            # Elo stats
            if self._has_pg:
                cur.execute("""
                    SELECT AVG(elo) as avg_elo, MIN(elo) as min_elo, MAX(elo) as max_elo,
                           STDDEV(elo) as std_elo
                    FROM cortex_nodes WHERE node_type = 'tip' AND is_active = TRUE
                """)
            else:
                cur.execute("""
                    SELECT AVG(elo) as avg_elo, MIN(elo) as min_elo, MAX(elo) as max_elo
                    FROM cortex_nodes WHERE node_type = 'tip' AND is_active = TRUE
                """)
            row = cur.fetchone()
            if self._has_pg:
                stats['elo_avg'] = float(row['avg_elo']) if row['avg_elo'] else 1200
                stats['elo_min'] = float(row['min_elo']) if row['min_elo'] else 1200
                stats['elo_max'] = float(row['max_elo']) if row['max_elo'] else 1200
                stats['elo_std'] = float(row['std_elo']) if row['std_elo'] else 0
            else:
                stats['elo_avg'] = row[0] if row[0] else 1200
                stats['elo_min'] = row[1] if row[1] else 1200
                stats['elo_max'] = row[2] if row[2] else 1200
                stats['elo_std'] = 0
            
            # Domain distribution
            if self._has_pg:
                cur.execute("""
                    SELECT domain, COUNT(*) as count 
                    FROM cortex_nodes 
                    WHERE node_type = 'tip' AND is_active = TRUE
                    GROUP BY domain 
                    ORDER BY count DESC
                """)
            else:
                cur.execute("""
                    SELECT domain, COUNT(*) as count 
                    FROM cortex_nodes 
                    WHERE node_type = 'tip' AND is_active = TRUE
                    GROUP BY domain 
                    ORDER BY count DESC
                """)
            stats['domains'] = {row['domain'] if self._has_pg else row[0]: 
                               row['count'] if self._has_pg else row[1] 
                               for row in cur.fetchall()}
            
            # Edges
            if self._has_pg:
                cur.execute("SELECT COUNT(*) as count FROM cortex_edges")
            else:
                cur.execute("SELECT COUNT(*) as count FROM cortex_edges")
            stats['total_edges'] = cur.fetchone()['count'] if self._has_pg else cur.fetchone()[0]
            
            # Evaluations
            if self._has_pg:
                cur.execute("SELECT COUNT(*) as count FROM cortex_eval_history")
            else:
                cur.execute("SELECT COUNT(*) as count FROM cortex_eval_history")
            stats['total_evals'] = cur.fetchone()['count'] if self._has_pg else cur.fetchone()[0]
        
        return stats
    
    def get_tip_quality_report(self) -> Dict[str, Any]:
        """Get a quality report on tips."""
        report = {}
        
        with cortex_cursor(dsn=self.dsn) as cur:
            # Tier distribution
            if self._has_pg:
                cur.execute("""
                    SELECT 
                        CASE 
                            WHEN elo >= 1300 THEN 'excellent'
                            WHEN elo >= 1100 THEN 'average'
                            ELSE 'poor'
                        END as tier,
                        COUNT(*) as count
                    FROM cortex_nodes
                    WHERE node_type = 'tip' AND is_active = TRUE
                    GROUP BY tier
                """)
            else:
                cur.execute("""
                    SELECT 
                        CASE 
                            WHEN elo >= 1300 THEN 'excellent'
                            WHEN elo >= 1100 THEN 'average'
                            ELSE 'poor'
                        END as tier,
                        COUNT(*) as count
                    FROM cortex_nodes
                    WHERE node_type = 'tip' AND is_active = TRUE
                    GROUP BY tier
                """)
            report['tiers'] = {row['tier'] if self._has_pg else row[0]: 
                              row['count'] if self._has_pg else row[1] 
                              for row in cur.fetchall()}
            
            # Unrated tips
            if self._has_pg:
                cur.execute("""
                    SELECT COUNT(*) as count FROM cortex_nodes
                    WHERE node_type = 'tip' AND is_active = TRUE AND elo_matches = 0
                """)
            else:
                cur.execute("""
                    SELECT COUNT(*) as count FROM cortex_nodes
                    WHERE node_type = 'tip' AND is_active = TRUE AND elo_matches = 0
                """)
            report['unrated'] = cur.fetchone()['count'] if self._has_pg else cur.fetchone()[0]
            
            # Low-elo tips needing repair
            if self._has_pg:
                cur.execute("""
                    SELECT COUNT(*) as count FROM cortex_nodes
                    WHERE node_type = 'tip' AND is_active = TRUE 
                      AND elo < 1050 AND elo_matches >= 8
                """)
            else:
                cur.execute("""
                    SELECT COUNT(*) as count FROM cortex_nodes
                    WHERE node_type = 'tip' AND is_active = TRUE 
                      AND elo < 1050 AND elo_matches >= 8
                """)
            report['needs_repair'] = cur.fetchone()['count'] if self._has_pg else cur.fetchone()[0]
        
        return report


# Backward compatibility: get_db() for plugin integration
def get_db() -> CortexDB:
    """Get or create CortexDB singleton. Used by distillation plugin."""
    return CortexDB()


# ========================================================================
# SELF-TEST
# ========================================================================

if __name__ == "__main__":
    print("Testing CortexDB...")
    db = CortexDB()
    
    # Test insert
    node_id = db.insert_node(
        text="WHEN testing CortexDB, DO verify all operations work correctly.",
        node_type="tip",
        domain="testing",
        confidence=0.9,
        tip_type="strategy",
        metadata={"round": "test", "source": "self_test"}
    )
    print(f"Inserted node: {node_id}")
    
    # Test get
    if node_id:
        node = db.get_node(node_id)
        print(f"Retrieved: {node['text'][:50]}...")
    
    # Test stats
    stats = db.get_stats()
    print(f"Stats: {stats}")
    
    # Test search
    results = db.search_text("testing")
    print(f"Search found {len(results)} results")
    
    print("CortexDB test complete!")
