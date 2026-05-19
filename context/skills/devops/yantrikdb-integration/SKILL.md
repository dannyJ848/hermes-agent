---
name: yantrikdb-integration
description: Integrate YantrikDB cognitive memory engine with Hermes Agent. Covers initialization, batch imports, queue management, and migration from Cerebrum SQLite.
trigger: When working with YantrikDB, cognitive memory engines, memory migration, or batch memory imports.
---

# YantrikDB Integration

YantrikDB is a cognitive memory engine with bundled embedders, graph relationships, and async ingestion. It can serve as a drop-in replacement or complement to Cerebrum/Hindsight for semantic memory storage.

## Installation

```bash
pip install yantrikdb          # bundled embedder (~7MB, works out of box)
pip install yantrikdb-mcp      # MCP server for Claude/Cursor/Windsurf
```

## Initialization Patterns

### Default (bundled embedder)

```python
import yantrikdb
ydb = yantrikdb.YantrikDB.with_default("/path/to/db.db")
```

This uses the bundled `potion-base-2M` embedder (dim=64). No sentence-transformers, no ONNX, no download.

### Larger bundled variant

```python
ydb = yantrikdb.YantrikDB("memory.db", embedding_dim=256)
ydb.set_embedder_named("potion-base-8M")   # ~28MB, ~92% MiniLM quality
# or: ydb.set_embedder_named("potion-base-32M")  # ~121MB, ~95% MiniLM
```

### Custom embedder (sentence-transformers)

```python
from sentence_transformers import SentenceTransformer
ydb = yantrikdb.YantrikDB("memory.db", embedding_dim=384)
ydb.set_embedder(SentenceTransformer("all-MiniLM-L6-v2"))
```

### Ollama embedder (NOT recommended — signature mismatch)

```python
# WRONG — set_embedder_named only takes one positional arg
ydb.set_embedder_named("ollama", "nomic-embed-text", "http://localhost:11434")
# → TypeError: takes 1 positional argument but 3 were given

# WRONG — set_embedder requires encode() that returns list[float]
ydb.set_embedder("ollama")
# → LookupError: unknown encoding: __yantrikdb_probe__
```

**Use `with_default()` or `set_embedder_named("potion-base-8M")` instead.**

## Core Operations

```python
# Record a memory
ydb.record(
    text="Alice is the engineering lead",
    memory_type="semantic",      # or "episodic", "procedural"
    importance=0.8,
    namespace="people",            # logical grouping
    domain="work",
    source="user",
    certainty=0.9,
    metadata={"user_id": "alice"}
)

# Recall by semantic similarity
results = ydb.recall("who leads the team?", top_k=3, namespace="people")
# → [{"text": "Alice is the engineering lead", "score": 1.0, ...}, ...]

# Graph relationships
ydb.relate("Alice", "Engineering", "leads")
ydb.get_edges("Alice")

# Consolidation and conflict detection
ydb.think()  # merges similar, finds contradictions, mines patterns

# Stats
ydb.stats()  # → {'active_memories': N, 'vec_index_entries': N, ...}

ydb.close()
```

## Batch Import Pattern

**CRITICAL:** YantrikDB has an async ingest queue with max 256 pending ops. Batch imports WILL fill the queue and throw `RuntimeError: ingest queue full (256 pending ops, max=256); retry after 50ms`.

### Working Pattern: Small Batches + think() Flush

```python
import time

BATCH_SIZE = 20       # Safe: stays under 256 queue limit
SLEEP_BETWEEN = 3.0   # Seconds between batches

def import_batch(ydb, records, batch_size=20):
    """Import records with queue management."""
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        
        # Retry with exponential backoff
        for attempt in range(20):
            try:
                ydb.record_batch(batch)
                break
            except RuntimeError as e:
                if "ingest queue full" in str(e) and attempt < 19:
                    time.sleep(0.1 * (attempt + 1))
                    continue
                raise
        
        # Flush queue every 5 batches
        if (i // batch_size + 1) % 5 == 0:
            ydb.think()  # Consolidates and frees queue space
            time.sleep(1.0)
        
        time.sleep(SLEEP_BETWEEN)
```

### Anti-Pattern: Large Batches Without Flush

