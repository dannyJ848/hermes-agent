# Cortex DB Schema Repair — May 15, 2026

## Problem

Cognitive orchestrator reports 19/20 subsystems active. `cortex_flywheel` fails to initialize with:
```
CortexFlywheel init failed (DB schema issue): no such column: node_type
```

Root cause: `~/.hermes/cortex.db` was created with only 5 columns (`id`, `content`, `metadata`, `created_at`, `updated_at`) but `cortex_access.py` expects 20+ columns plus three additional tables.

## Full Schema Required

### cortex_nodes (20 columns)
```sql
CREATE TABLE cortex_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_type TEXT DEFAULT 'tip',
    text TEXT,
    domain TEXT DEFAULT 'general',
    confidence REAL DEFAULT 0.5,
    elo REAL DEFAULT 1200.0,
    elo_matches INTEGER DEFAULT 0,
    provenance TEXT,
    source_ids TEXT,
    metadata TEXT,
    content_md5 TEXT,
    embedding TEXT,
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    frequency INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    last_seen REAL,
    last_evaluated REAL,
    created_at REAL,
    updated_at REAL
);
```

Indexes: `idx_node_type`, `idx_domain`, `idx_elo`, `idx_is_active`, `idx_content_md5`

### cortex_edges
```sql
CREATE TABLE cortex_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    target_id INTEGER NOT NULL,
    relation TEXT DEFAULT 'related_to',
    weight REAL DEFAULT 1.0,
    metadata TEXT DEFAULT '{}',
    created_at REAL
);
```

Indexes: `idx_edges_source`, `idx_edges_target`

### cortex_eval_history
```sql
CREATE TABLE cortex_eval_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id TEXT NOT NULL,
    node_id_a INTEGER NOT NULL,
    node_id_b INTEGER NOT NULL,
    winner_id INTEGER,
    judge_id TEXT DEFAULT '',
    judge_axis TEXT DEFAULT '',
    margin REAL DEFAULT 0.5,
    domain TEXT DEFAULT '',
    created_at REAL
);
```

Index: `idx_eval_round`

### cortex_flywheel
```sql
CREATE TABLE cortex_flywheel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_type TEXT NOT NULL,
    status TEXT DEFAULT 'running',
    domain TEXT DEFAULT '',
    items_processed INTEGER DEFAULT 0,
    items_produced INTEGER DEFAULT 0,
    metrics TEXT DEFAULT '{}',
    error_message TEXT DEFAULT '',
    started_at REAL,
    completed_at REAL
);
```

## How to Discover the Schema

The schema is NOT in `cortex_access.py` as CREATE TABLE statements. It's implied by INSERT/UPDATE/SELECT statements. To extract:

```bash
# 1. Check all columns referenced in INSERT
grep -A5 "INSERT INTO cortex_nodes" agent/cortex_access.py

# 2. Check all columns in UPDATE SET
grep "UPDATE cortex_nodes SET" agent/cortex_access.py

# 3. Check WHERE clauses for indexed columns
grep "WHERE.*=" agent/cortex_access.py | grep cortex

# 4. Check cortex_flywheel for additional tables
grep "FROM cortex_" agent/cortex_access.py | sort | uniq
```

## Repair Procedure (Proven Path)

**DO NOT use heredocs or terminal command strings** — bash escaping destroys multi-line SQL.

**DO use write_file + subprocess.run:**

```python
import subprocess

script = '''
import sqlite3
db_path = '/home/djg6228/.hermes/cortex.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Drop partial tables
cur.execute("DROP TABLE IF EXISTS cortex_edges")
cur.execute("DROP TABLE IF EXISTS cortex_eval_history")
cur.execute("DROP TABLE IF EXISTS cortex_flywheel")
cur.execute("DROP TABLE IF EXISTS cortex_nodes")

# Create cortex_nodes with full schema
cur.execute("""
CREATE TABLE cortex_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_type TEXT DEFAULT 'tip',
    text TEXT,
    domain TEXT DEFAULT 'general',
    confidence REAL DEFAULT 0.5,
    elo REAL DEFAULT 1200.0,
    elo_matches INTEGER DEFAULT 0,
    provenance TEXT,
    source_ids TEXT,
    metadata TEXT,
    content_md5 TEXT,
    embedding TEXT,
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    frequency INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    last_seen REAL,
    last_evaluated REAL,
    created_at REAL,
    updated_at REAL
)
""")

cur.execute("CREATE INDEX idx_node_type ON cortex_nodes(node_type)")
cur.execute("CREATE INDEX idx_domain ON cortex_nodes(domain)")
cur.execute("CREATE INDEX idx_elo ON cortex_nodes(elo)")
cur.execute("CREATE INDEX idx_is_active ON cortex_nodes(is_active)")
cur.execute("CREATE INDEX idx_content_md5 ON cortex_nodes(content_md5)")

# Create cortex_edges
cur.execute("""
CREATE TABLE cortex_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    target_id INTEGER NOT NULL,
    relation TEXT DEFAULT 'related_to',
    weight REAL DEFAULT 1.0,
    metadata TEXT DEFAULT '{}',
    created_at REAL
)
""")

cur.execute("CREATE INDEX idx_edges_source ON cortex_edges(source_id)")
cur.execute("CREATE INDEX idx_edges_target ON cortex_edges(target_id)")

# Create cortex_eval_history
cur.execute("""
CREATE TABLE cortex_eval_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id TEXT NOT NULL,
    node_id_a INTEGER NOT NULL,
    node_id_b INTEGER NOT NULL,
    winner_id INTEGER,
    judge_id TEXT DEFAULT '',
    judge_axis TEXT DEFAULT '',
    margin REAL DEFAULT 0.5,
    domain TEXT DEFAULT '',
    created_at REAL
)
""")

cur.execute("CREATE INDEX idx_eval_round ON cortex_eval_history(round_id)")

# Create cortex_flywheel
cur.execute("""
CREATE TABLE cortex_flywheel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_type TEXT NOT NULL,
    status TEXT DEFAULT 'running',
    domain TEXT DEFAULT '',
    items_processed INTEGER DEFAULT 0,
    items_produced INTEGER DEFAULT 0,
    metrics TEXT DEFAULT '{}',
    error_message TEXT DEFAULT '',
    started_at REAL,
    completed_at REAL
)
""")

conn.commit()
conn.close()
print("Schema created successfully")
'''

# Write locally, pipe to remote via stdin
result = subprocess.run(
    ['ssh', '-i', key_path, 'djg6228@spark-85e8.local',
     'cat > /tmp/fix_cortex.py && python3 /tmp/fix_cortex.py'],
    input=script,
    capture_output=True,
    text=True,
    timeout=30
)
print(result.stdout)
```

## Verification

```bash
ssh djg6228@spark-85e8.local 'sqlite3 ~/.hermes/cortex.db ".tables"'
# Expected: cortex_edges  cortex_eval_history  cortex_flywheel  cortex_nodes

# Test cognitive orchestrator initialization
python3 -c "from run_agent import AIAgent; agent = AIAgent()" 2>&1 | grep "orchestrator ready"
# Expected: "Cognitive orchestrator ready: 20/20 subsystems active"
```

## Related

- `infrastructure-surgical-management` skill — SSH remote script execution pattern
- `hermes-cron-infrastructure` skill — Weak tool avoidance (write_file + execute_code vs terminal heredocs)
