---
name: postgres-comprehensive-audit
description: Run a 25-dimension comprehensive audit against a PostgreSQL+pgvector database — data integrity, concurrency, failure recovery, query correctness, Elo/embedding quality, semantic dedup, HNSW indexing, orphan rescue, domain backfill, eval pruning, time-windowed dedup, SSD config tuning, duplicate index detection, backup, security, capacity, and dependency mapping.
version: 3.0
tags: [postgres, audit, database, integrity, concurrency, security, capacity, pgvector, embeddings, semantic-dedup]
---

# PostgreSQL Comprehensive Audit Marathon

## When to Use
- After migrating from SQLite to PostgreSQL
- Before putting a database-backed system into production
- After significant schema changes or data imports
- As periodic health check (monthly/quarterly)

## The 10 Audits

### Tier 1 — Must-do
1. **Data Integrity** — row counts, NULL checks, timestamp sanity, hash spot-checks, FK validity
2. **Concurrency** — multi-writer stress test, transaction isolation, lock contention, dead tuples
3. **Failure Mode & Recovery** — service health, daemon/heartbeat, backup existence, rollback correctness
4. **Query Correctness** — test every SQL pattern through the actual query layer (shim/ORM/raw)

### Tier 2 — Should-do
5. **Elo/Rating Quality** — distribution histogram, unrated nodes, eval history, rating inflation
6. **Embedding Coverage** — % with embeddings, cosine similarity sanity check, dimension verification
7. **Backup & Restore** — file existence, size, INSERT count, header inspection, restore dry-run
8. **Security** — file permissions, credential exposure, SQL injection risk, PG auth settings

### Tier 3 — Nice-to-have
9. **Capacity Planning** — DB size, growth rate, disk projections, index usage stats
10. **Dependency Graph** — external services, blast radius, criticality mapping

## Implementation Pattern

### Script Template (Python + psycopg2)
```python
import psycopg2, sqlite3, json, hashlib, threading, time
from datetime import datetime

PG_CONN = 'postgresql://user:pass@localhost:5432/dbname'
results = {"timestamp": datetime.now().isoformat(), "checks": {}}

pg = psycopg2.connect(PG_CONN)
pg.autocommit = True  # Required for individual statement commits
pc = pg.cursor()

# For SQLite comparison:
sl_conn = sqlite3.connect('/path/to/sqlite.db')
sl = sl_conn.cursor()  # NOT sl_conn directly!
```

### Key Checks Template

#### Data Integrity
```python
# Row count reconciliation
for sl_table, (pg_table, pg_filter) in table_map.items():
    sl.execute(f"SELECT COUNT(*) FROM {sl_table}")
    sl_count = sl.fetchone()[0]
    sql = f"SELECT COUNT(*) FROM {pg_table}"
    if pg_filter: sql += f" WHERE {pg_filter}"
    pc.execute(sql)
    pg_count = pc.fetchone()[0]

# NULL check — use IS NULL for numeric, IS NULL OR = '' for text
for col, is_numeric in [("text", False), ("confidence", True)]:
    if is_numeric:
        pc.execute(f"SELECT COUNT(*) FROM table WHERE {col} IS NULL")
    else:
        pc.execute(f"SELECT COUNT(*) FROM table WHERE {col} IS NULL OR {col} = ''")

# Timestamp sanity
pc.execute("SELECT COUNT(*) FROM table WHERE created_at > NOW()")  # future
pc.execute("SELECT COUNT(*) FROM table WHERE created_at < '2024-01-01'")  # too old
```

#### Concurrency
```python
# Multi-writer test with barrier synchronization
barrier = threading.Barrier(num_threads)
def writer(thread_id):
    conn = psycopg2.connect(PG_CONN)
    conn.autocommit = True
    cur = conn.cursor()
    barrier.wait(timeout=5)  # all threads start simultaneously
    for i in range(inserts_per_thread):
        cur.execute("INSERT INTO table (...) VALUES (...)")
    cur.close(); conn.close()

# Dead tuple check (needs VACUUM if high)
pc.execute("SELECT n_dead_tup FROM pg_stat_user_tables WHERE relname='table'")
```