```python
# WRONG — will fail at ~250 records
for tip in all_tips:
    ydb.record(text=tip, ...)  # Queue fills, throws at ~256

# WRONG — batch too large
ydb.record_batch(all_tips[:500])  # → ingest queue full
```

## Cerebrum → YantrikDB Migration

### Step 1: Read from Cerebrum SQLite

```python
import sqlite3

conn = sqlite3.connect("~/.hermes/cerebrum_memory.db")
c = conn.cursor()
c.execute("""
    SELECT id, tip_type, condition, recommendation, rationale,
           tool_name, domain, confidence, upvotes, downvotes,
           frequency, source_ids
    FROM distilled_tips
""")
tips = c.fetchall()  # 1282 tips in this session
conn.close()
```

### Step 2: Transform to YantrikDB format

```python
records = []
for tip in tips:
    tip_id, tip_type, condition, recommendation, rationale, \
        tool_name, domain, confidence, upvotes, downvotes, \
        frequency, source_ids = tip
    
    text = f"[{tip_type}] {domain or 'general'} | {tool_name or ''}\n"
    text += f"CONDITION: {condition}\n"
    text += f"RECOMMENDATION: {recommendation}\n"
    if rationale:
        text += f"RATIONALE: {rationale}\n"
    text += f"Confidence: {confidence:.4f} | Votes: +{upvotes}/-{downvotes}"
    
    records.append({
        "text": text,
        "memory_type": "semantic",
        "importance": min(1.0, (confidence or 0.5) * (1 + (upvotes or 0) * 0.1)),
        "metadata": {
            "cerebrum_id": tip_id,
            "tip_type": tip_type,
            "tool_name": tool_name or "",
            "domain": domain or "general",
            "upvotes": upvotes,
            "downvotes": downvotes,
            "frequency": frequency,
        },
        "namespace": "cerebrum_tips",
        "domain": domain or "general",
        "source": "cerebrum_migration",
        "certainty": confidence or 0.5
    })
```

### Step 3: Import with flush management

```python
ydb = yantrikdb.YantrikDB.with_default("~/.hermes/yantrikdb_copy.db")

import_batch(ydb, records, batch_size=20)

# Verify
result = ydb.recall("tool usage patterns", top_k=3, namespace="cerebrum_tips")
print(f"Imported {len(records)} tips, sample recall: {result[0]['text'][:80]}...")

ydb.close()
```

## Queue Management Deep Dive

The ingest queue is async — `record()` and `record_batch()` enqueue ops but don't wait for embedding + indexing. The background thread processes them. When the queue hits 256, new ops are rejected.

**`think()` flushes the queue** by triggering consolidation, which processes pending ops. Call it periodically during bulk imports.

### Session-Discovered Flush Pattern

From live migration of 1,282 cerebrum tips:
- `think()` after every ~100 records (5 batches of 20) keeps queue clear — **when the background thread is healthy**
- `stats()` before/after `think()` shows `active_memories` increasing and `operations` incrementing
- Without `think()`, queue fills at ~250 records regardless of sleep time
- **Critical finding (May 2026):** When the background thread is deadlocked, `think()` takes 18+ seconds and does NOT reduce queue depth. Batches as small as 50 with 2-second delays still fill the queue to 256. This is a plugin-level bug requiring the direct SQLite workaround.
- `record_batch()` with 20-item batches + `think()` every 5 batches = sustainable throughput (when queue is healthy)

**`stats()` shows queue state:**
```python
stats = ydb.stats()
# 'operations': total ops processed
# 'vec_index_entries': memories with embeddings
# 'active_memories': total in DB
```

If `operations` stops increasing between calls, the queue is stalled.

## Emergency Workaround: Direct SQLite Insertion

When the ingest queue is permanently stuck (background thread not draining, `think()` fails to reduce queue depth), bypass the API and insert directly into YantrikDB's SQLite schema. **The `embed()` method still works even when the queue is stuck** — use it to generate embeddings, then insert via raw SQL.

