#!/usr/bin/env python3
"""
Unified Cortex Database Architecture
=====================================
Merges: cerebrum SQLite + Hindsight Postgres + 72 subconscious DBs
Into: Single PostgreSQL database 'cortex' with pgvector

Design Principles:
1. ONE database, ONE connection, ONE truth
2. Postgres for durability, pgvector for embeddings
3. Preserve ALL existing data during migration
4. Backward-compatible access layer
5. Self-sustaining autonomous flywheel built in
"""

# ============================================================
# SCHEMA DESIGN
# ============================================================

SCHEMA_SQL = """
-- ============================================================
-- EXTENSIONS
-- ============================================================
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- fuzzy text search
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- SCHEMA: cortex (unified namespace)
-- ============================================================
-- We use the public schema but with a cortex_ prefix for clarity

-- ============================================================
-- CORE: KNOWLEDGE NODES (replaces memory_units + kg_nodes)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_nodes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Content
    text            TEXT NOT NULL,
    node_type       TEXT NOT NULL,  -- 'tip', 'experience', 'fact', 'prediction', 'entity', 'concept', 'research', 'tool_concept'
    domain          TEXT DEFAULT '',
    
    -- Hierarchy
    parent_id       UUID REFERENCES cortex_nodes(id),
    source_doc_id   UUID,  -- FK to cortex_documents
    
    -- Embedding (pgvector)
    embedding       vector(384),  -- BAAI/bge-small-en-v1.5 dimension
    
    -- Full-text search
    search_vector   tsvector GENERATED ALWAYS AS (to_tsvector('english', coalesce(text, ''))) STORED,
    
    -- Quality signals (unified from Elo + confidence + votes)
    elo             REAL DEFAULT 1200.0,
    elo_matches     INTEGER DEFAULT 0,
    elo_wins        INTEGER DEFAULT 0,
    elo_losses      INTEGER DEFAULT 0,
    confidence      REAL DEFAULT 0.5,
    upvotes         INTEGER DEFAULT 0,
    downvotes       INTEGER DEFAULT 0,
    frequency       INTEGER DEFAULT 1,
    salience        REAL DEFAULT 0.5,
    trust           REAL DEFAULT 0.5,
    
    -- Metadata
    metadata        JSONB DEFAULT '{}',
    tags            TEXT[] DEFAULT '{}',
    source_ids      TEXT DEFAULT '',
    
    -- Timestamps
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    last_accessed   TIMESTAMPTZ DEFAULT NOW(),
    last_evaluated  TIMESTAMPTZ,
    last_consolidated TIMESTAMPTZ,
    
    -- Lifecycle
    access_count    INTEGER DEFAULT 0,
    consolidation_count INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    provenance      TEXT DEFAULT ''  -- where this node came from
);

CREATE INDEX IF NOT EXISTS idx_nodes_type ON cortex_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_nodes_domain ON cortex_nodes(domain);
CREATE INDEX IF NOT EXISTS idx_nodes_elo ON cortex_nodes(elo) WHERE is_active;
CREATE INDEX IF NOT EXISTS idx_nodes_active ON cortex_nodes(is_active) WHERE is_active;
CREATE INDEX IF NOT EXISTS idx_nodes_text_trgm ON cortex_nodes USING gin(text gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_nodes_search ON cortex_nodes USING gin(search_vector);
CREATE INDEX IF NOT EXISTS idx_nodes_tags ON cortex_nodes USING gin(tags);

-- ============================================================
-- CORE: EDGES (replaces memory_links + kg_edges)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_edges (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id       UUID NOT NULL REFERENCES cortex_nodes(id) ON DELETE CASCADE,
    target_id       UUID NOT NULL REFERENCES cortex_nodes(id) ON DELETE CASCADE,
    relation        TEXT NOT NULL DEFAULT 'related_to',
    weight          REAL DEFAULT 1.0,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(source_id, target_id, relation)
);

CREATE INDEX IF NOT EXISTS idx_edges_source ON cortex_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON cortex_edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_relation ON cortex_edges(relation);

-- ============================================================
-- CORE: DOCUMENTS (replaces Hindsight documents + knowledge files)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Content
    original_text   TEXT NOT NULL,
    content_hash    TEXT,
    
    -- Classification
    doc_type        TEXT DEFAULT 'generic',  -- 'research', 'tip_batch', 'experience_batch', 'web_page', etc.
    domain          TEXT DEFAULT '',
    source_url      TEXT DEFAULT '',
    
    -- Metadata
    metadata        JSONB DEFAULT '{}',
    tags            TEXT[] DEFAULT '{}',
    
    -- Timestamps
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- CORE: CHUNKS (for RAG retrieval)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_chunks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id     UUID NOT NULL REFERENCES cortex_documents(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    chunk_text      TEXT NOT NULL,
    content_hash    TEXT,
    embedding       vector(384),
    search_vector   tsvector GENERATED ALWAYS AS (to_tsvector('english', coalesce(chunk_text, ''))) STORED,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON cortex_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_search ON cortex_chunks USING gin(search_vector);

-- ============================================================
-- CORE: ENTITIES (replaces Hindsight entities + cerebrum entities)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_entities (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canonical_name  TEXT NOT NULL,
    entity_type     TEXT DEFAULT 'generic',
    metadata        JSONB DEFAULT '{}',
    mention_count   INTEGER DEFAULT 1,
    first_seen      TIMESTAMPTZ DEFAULT NOW(),
    last_seen       TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(canonical_name, entity_type)
);

CREATE INDEX IF NOT EXISTS idx_entities_name ON cortex_entities(canonical_name);
CREATE INDEX IF NOT EXISTS idx_entities_type ON cortex_entities(entity_type);

-- Node-entity junction
CREATE TABLE IF NOT EXISTS cortex_node_entities (
    node_id         UUID NOT NULL REFERENCES cortex_nodes(id) ON DELETE CASCADE,
    entity_id       UUID NOT NULL REFERENCES cortex_entities(id) ON DELETE CASCADE,
    PRIMARY KEY(node_id, entity_id)
);

-- Entity co-occurrence
CREATE TABLE IF NOT EXISTS cortex_entity_cooccurrences (
    entity_id_1     UUID NOT NULL REFERENCES cortex_entities(id) ON DELETE CASCADE,
    entity_id_2     UUID NOT NULL REFERENCES cortex_entities(id) ON DELETE CASCADE,
    cooccurrence_count INTEGER DEFAULT 1,
    last_cooccurred TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY(entity_id_1, entity_id_2)
);

-- ============================================================
-- TRACKING: TOOL PERFORMANCE (replaces 15+ scattered SQLite tables)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_tool_calls (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      TEXT DEFAULT '',
    tool_name       TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'success',  -- 'success', 'error', 'timeout'
    speed_ms        REAL,
    args_summary    TEXT DEFAULT '',
    error_type      TEXT DEFAULT '',
    error_message   TEXT DEFAULT '',
    confidence      REAL,
    approach        TEXT DEFAULT '',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_toolcalls_tool ON cortex_tool_calls(tool_name);
CREATE INDEX IF NOT EXISTS idx_toolcalls_session ON cortex_tool_calls(session_id);
CREATE INDEX IF NOT EXISTS idx_toolcalls_time ON cortex_tool_calls(created_at);

-- ============================================================
-- TRACKING: PREDICTIONS (replaces cerebrum predictions + metacog)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_predictions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      TEXT DEFAULT '',
    task_type       TEXT DEFAULT '',
    task_summary    TEXT DEFAULT '',
    predicted_difficulty REAL,
    predicted_approach TEXT DEFAULT '',
    predicted_iterations INTEGER,
    predicted_outcome TEXT DEFAULT '',
    confidence      REAL,
    
    actual_difficulty REAL,
    actual_iterations INTEGER,
    actual_outcome   TEXT DEFAULT '',
    actual_approach  TEXT DEFAULT '',
    difficulty_error REAL,
    outcome_error   INTEGER,
    
    resolved        BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ
);

-- ============================================================
-- TRACKING: SELF-DEBUG (replaces self_debug_sessions)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_debug_sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      TEXT DEFAULT '',
    file_path       TEXT DEFAULT '',
    language        TEXT DEFAULT '',
    error_type      TEXT DEFAULT '',
    error_message   TEXT DEFAULT '',
    explanation     TEXT DEFAULT '',
    fix_strategy    TEXT DEFAULT '',
    iterations      INTEGER DEFAULT 0,
    success         BOOLEAN DEFAULT FALSE,
    time_to_fix_ms  INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TRACKING: TOKEN USAGE (replaces token_usage + token_tracking)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_token_usage (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      TEXT DEFAULT '',
    tool_name       TEXT DEFAULT '',
    task_type       TEXT DEFAULT '',
    tokens_in       INTEGER DEFAULT 0,
    tokens_out      INTEGER DEFAULT 0,
    speed_ms        REAL,
    success         BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tokenusage_time ON cortex_token_usage(created_at);

-- ============================================================
-- TRACKING: CALIBRATION (replaces calibration_log + speed_trends)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_calibration (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tool_name       TEXT NOT NULL,
    task_type       TEXT DEFAULT '',
    predicted_success REAL,
    actual_success  BOOLEAN,
    prediction_error REAL,
    strategy_used   TEXT DEFAULT '',
    session_id      TEXT DEFAULT '',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TRACKING: CIRCUIT BREAKERS
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_circuit_breakers (
    tool_name       TEXT PRIMARY KEY,
    state           TEXT DEFAULT 'closed',  -- 'closed', 'open', 'half_open'
    failure_count   INTEGER DEFAULT 0,
    success_count   INTEGER DEFAULT 0,
    last_failure    TIMESTAMPTZ,
    last_state_change TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TRACKING: REASONING (replaces reasoning_traces + chains + patterns)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_reasoning (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chain_id        TEXT DEFAULT '',
    session_id      TEXT DEFAULT '',
    task_type       TEXT DEFAULT '',
    task_summary    TEXT DEFAULT '',
    strategy        TEXT DEFAULT '',
    approach        TEXT DEFAULT '',
    outcome         TEXT DEFAULT '',
    iterations_used INTEGER DEFAULT 0,
    total_reward    REAL DEFAULT 0,
    backtrack_count INTEGER DEFAULT 0,
    lessons         TEXT DEFAULT '',
    entities        TEXT DEFAULT '',
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    ended_at        TIMESTAMPTZ
);

-- ============================================================
-- TRACKING: STEP REWARDS (replaces step_rewards)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_step_rewards (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chain_id        TEXT NOT NULL,
    step_num        INTEGER NOT NULL,
    tool_name       TEXT DEFAULT '',
    reward          REAL DEFAULT 0,
    notes           TEXT DEFAULT '',
    is_backtrack    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TRAINING: EVAL HISTORY (new — tracks Elo tournaments)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_eval_history (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    round_id        TEXT NOT NULL,
    node_id_a       UUID NOT NULL REFERENCES cortex_nodes(id),
    node_id_b       UUID NOT NULL REFERENCES cortex_nodes(id),
    winner_id       UUID REFERENCES cortex_nodes(id),
    judge_id        TEXT DEFAULT '',  -- 'phi3', 'llama8b', 'deepseek'
    judge_axis      TEXT DEFAULT '',  -- 'accuracy', 'efficiency', 'completeness'
    margin          REAL DEFAULT 0.5,
    domain          TEXT DEFAULT '',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_eval_round ON cortex_eval_history(round_id);
CREATE INDEX IF NOT EXISTS idx_eval_node ON cortex_eval_history(node_id_a);

-- ============================================================
-- TRAINING: FLYWHEEL STATE (new — tracks autonomous cycles)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_flywheel (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cycle_type      TEXT NOT NULL,  -- 'research', 'distill', 'eval', 'consolidate', 'repair'
    status          TEXT DEFAULT 'running',  -- 'running', 'completed', 'failed'
    domain          TEXT DEFAULT '',
    items_processed INTEGER DEFAULT 0,
    items_produced  INTEGER DEFAULT 0,
    metrics         JSONB DEFAULT '{}',
    error_message   TEXT DEFAULT '',
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

-- ============================================================
-- TRAINING: LIFE EVENTS (replaces life_events)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_life_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type      TEXT NOT NULL,
    title           TEXT DEFAULT '',
    description     TEXT DEFAULT '',
    emotional_valence REAL DEFAULT 0,
    significance    REAL DEFAULT 0.5,
    lessons         TEXT DEFAULT '',
    chapter         TEXT DEFAULT '',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TRAINING: IDENTITY STATE (replaces identity_state + self_model)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_identity (
    key             TEXT PRIMARY KEY,
    value           TEXT NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TRAINING: EPISTEMIC FACTS (replaces epistemic_facts + facts)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_epistemic_facts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content         TEXT NOT NULL UNIQUE,
    formation       TEXT DEFAULT '',
    grounding_type  TEXT DEFAULT '',
    grounding_score REAL DEFAULT 0.5,
    trust_score     REAL DEFAULT 0.5,
    source_url      TEXT DEFAULT '',
    tags            TEXT[] DEFAULT '{}',
    decay_half_life INTEGER DEFAULT 720,  -- hours
    verification_count INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    last_verified   TIMESTAMPTZ
);

-- ============================================================
-- TRAINING: EXPLORATION TASKS (replaces exploration_tasks)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_exploration (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id         TEXT UNIQUE NOT NULL,
    domain          TEXT DEFAULT '',
    description     TEXT DEFAULT '',
    priority        REAL DEFAULT 0.5,
    status          TEXT DEFAULT 'pending',
    outcome         TEXT DEFAULT '',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

-- ============================================================
-- TRAINING: MASTERY (replaces mastery_scores)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_mastery (
    tool_name       TEXT PRIMARY KEY,
    level           TEXT DEFAULT 'novice',
    confidence      REAL DEFAULT 0.3,
    call_count      INTEGER DEFAULT 0,
    success_count   INTEGER DEFAULT 0,
    last_used       TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- MIGRATION: Source tracking (what came from where)
-- ============================================================
CREATE TABLE IF NOT EXISTS cortex_migration_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_db       TEXT NOT NULL,  -- 'cerebrum_sqlite', 'hindsight_pg', 'subconscious_X'
    source_table    TEXT NOT NULL,
    source_id       TEXT NOT NULL,
    target_table    TEXT NOT NULL,
    target_id       UUID NOT NULL,
    migrated_at     TIMESTAMPTZ DEFAULT NOW(),
    verified        BOOLEAN DEFAULT FALSE
);
"""

