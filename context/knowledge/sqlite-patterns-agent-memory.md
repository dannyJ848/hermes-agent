# sqlite-patterns-agent-memory

*Researched: 2026-04-08 01:06 CDT*

# SQLite Patterns for Agent Memory Persistence

## Key Finding (2025-2026 Landscape)

SQLite remains the dominant structured persistence layer for AI agents, competing with PAG (agent-graph oriented) and MEMORY.md (file-backed conversational memory).

### Three Approaches Compared:
1. **SQLite** — Structured relational store for durable, queryable data. Best for: knowledge graphs, distilled tips, health logs, session metadata. Scales to GB with WAL mode.
2. **PAG (Persistent Agent Graph)** — Agent-graph oriented persistence for complex relational queries between agent states. Best for multi-agent distributed systems.
3. **MEMORY.md** — File-backed episodic memory. Simple, human-readable. Best for lightweight conversational context.

### SQLite Patterns for Agent Systems:
- **WAL mode** for concurrent read/write without blocking
- **FTS5** for full-text search across memories and sessions
- **JSON columns** for flexible semi-structured data (tool results, metadata)
- **Batch inserts with transactions** for bulk knowledge ingestion
- **Prepared statements** for repeated query patterns (session lookup, tip retrieval)
- **Connection pooling** with timeout for multi-threaded access
- **Aggressive VACUUM** during maintenance windows to reclaim space

### Memory Architecture Layers:
- **Episodic** (past interactions) — session transcripts
- **Semantic** (learned facts) — knowledge graph nodes/edges
- **Procedural** (learned skills) — distilled tips with confidence scores

### Relevance to Hermes Agent:
Our cerebrum_memory.db uses all three memory types via SQLite:
- `kg_nodes` / `kg_edges` = semantic memory (212 nodes, 538 edges)
- `distilled_tips` = procedural memory (88 high-confidence tips)
- `stop_detection_log` / `health_checks` = operational telemetry

### Improvement Opportunities:
- Add FTS5 virtual tables on kg_nodes for natural language retrieval
- Implement WAL mode if not already active
- Consider JSON columns for flexible tool result storage
- Batch tip distillation into single transactions

Source: Sparkco AI technical evaluation (Feb 2026)


## Sources

- https://sparkco.ai/blog/persistent-memory-for-ai-agents-comparing-pag-memorymd-and-sqlite-approaches