```python
import sqlite3, struct, time, json
from yantrikdb import YantrikDB

def direct_insert(ydb_path, records):
    """Insert records directly into YantrikDB SQLite, bypassing the queue."""
    db = YantrikDB.with_default(ydb_path)  # For embeddings only
    conn = sqlite3.connect(ydb_path)
    cursor = conn.cursor()
    
    for rec in records:
        # Generate embedding via YantrikDB API
        emb = db.embed(rec['text'])
        emb_blob = struct.pack(f'{len(emb)}f', *emb)
        
        rid = f"manual_{int(time.time() * 1e6)}_{hash(rec['text']) & 0xFFFFFFFF:08x}"
        now = time.time()
        
        cursor.execute('''
            INSERT INTO memories (rid, type, text, embedding, created_at, updated_at,
                                importance, half_life, last_access, access_count, valence,
                                consolidation_status, storage_tier, metadata, namespace,
                                certainty, domain, source, created_at_unix_micros)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rid, rec.get('memory_type', 'semantic'), rec['text'], emb_blob,
            now, now, rec.get('importance', 0.5), 604800.0, now, 0, 0.0,
            'active', 'hot', json.dumps(rec.get('metadata', {})),
            rec.get('namespace', 'default'), rec.get('certainty', 0.8),
            rec.get('domain', 'general'), rec.get('source', 'user'),
            int(now * 1e6)
        ))
    
    conn.commit()
    conn.close()
    db.close()
```

**When to use this workaround:**
- `record()` throws "ingest queue full" even after `think()` + sleep
- `stats()` shows `operations` not increasing between `think()` calls
- Queue fills with batches smaller than 50 despite 2+ second delays
- Terminal commands timeout because `think()` takes 18+ seconds per call

**Schema requirements:** The `memories` table has 30 columns (see `PRAGMA table_info(memories)`). The minimal required insert set is: `rid`, `type`, `text`, `embedding`, `created_at`, `updated_at`, `importance`, `half_life`, `last_access`, `access_count`, `valence`, `consolidation_status`, `storage_tier`, `metadata`, `namespace`, `certainty`, `domain`, `source`, `created_at_unix_micros`.

**Post-insertion:** Call `db.rebuild_vec_index()` or restart YantrikDB to rebuild the vector index from the SQLite table. Without this, `recall()` may not find newly inserted records.

## MemoryProvider ABC Integration

To wire YantrikDB as Hermes' official memory provider (set `memory.provider: yantrikdb` in `config.yaml`), implement the `MemoryProvider` ABC in `plugins/memory/yantrikdb/__init__.py`.

### Key Implementation Points

**Python version mismatch:** YantrikDB's Rust extension (`_yantrikdb_rust.cpython-XX-darwin.so`) is compiled for a specific Python version (e.g., 3.8). If Hermes runs on a different Python (e.g., 3.11), the import fails with `ImportError: ... undefined symbol` or `ModuleNotFoundError: No module named 'yantrikdb._yantrikdb_rust'`.

**Fix: Rebuild the Rust extension for the target Python version:**

```bash
# 1. Ensure maturin is installed in the target venv
/Users/dannygomez/hermes-agent/venv/bin/python3 -m pip install maturin

# 2. Build the wheel for the target Python
cd ~/.hermes/plugins/yantrikdb
/Users/dannygomez/hermes-agent/venv/bin/python3 -m maturin build \
    --release \
    --interpreter /Users/dannygomez/hermes-agent/venv/bin/python3

# 3. Install the built wheel
/Users/dannygomez/hermes-agent/venv/bin/python3 -m pip install \
    target/wheels/yantrikdb-*.whl --force-reinstall
```

**Verify:**
```python
/Users/dannygomez/hermes-agent/venv/bin/python3 -c "from yantrikdb import YantrikDB; print('OK')"
```

**Alternative (if rebuilding is not possible):** Use lazy import in `_load_yantrikdb()` and add the plugin's `src/` directory to `sys.path` dynamically. But rebuilding is the correct fix — the lazy import only works if the `.so` happens to be compatible.

