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
- `think()` after every ~100 records (5 batches of 20) keeps queue clear
- `stats()` before/after `think()` shows `active_memories` increasing and `operations` incrementing
- Without `think()`, queue fills at ~250 records regardless of sleep time
- `record_batch()` with 20-item batches + `think()` every 5 batches = sustainable throughput

**`stats()` shows queue state:**
```python
stats = ydb.stats()
# 'operations': total ops processed
# 'vec_index_entries': memories with embeddings
# 'active_memories': total in DB
```

If `operations` stops increasing between calls, the queue is stalled.

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
- **Async processing means immediate `recall()` may miss just-recorded items:** Call `think()` or wait a few seconds before verifying.
- **Graph index (`edges`, `entities`) only populates after `think()`:** `stats()` shows `edges: 0` until consolidation runs.
- **Shell heredoc escaping in terminal tool:** Writing multi-line Python via `cat << 'EOF'` in Hermes terminal often fails with `eval: line N: unexpected EOF` due to quote/escape handling. Use `write_file` to create scripts, then `python3 /path/to/script.py` to execute. Never use heredocs with special characters (`$`, backticks, `"`) in the terminal tool.
- **Loop detection self-rescue:** Hermes has aggressive loop detection (50+ repetitions). When terminal fails 5+ times with identical args, the tool is hard-stopped. The only recovery is to change strategy entirely — different tool, different command, or write a file and execute it.

## Related

- `hermes-memory-providers` — Hermes' built-in memory provider system (Honcho, Hindsight, Holographic, etc.)
- `cerebrum-memory` — Cerebrum biologically-inspired memory system
- `hermes-cron-infrastructure` — For scheduling periodic `think()` and import jobs