#### Capacity
```python
pc.execute("SELECT pg_size_pretty(pg_database_size('dbname'))")
pc.execute("SELECT DATE(created_at), COUNT(*) FROM table GROUP BY DATE(created_at) ORDER BY DATE(created_at) DESC LIMIT 14")
pc.execute("SELECT indexrelname, idx_scan FROM pg_stat_user_indexes ORDER BY idx_scan DESC LIMIT 10")
```

## Gotchas (learned the hard way)

1. **Write scripts to /tmp, don't inline**: Shell quoting breaks every time with complex Python. Use `write_file` then `python3 /tmp/script.py`.
2. **sqlite3.connect() returns connection, not cursor**: Must call `conn.cursor()` before `execute()`.
3. **Numeric columns can't use `= ''`**: Postgres rejects this. Use `IS NULL` only.
4. **Check actual table/column names**: Schema may have changed. Use `PRAGMA table_info()` for SQLite, `information_schema.columns` for Postgres.
5. **`pg.autocommit = True`**: Without this, every statement starts an implicit transaction that stays open.
6. **fetchone() after DELETE returns None**: Don't try to read results from non-SELECT statements.
7. **gzip.open for backup inspection**: Use `gzip.open(backup, 'rt')` to peek at .gz SQL dumps.
8. **psycopg2 transaction cascade**: One error aborts all subsequent commands. Use try/except with rollback per operation.

## Bonus Tier — Deep Performance Audit

After the 10 core audits, run these for production-grade optimization:

### 11. Index Usage Analysis
```python
# Find unused indexes (idx_scan = 0)
c.execute("""
    SELECT relname as table_name, indexrelname as index_name,
           idx_scan as scans, pg_size_pretty(pg_relation_size(indexrelid)) as size
    FROM pg_stat_user_indexes
    ORDER BY idx_scan ASC
""")
# SAFE TO DROP: non-pkey indexes with 0 scans (save write overhead)
# NEVER DROP: *_pkey indexes (ORM/JOIN integrity depends on them)
```

### 12. Data Skew & Distribution
```python
c.execute("""
    SELECT node_type, COUNT(*) as cnt,
           ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct,
           AVG(elo) as avg_elo, COUNT(embedding) as emb_count
    FROM cortex_nodes GROUP BY node_type ORDER BY cnt DESC
""")
```

### 13. Cache Hit Ratio
```python
c.execute("""
    SELECT ROUND(SUM(idx_blks_hit) * 100.0 /
           NULLIF(SUM(idx_blks_hit + idx_blks_read), 0), 2)
    FROM pg_statio_user_indexes
""")
# Target: >99%. If lower, increase shared_buffers.
```

### 14. Table Bloat & Dead Tuples
```python
c.execute("""
    SELECT relname, n_dead_tup, n_live_tup,
           ROUND(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_pct
    FROM pg_stat_user_tables WHERE n_dead_tup > 100
""")
# If dead_pct > 10%, run VACUUM ANALYZE. If > 30%, run full VACUUM.
```

### 15. Sequential Scan Stats
```python
c.execute("""
    SELECT relname, seq_scan, idx_scan, n_live_tup
    FROM pg_stat_user_tables ORDER BY seq_scan DESC
""")
# Flag tables where seq_pct > 80% AND rows > 1000 — need index
```

### 16. PG Config Review
Check: shared_buffers, effective_cache_size, work_mem, maintenance_work_mem.
If effective_cache_size < total RAM, increase it.

## Gotchas (learned the hard way)

9. **RealDictRow from cortex_cursor**: Returns dict-like rows, NOT tuples. Use `row['column']` not `row[0]`. When unpacking with `for a, b in rows`, it fails — use `for row in rows: a = row['col_a']`.
10. **ROUND(double precision, int) fails in Postgres**: Cast first: `AVG(x)::numeric(10,1)`. Direct `ROUND(avg_col, 1)` only works on numeric type, not float8.
11. **pg_statio_user_tables** (not pg_stio_user_tables) — double-check catalog view names.
12. **Background process output buffering**: Hermes background processes may not capture stdout even with `python3 -u`. For verification, run the same query foreground instead of relying on background output.
13. **VACUUM requires autocommit**: `VACUUM ANALYZE table` cannot run inside a transaction. Set `pg.autocommit = True` before executing.