# ============================================================
# ACCESS LAYER
# ============================================================

ACCESS_LAYER = '''
"""
cortex_access.py — Unified access layer for the Cortex database.
Replaces all scattered SQLite/Postgres access with ONE interface.
"""

import psycopg2
import psycopg2.extras
import json
import time
import uuid
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

# Connection config
CORTEX_DSN = "postgresql://hindsight:hindsight@localhost:5432/cortex"


def get_connection():
    """Get a connection to the Cortex database."""
    return psycopg2.connect(CORTEX_DSN)


@contextmanager
def cortex_cursor(commit=True):
    """Context manager for Cortex DB operations."""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class CortexDB:
    """Unified access to the Cortex knowledge/training database."""
    
    def __init__(self):
        self.dsn = CORTEX_DSN
    
    # ── Node operations ──
    
    def insert_node(self, text: str, node_type: str, domain: str = "",
                    confidence: float = 0.5, metadata: dict = None,
                    tags: list = None, source_ids: str = "",
                    provenance: str = "") -> str:
        """Insert a new knowledge node. Returns UUID."""
        node_id = str(uuid.uuid4())
        with cortex_cursor() as cur:
            cur.execute("""
                INSERT INTO cortex_nodes 
                (id, text, node_type, domain, confidence, metadata, tags,
                 source_ids, provenance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (node_id, text, node_type, domain, confidence,
                  json.dumps(metadata or {}), tags or [],
                  source_ids, provenance))
        return node_id
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        with cortex_cursor(commit=False) as cur:
            cur.execute("SELECT * FROM cortex_nodes WHERE id = %s", (node_id,))
            return cur.fetchone()
    
    def update_elo(self, node_id: str, new_elo: float, won: bool):
        with cortex_cursor() as cur:
            cur.execute("""
                UPDATE cortex_nodes SET
                    elo = %s,
                    elo_matches = elo_matches + 1,
                    elo_wins = elo_wins + %s,
                    elo_losses = elo_losses + %s,
                    last_evaluated = NOW(),
                    updated_at = NOW()
                WHERE id = %s
            """, (new_elo, 1 if won else 0, 0 if won else 1, node_id))
    
    def search_nodes(self, query: str, node_type: str = None,
                     domain: str = None, limit: int = 10) -> List[Dict]:
        """Full-text + metadata search."""
        with cortex_cursor(commit=False) as cur:
            sql = """
                SELECT *, ts_rank(search_vector, plainto_tsquery(%s)) as rank
                FROM cortex_nodes
                WHERE search_vector @@ plainto_tsquery(%s)
                  AND is_active = TRUE
            """
            params = [query, query]
            if node_type:
                sql += " AND node_type = %s"
                params.append(node_type)
            if domain:
                sql += " AND domain = %s"
                params.append(domain)
            sql += " ORDER BY rank DESC, elo DESC LIMIT %s"
            params.append(limit)
            cur.execute(sql, params)
            return cur.fetchall()
    
    def vector_search(self, embedding: list, node_type: str = None,
                      limit: int = 10) -> List[Dict]:
        """Cosine similarity search using pgvector."""
        with cortex_cursor(commit=False) as cur:
            sql = """
                SELECT *, 1 - (embedding <=> %s::vector) as similarity
                FROM cortex_nodes
                WHERE embedding IS NOT NULL AND is_active = TRUE
            """
            params = [str(embedding)]
            if node_type:
                sql += " AND node_type = %s"
                params.append(node_type)
            sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
            params.extend([str(embedding), limit])
            cur.execute(sql, params)
            return cur.fetchall()
    
    def get_tips_for_eval(self, domain: str = None, unrated_only: bool = False,
                          limit: int = 50) -> List[Dict]:
        """Get tips ready for Elo tournament evaluation."""
        with cortex_cursor(commit=False) as cur:
            sql = """
                SELECT * FROM cortex_nodes
                WHERE node_type = 'tip' AND is_active = TRUE
            """
            params = []
            if domain:
                sql += " AND domain LIKE %s"
                params.append(f"%{domain}%")
            if unrated_only:
                sql += " AND elo_matches = 0"
            sql += " ORDER BY RANDOM() LIMIT %s"
            params.append(limit)
            cur.execute(sql, params)
            return cur.fetchall()
    
    def get_low_elo_tips(self, threshold: float = 1150, min_matches: int = 3,
                         limit: int = 20) -> List[Dict]:
        """Get tips that need repair (low Elo after sufficient matches)."""
        with cortex_cursor(commit=False) as cur:
            cur.execute("""
                SELECT * FROM cortex_nodes
                WHERE node_type = 'tip' AND is_active = TRUE
                  AND elo < %s AND elo_matches >= %s
                ORDER BY elo ASC LIMIT %s
            """, (threshold, min_matches, limit))
            return cur.fetchall()
    
    # ── Edge operations ──
    
    def add_edge(self, source_id: str, target_id: str, relation: str = "related_to",
                 weight: float = 1.0):
        with cortex_cursor() as cur:
            cur.execute("""
                INSERT INTO cortex_edges (source_id, target_id, relation, weight)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (source_id, target_id, relation) DO UPDATE
                SET weight = GREATEST(cortex_edges.weight, %s)
            """, (source_id, target_id, relation, weight, weight))
    
    def get_neighbors(self, node_id: str, relation: str = None,
                      limit: int = 20) -> List[Dict]:
        with cortex_cursor(commit=False) as cur:
            sql = """
                SELECT n.*, e.relation, e.weight as edge_weight
                FROM cortex_nodes n
                JOIN cortex_edges e ON (e.target_id = n.id OR e.source_id = n.id)
                WHERE (e.source_id = %s OR e.target_id = %s) AND n.id != %s
            """
            params = [node_id, node_id, node_id]
            if relation:
                sql += " AND e.relation = %s"
                params.append(relation)
            sql += " ORDER BY e.weight DESC LIMIT %s"
            params.append(limit)
            cur.execute(sql, params)
            return cur.fetchall()
    
    # ── Tracking operations ──
    
    def record_tool_call(self, tool_name: str, status: str, speed_ms: float = None,
                         session_id: str = "", args_summary: str = "",
                         error_type: str = "", error_message: str = "",
                         confidence: float = None, approach: str = ""):
        with cortex_cursor() as cur:
            cur.execute("""
                INSERT INTO cortex_tool_calls
                (session_id, tool_name, status, speed_ms, args_summary,
                 error_type, error_message, confidence, approach)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (session_id, tool_name, status, speed_ms, args_summary,
                  error_type, error_message, confidence, approach))
    
    def record_prediction(self, session_id: str, task_type: str, task_summary: str,
                          predicted_difficulty: float, predicted_approach: str,
                          predicted_iterations: int, predicted_outcome: str,
                          confidence: float) -> str:
        pred_id = str(uuid.uuid4())
        with cortex_cursor() as cur:
            cur.execute("""
                INSERT INTO cortex_predictions
                (id, session_id, task_type, task_summary, predicted_difficulty,
                 predicted_approach, predicted_iterations, predicted_outcome, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (pred_id, session_id, task_type, task_summary, predicted_difficulty,
                  predicted_approach, predicted_iterations, predicted_outcome, confidence))
        return pred_id
    
    def record_flywheel_cycle(self, cycle_type: str, domain: str = "",
                              items_processed: int = 0, items_produced: int = 0,
                              metrics: dict = None) -> str:
        cycle_id = str(uuid.uuid4())
        with cortex_cursor() as cur:
            cur.execute("""
                INSERT INTO cortex_flywheel
                (id, cycle_type, domain, items_processed, items_produced, metrics)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (cycle_id, cycle_type, domain, items_processed,
                  items_produced, json.dumps(metrics or {})))
        return cycle_id
    
    def complete_flywheel_cycle(self, cycle_id: str, status: str = "completed",
                                error_message: str = ""):
        with cortex_cursor() as cur:
            cur.execute("""
                UPDATE cortex_flywheel
                SET status = %s, error_message = %s, completed_at = NOW()
                WHERE id = %s
            """, (status, error_message, cycle_id))
    
    # ── Stats ──
    
    def get_stats(self) -> Dict:
        with cortex_cursor(commit=False) as cur:
            stats = {}
            
            # Node counts by type
            cur.execute("""
                SELECT node_type, COUNT(*), AVG(elo), AVG(confidence)
                FROM cortex_nodes WHERE is_active = TRUE
                GROUP BY node_type ORDER BY COUNT(*) DESC
            """)
            stats['nodes_by_type'] = [
                {'type': r['node_type'], 'count': r['count'],
                 'avg_elo': float(r['avg_elo'] or 0),
                 'avg_confidence': float(r['avg_confidence'] or 0)}
                for r in cur.fetchall()
            ]
            
            # Total counts
            cur.execute("SELECT COUNT(*) as total FROM cortex_nodes WHERE is_active = TRUE")
            stats['total_nodes'] = cur.fetchone()['total']
            
            cur.execute("SELECT COUNT(*) as total FROM cortex_edges")
            stats['total_edges'] = cur.fetchone()['total']
            
            cur.execute("SELECT COUNT(*) as total FROM cortex_entities")
            stats['total_entities'] = cur.fetchone()['total']
            
            cur.execute("SELECT COUNT(*) as total FROM cortex_documents")
            stats['total_documents'] = cur.fetchone()['total']
            
            # Elo distribution
            cur.execute("""
                SELECT MIN(elo) as min, MAX(elo) as max, AVG(elo) as avg,
                       COUNT(*) FILTER (WHERE elo_matches > 0) as rated
                FROM cortex_nodes WHERE is_active = TRUE
            """)
            r = cur.fetchone()
            stats['elo'] = {
                'min': float(r['min'] or 0),
                'max': float(r['max'] or 0),
                'avg': float(r['avg'] or 0),
                'rated': r['rated']
            }
            
            # Recent flywheel cycles
            cur.execute("""
                SELECT cycle_type, COUNT(*), 
                       COUNT(*) FILTER (WHERE status = 'completed') as completed,
                       SUM(items_produced) as produced
                FROM cortex_flywheel
                WHERE created_at > NOW() - INTERVAL '24 hours'
                GROUP BY cycle_type
            """)
            stats['flywheel_24h'] = [
                {'type': r['cycle_type'], 'total': r['count'],
                 'completed': r['completed'],
                 'produced': r['produced'] or 0}
                for r in cur.fetchall()
            ]
            
            return stats
'''

print("Schema and access layer designed successfully.")
print(f"Schema: {len(SCHEMA_SQL)} chars")
print(f"Access layer: {len(ACCESS_LAYER)} chars")