**Lazy import pattern (with installed-package-first fallback):**
```python
_YantrikDB = None
_TenantManager = None

def _load_yantrikdb():
    """Import YantrikDB."""
    global _YantrikDB, _TenantManager
    if _YantrikDB is not None:
        return _YantrikDB, _TenantManager

    # Try importing from the installed package first (pip installed wheel)
    try:
        from yantrikdb import YantrikDB, TenantManager
        _YantrikDB = YantrikDB
        _TenantManager = TenantManager
        return _YantrikDB, _TenantManager
    except ImportError:
        pass  # Fall through to src/ path

    # Fallback: try from the plugin src directory
    try:
        from hermes_cli.config import get_hermes_home
        hermes_home = get_hermes_home()
    except Exception:
        hermes_home = Path.home() / ".hermes"

    plugin_src = hermes_home / "plugins" / "yantrikdb" / "src"
    if str(plugin_src) not in sys.path:
        sys.path.insert(0, str(plugin_src))

    from yantrikdb import YantrikDB, TenantManager
    _YantrikDB = YantrikDB
    _TenantManager = TenantManager
    return _YantrikDB, _TenantManager
```

**Store via direct SQLite (not `record()`):** Because the ingest queue is unreliable, always use `_store_direct_sqlite()` for `yantrikdb_store` tool calls. Generate embeddings with `db.embed()`, pack with `struct.pack(f'{len(emb)}f', *emb)`, and insert raw SQL. This is the ONLY reliable write path.

**Recall with safe `top_k`:** YantrikDB's `recall()` generates `SELECT ... WHERE rid IN (...)` with one parameter per result. SQLite's parameter limit is 32,766. Cap `top_k` at 25 in the provider to avoid this. For larger result sets, make multiple smaller calls.

**Prefetch returns formatted text:** The `prefetch()` method should return a string (not a list) that gets injected into the system prompt. Format as markdown with truncated text snippets.

**Tool schemas to expose:**
- `yantrikdb_recall` — semantic search with `query`, `namespace`, `top_k` (max 25)
- `yantrikdb_store` — save memory with `text`, `memory_type`, `importance`, `namespace`, `domain`, `source`

**Registration:** End the module with `register_memory_provider()` returning a `YantrikDBMemoryProvider()` instance. The plugin loader calls this to activate the provider.

### Complete Provider Skeleton

```python
class YantrikDBMemoryProvider(MemoryProvider):
    _db = None
    _db_path = None
    
    @property
    def name(self): return "yantrikdb"
    
    def is_available(self):
        try:
            _load_yantrikdb()
            return True
        except Exception:
            return False
    
    def initialize(self, session_id, **kwargs):
        YantrikDB, _ = _load_yantrikdb()
        hermes_home = kwargs.get("hermes_home", str(Path.home() / ".hermes"))
        self._db_path = Path(hermes_home) / "yantrikdb_copy.db"
        self._db = YantrikDB.with_default(str(self._db_path))
    
    def shutdown(self):
        if self._db:
            self._db.close()
            self._db = None
    
    def system_prompt_block(self):
        return "You have access to YantrikDB cognitive memory..."
    
    def prefetch(self, query, session_id=''):
        if not self._db: return ""
        try:
            results = self._db.recall(query, namespace="cerebrum_tips", top_k=5)
            if not results: return ""
            lines = ["### Relevant learned behaviors:"]
            for r in results:
                lines.append(f"- {r.get('text', '')[:200]}")
            return "\n".join(lines)
        except Exception:
            return ""
    
    def get_tool_schemas(self):
        return [RECALL_SCHEMA, STORE_SCHEMA]
    
    def handle_tool_call(self, tool_name, arguments):
        if tool_name == "yantrikdb_recall":
            return self._handle_recall(arguments)
        elif tool_name == "yantrikdb_store":
            return self._store_direct_sqlite(**arguments)
        return json.dumps({"success": False, "error": "Unknown tool"})
    
    def _handle_recall(self, args):
        query = args.get("query", "")
        namespace = args.get("namespace", "")
        top_k = min(args.get("top_k", 5), 25)  # SAFE cap
        results = self._db.recall(query, namespace=namespace or None, top_k=top_k)
        formatted = [{"text": r.get("text", "")[:500], ...} for r in results]
        return json.dumps({"success": True, "results": formatted, "count": len(formatted)})
    
    def _store_direct_sqlite(self, text, memory_type="semantic", importance=0.5,
                             namespace="default", domain="general", source="session"):
        import sqlite3, struct
        emb = self._db.embed(text)
        emb_blob = struct.pack(f"{len(emb)}f", *emb)
        rid = f"manual_{int(time.time() * 1000)}"
        now = time.time()
        conn = sqlite3.connect(str(self._db_path))
        c = conn.cursor()
        c.execute("INSERT INTO memories (...) VALUES (...)", (...))
        conn.commit()
        conn.close()
        return json.dumps({"success": True, "stored": True})

def register_memory_provider():
    return YantrikDBMemoryProvider()
```