## FK-Safe Bulk Deletion Pattern

When cleaning up rows that have foreign key references (NO ACTION, not CASCADE), you must delete referencing rows first or the DELETE fails with `ForeignKeyViolation`. Pattern:

```python
def safe_delete(cursor, pg, sql, label):
    """Delete with rollback on FK violation."""
    try:
        cursor.execute(sql)
        cnt = cursor.rowcount
        pg.commit()
        return cnt
    except Exception as e:
        pg.rollback()
        return 0

# Step 1: Collect IDs to delete
cursor.execute("SELECT id FROM cortex_nodes WHERE <bad_condition>")
bad_ids = tuple(r[0] for r in cursor.fetchall())

# Step 2: Delete ALL FK references first (order matters!)
for ref_table, ref_col in [
    ('cortex_eval_history', 'node_id_a'),
    ('cortex_eval_history', 'node_id_b'),
    ('cortex_eval_history', 'winner_id'),
    ('cortex_edges', 'source_id'),
    ('cortex_edges', 'target_id'),
    ('cortex_node_entities', 'node_id'),
]:
    safe_delete(cursor, pg, f"DELETE FROM {ref_table} WHERE {ref_col} IN %s", f"{ref_table}.{ref_col}")

# Step 3: Now safe to delete the target rows
safe_delete(cursor, pg, f"DELETE FROM cortex_nodes WHERE id IN %s", "target nodes")
```

**Key insight**: Check FK ON DELETE action first — `CASCADE` handles it automatically, but `NO ACTION` (the default) requires manual cleanup. Query: `SELECT conname, confdeltype FROM pg_constraint WHERE confrelid = 'cortex_nodes'::regclass`. confdeltype: 0=NO ACTION, 4=CASCADE.

## Tier 4 — Semantic & Vector Audits (pgvector)

When the database has embedding columns (pgvector), these audits catch quality issues that SQL alone can't detect.

### 17. Embedding Coverage & Backfill
```python
# Check coverage
c.execute("SELECT COUNT(*), COUNT(embedding) FROM cortex_nodes")
total, with_emb = c.fetchone()
pct = 100 * with_emb / total

# Backfill missing embeddings (sentence-transformers)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

c.execute("SELECT id, text FROM cortex_nodes WHERE embedding IS NULL AND text IS NOT NULL")
rows = c.fetchall()
texts = [r[1] or '' for r in rows]
embeddings = model.encode(texts, batch_size=500)
for i, (node_id, _) in enumerate(rows):
    c.execute("UPDATE cortex_nodes SET embedding = %s::vector WHERE id = %s",
              (str(embeddings[i].tolist()), node_id))
```

**Gotcha**: New rows inserted during backfill will also lack embeddings. Run backfill in a loop until 0 remaining, or add a trigger to auto-embed on INSERT.

### 18. Semantic Dedup (pgvector Cosine Similarity)
Exact text dedup misses near-duplicates with minor wording differences. Use embedding cosine similarity:

```python
# Find all pairs with similarity > threshold (0.95 for near-dupes)
# UNION-FIND clustering to group related duplicates
from collections import defaultdict

parent = {}
def find(x):
    while parent.get(x, x) != x:
        parent[x] = parent.get(parent[x], parent[x])
        x = parent[x]
    return x
def union(x, y):
    px, py = find(x), find(y)
    if px != py: parent[px] = py

# pgvector distance: similarity = 1 - (embedding <=> embedding)
c.execute("""
    SELECT a.id, b.id FROM cortex_nodes a
    JOIN cortex_nodes b ON a.id < b.id
    WHERE a.node_type = 'tip' AND b.node_type = 'tip'
    AND a.embedding IS NOT NULL AND b.embedding IS NOT NULL
    AND (1 - (a.embedding <=> b.embedding)) > 0.95
""")
for a_id, b_id in c.fetchall():
    union(a_id, b_id)

# Keep highest Elo per cluster, delete rest (use FK-safe pattern above)
```

**Gotcha**: Full self-join on large tables is O(n^2). Use HNSW index or LIMIT batching. For 4K tips it's fine; for 100K+ use batched nearest-neighbor.