## Verification

```python
# Check namespace contents
existing = ydb.list_memories(namespace="cerebrum_tips")
print(f"Memories in namespace: {len(existing)}")

# Check by metadata
for mem in existing:
    if isinstance(mem, dict) and "metadata" in mem:
        meta = mem["metadata"]
        if isinstance(meta, dict):
            print(f"  cerebrum_id={meta.get('cerebrum_id')}")
```

## Pitfalls

- **Ingest queue limit (256 ops):** The #1 blocker for bulk imports. Use small batches + `think()` flush.
- **Timeout on large imports:** 600s terminal timeout may not be enough for 1,000+ records. Use background script or smaller batch sizes.
- **No `nohup` in Hermes terminal:** Hermes rejects shell-level backgrounding. Use `terminal(background=true)` for daemon-style processes.
- **Embedder must be set before any record() call:** `YantrikDB(path)` without embedder throws `RuntimeError: No embedder configured`. Use `with_default()` or `set_embedder_named()` immediately after construction.
- **`list_memories()` returns mixed types:** Some entries are `dict`, some may be `str`. Always check `isinstance(mem, dict)` before accessing fields.
- **Duplicate records from partial migrations:** When a migration is interrupted and restarted, already-migrated records may be re-inserted. Use deterministic RIDs (e.g., `cerebrum_{id:08d}`) and check existing IDs before inserting. After migration, verify: `SELECT COUNT(DISTINCT json_extract(metadata, '$.cerebrum_id'))` should equal total tips; if `COUNT(*)` is higher, duplicates exist.
- **SQLite IN clause limit (32,766 params):** `recall()` with `top_k > 1000` on large databases generates `SELECT ... WHERE rid IN (...)` with thousands of parameters, exceeding SQLite's limit. Use `top_k <= 500` or query in multiple smaller calls.
- **`record_batch()` signature mismatch:** `record_batch(inputs)` takes a list of **dicts**, not tuples. And it does NOT accept `namespace` as a keyword arg — the namespace must be inside each dict. `record_batch([{'text': 'x', 'namespace': 'foo'}])` works; `record_batch(batch, namespace='foo')` fails with "unexpected keyword argument 'namespace'". Contrast with `record(text='x', namespace='foo')` which DOES accept `namespace` as a kwarg.
- **Shell heredoc escaping in terminal tool:** Writing multi-line Python via `cat << 'EOF'` in Hermes terminal often fails with `eval: line N: unexpected EOF` due to quote/escape handling. Use `write_file` to create scripts, then `python3 /path/to/script.py` to execute. Never use heredocs with special characters (`$`, backticks, `"`) in the terminal tool.
- **Loop detection self-rescue:** Hermes has aggressive loop detection (50+ repetitions). When terminal fails 5+ times with identical args, the tool is hard-stopped. The only recovery is to change strategy entirely — different tool, different command, or write a file and execute it.

## References

- `references/direct-sqlite-insert.md` — Emergency workaround when the ingest queue is permanently stuck. Full working script with embedding generation, schema details, and post-migration index rebuild.
- `references/sqlite-in-clause-limit.md` — `recall()` fails with `top_k > 1000` on large databases due to SQLite's 32,766 parameter limit. Workarounds and safe `top_k` values.
- `references/rust-extension-rebuild.md` — Step-by-step recipe for rebuilding YantrikDB's Rust extension when the compiled `.so` is for a different Python version than the one Hermes runs on. Includes maturin commands, verification steps, and common error workarounds.
- `references/session-commit-script.md` — Manual script to copy `~/.hermes/{MEMORY.md,SOUL.md,USER.md,MASTER.md}` into the git repo (`docs/context/`) and commit them. Respects user constraint against autonomous processes without permission. Never commits credentials or DBs.

## Related

- `hermes-memory-providers` — Hermes' built-in memory provider system (Honcho, Hindsight, Holographic, etc.)
- `cerebrum-memory` — Cerebrum biologically-inspired memory system
- `hermes-cron-infrastructure` — For scheduling periodic `think()` and import jobs