### 19. HNSW Vector Index Creation
Without an HNSW index, every `ORDER BY embedding <=> $1 LIMIT k` does a brute-force O(n) scan:

```python
# Create HNSW index (one-time, takes ~30s for 35K rows)
c.execute("""
    CREATE INDEX idx_nodes_embedding_hnsw
    ON cortex_nodes USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64)
""")
# m=16: connectivity (higher = more accurate, more memory)
# ef_construction=64: build-time search depth (higher = slower build, better quality)

# Verify speed improvement
# Before HNSW: ~50ms for k-NN on 35K rows
# After HNSW:  ~0.3ms for k-NN on 35K rows (100x+ speedup)
```

**Verify**: `SELECT indexrelname FROM pg_indexes WHERE indexdef LIKE '%vector%'` — note that FTS/GIN indexes also match "vector" in their def. Filter for `hnsw` or `ivfflat` specifically.

### 20. Orphan Node Rescue
Nodes with no edges are invisible to graph traversals. Connect them via semantic similarity:

```python
# Find orphans
c.execute("""
    SELECT n.id FROM cortex_nodes n
    LEFT JOIN cortex_edges e ON (n.id = e.source_id OR n.id = e.target_id)
    WHERE e.id IS NULL AND n.node_type = 'tip' AND n.is_active = true
""")

# Create semantic edges using LATERAL JOIN (efficient per-node k-NN)
c.execute("""
    INSERT INTO cortex_edges (id, source_id, target_id, relation, weight, created_at)
    SELECT gen_random_uuid(), %s, m.id, 'semantic',
           LEAST(1 - (t.embedding <=> m.embedding), 1.0), NOW()
    FROM cortex_nodes t, LATERAL (
        SELECT id, embedding FROM cortex_nodes
        WHERE node_type NOT IN ('tip', 'circuit_breaker')
        AND embedding IS NOT NULL AND is_active = true
        ORDER BY embedding <=> t.embedding LIMIT 3
    ) m
    WHERE t.id = %s
    AND (1 - (t.embedding <=> m.embedding)) > 0.5
""", (tip_id, tip_id))
```

### 21. Domain Backfill from JSONB Metadata
When migration leaves domain/type columns empty but the data exists in metadata JSONB:

```python
# Extract from metadata action_type
c.execute("""
    UPDATE cortex_nodes SET domain = metadata->>'action_type'
    WHERE node_type='experience'
    AND (domain IS NULL OR domain = '')
    AND metadata->>'action_type' IS NOT NULL
""")

# Fall back to provenance
c.execute("""
    UPDATE cortex_nodes SET domain = provenance
    WHERE node_type='experience'
    AND (domain IS NULL OR domain = '')
    AND provenance IS NOT NULL AND provenance != ''
""")

# Final fallback
c.execute("""
    UPDATE cortex_nodes SET domain = 'generic'
    WHERE node_type='experience' AND (domain IS NULL OR domain = '')
""")
```

## Confidence Type Guard (Shim Pattern)

When a compatibility shim translates between databases, numeric fields can receive wrong types:

```python
# In the INSERT handler — detect Unix timestamps masquerading as confidence
if k == 'confidence':
    if isinstance(v, (int, float)):
        fv = float(v)
        if fv > 1e9:  # Unix timestamp (year 2001+)
            v = 0.5    # Fallback — don't silently clamp to 1.0
        else:
            v = min(max(fv, 0.0), 1.0)
    else:
        v = 0.5
```

**Gotcha**: `min(max(1776195800, 0.0), 1.0)` = 1.0, which silently masks the bug. Always detect timestamp-scale values BEFORE clamping.

## Tier 5 — Operational Audits

### 22. Stale Eval History Pruning
Eval records referencing inactive/deleted nodes waste space and slow queries. Prune in batches:

```python
# Batched DELETE to avoid long locks
for batch in range(10):
    c.execute("""
        DELETE FROM cortex_eval_history WHERE id IN (
            SELECT eh.id FROM cortex_eval_history eh
            JOIN cortex_nodes a ON eh.node_id_a = a.id
            JOIN cortex_nodes b ON eh.node_id_b = b.id
            WHERE a.is_active = false OR b.is_active = false
            LIMIT 10000
        )
    """)
    if c.rowcount == 0:
        break
```

### 23. Time-Windowed Dedup (Circuit Breakers)
For high-frequency logging tables where each "event" creates a row, keep one per time window:

```python
c.execute("""
    WITH ranked AS (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY metadata->>'tool_name',
                               DATE_TRUNC('hour', created_at)
                   ORDER BY created_at
               ) as rn
        FROM cortex_nodes WHERE node_type='circuit_breaker'
    )
    DELETE FROM cortex_nodes WHERE id IN (SELECT id FROM ranked WHERE rn > 1)
""")
```

### 24. PG Config for SSD
```python
# SSD-optimized settings (default random_page_cost=4 is for HDD)
c.execute("ALTER SYSTEM SET random_page_cost = 1.1")
# work_mem should be total_ram / (max_connections * 2) — 64MB is too high for 100 connections
c.execute("ALTER SYSTEM SET work_mem = '16MB'")
# NOTE: requires pg_reload_conf() or PG restart. User may need superuser.
```

### 25. Duplicate Index Detection
```python
# Find indexes with identical column definitions
c.execute("""
    SELECT i1.relname as name1, i2.relname as name2
    FROM pg_index x1 JOIN pg_class i1 ON x1.indexrelid = i1.oid
    JOIN pg_index x2 ON x1.indrelid = x2.indrelid
    JOIN pg_class i2 ON x2.indexrelid = i2.oid
    WHERE i1.oid < i2.oid AND x1.indkey = x2.indkey
""")
# CAUTION: Same indkey doesn't mean fully redundant — partial indexes (WHERE clause)
# and different index types (btree vs GIN) may serve different purposes.
# Only drop if both are same type AND one has fewer scans.
```

**Gotcha**: Prefix-based text dedup (GROUP BY LEFT(text, 100)) is a false alarm — tips about the same topic with different recommendations are NOT duplicates. Always verify with full-text or embedding comparison.

## Flywheel Data Flow Audit (CRITICAL — beyond surface checks)

Surface row counts and "table exists" checks can report 100% green while the actual data pipeline is broken. Run these AFTER the standard checks to find broken data flows:

### F1. Domain Normalization Coverage (per node_type)
Surface checks only verify that canonical domains exist. You must verify coverage PER NODE TYPE:
```python
CANONICAL_DOMAINS = {'tool_usage', 'agent_architecture', 'coding', 'reasoning', ...}
for nt in ['tip', 'experience', 'fact']:
    c.execute(f"SELECT count(*) FROM cortex_nodes WHERE node_type='{nt}' AND is_active=true AND domain NOT IN %s", (tuple(CANONICAL_DOMAINS),))
    non_canon = c.fetchone()[0]
    if non_canon > 0:
        # CRITICAL: domain normalization was applied to tips but not experiences
        c.execute(f"SELECT domain, count(*) FROM cortex_nodes WHERE node_type='{nt}' AND is_active=true GROUP BY domain ORDER BY count(*) DESC LIMIT 10")
        # Fix: batch UPDATE experiences to canonical domains based on content/action_type
```

**Gotcha**: Domain normalization scripts often only target `node_type='tip'`. Experiences and other types get the raw tool_name or empty string as domain. CHECK ALL TYPES.

### F2. Elo Distribution by Node Type (dead rating detection)
```python
c.execute("""
    SELECT node_type, count(*), avg(elo)::numeric(10,1), 
           percentile_cont(0.9) WITHIN GROUP (ORDER BY elo)::numeric(10,1),
           max(elo) FROM cortex_nodes WHERE is_active=true 
    GROUP BY node_type ORDER BY count(*) DESC
""")
# If any type has avg_elo near seed (e.g. 1200) and p90 also near seed,
# the rating daemon isn't scoring that type. This breaks retrieval by elo.
```

**Gotcha**: If the Elo rater only evaluates tips but not experiences, the experience retrieval path (`min_elo=1300`) will never find experiences rated below that threshold. Check that the daemon's rating loop covers ALL active node types, not just tips.

### F3. Retrieval Parameter Alignment
Check that every query in the injection pipeline can actually return results given current Elo/salience distributions:
```python
# Example: P3 Retriever requires min_elo=1300 for tips
# But P3 experience path queries by salience not elo
# If experience max_elo < tip min_elo threshold, retrieval is dead
c.execute("SELECT max(elo) FROM cortex_nodes WHERE node_type='experience' AND is_active=true")
exp_max_elo = c.fetchone()[0]
if exp_max_elo < 1300:
    print("CRITICAL: Experience max Elo below Retriever min_elo threshold!")
```

### F4. Access Pattern Audit (injection actually reaching nodes?)
```python
# If 99.9% of nodes of a type have access_count=0, injection is cosmetic
c.execute("""
    SELECT node_type, count(*) as total, 
           count(*) FILTER (WHERE access_count > 0) as accessed
    FROM cortex_nodes WHERE is_active=true 
    GROUP BY node_type ORDER BY total DESC
""")
for row in c.fetchall():
    pct = 100 * row[2] / row[1] if row[1] > 0 else 0
    if pct < 1 and row[1] > 100:
        print(f"WARN: {row[0]} — only {pct:.1f}% ever accessed ({row[2]}/{row[1]})")
```

### F5. JSON Content vs Keyword Retrieval Mismatch
If experiences are stored as JSON action_hash blobs but retrieval uses `text ILIKE %keyword%` against the text column, keyword matching will fail:
```python
c.execute("SELECT count(*) FROM cortex_nodes WHERE node_type='experience' AND text ILIKE '{%' AND is_active=true")
json_blobs = c.fetchone()[0]
c.execute("SELECT count(*) FROM cortex_nodes WHERE node_type='experience' AND text NOT ILIKE '{%' AND is_active=true")
natural_lang = c.fetchone()[0]
if json_blobs > natural_lang:
    print(f"CRITICAL: {json_blobs} experiences are JSON blobs, keyword retrieval broken")
    # Fix: add generated text column or switch to embedding-based retrieval
```

### F6. Dead Node Type Audit
```python
# Node types with 0 accesses are being created but never injected
c.execute("""
    SELECT node_type, count(*), avg(access_count)::numeric(10,2) 
    FROM cortex_nodes WHERE is_active=true 
    AND node_type NOT IN ('tip', 'experience', 'fact')
    GROUP BY node_type ORDER BY count(*) DESC
""")
# observation, world, skill_verification, entity, etc. with 0 access = dead weight
# Either wire them into injection or stop creating them
```

### F7. KV Store Null Key Check
```python
c.execute("SELECT count(*) FROM cortex_kv_store WHERE key IS NULL")
null_keys = c.fetchone()[0]
if null_keys > 0:
    print(f"HIGH: {null_keys} KV store rows have NULL key — lookups broken")
```

### F8. World Model Prediction Freshness
```python
c.execute("SELECT max(created_at) FROM cortex_predictions")
last_pred = c.fetchone()[0]
if last_pred and (datetime.now() - last_pred).days > 2:
    print("CRITICAL: World model predictions stale (>2 days old)")
    # simulate() may have stopped firing in pre_tool_call hook
```

## The Audit Gauntlet Pattern

For comprehensive DB health, run audits in waves:

**Wave 1**: Data integrity basics (embedding coverage, confidence range, dedup, FK integrity, timestamps)
**Wave 2**: Semantic quality (cosine dedup, domain backfill, orphan rescue, HNSW indexing)
**Wave 3**: Deep audits (Elo distribution, edge weight analysis, cross-type similarity, circuit breaker health)
**Wave 4**: Flywheel data flow audit (F1-F8 above — trace actual pipeline function, not just data existence)
**Wave 5**: Fix all findings, then re-run Wave 1 as verification

Key insight: new rows arrive during the audit (from daemons/crons). The final verification will always show a few new issues. The shim's type guards are the permanent fix; batch cleanup is the one-time fix.

**CRITICAL insight from R168+ audit**: A 23-check surface audit reporting 100% pass can coexist with 12 real flywheel issues (5 critical). Surface checks verify data EXISTS; flywheel checks verify it FLOWS. Both are required.

## Output Format

Produce a structured summary with:
- PASS/WARN/FAIL per audit
- Specific numbers and deltas
- Action items in priority order
- JSON results saved to `/tmp/` for programmatic access
