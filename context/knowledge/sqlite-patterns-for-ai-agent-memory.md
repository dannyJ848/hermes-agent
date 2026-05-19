# sqlite-patterns-for-ai-agent-memory

*Researched: 2026-04-08 02:14 CDT*

# SQLite Patterns for AI Agent Memory

## Key Finding: sqlite-memory Extension (sqliteai/sqlite-memory)
A SQLite extension providing AI agents with persistent, searchable memory via:
- **Hybrid semantic search** combining vector similarity + FTS5 full-text search
- **Markdown-based memory** entries (human-readable, LLM-friendly)
- **Offline-first sync** between agents
- 23 stars on GitHub, actively maintained

## Multi-Layer Memory Architecture (Reddit/Redis+SQLite)
Tiered approach with SQLite as procedural memory layer:
- L4 Procedural (SQLite) — Patterns and skills, ~3ms latency
- Memories flow between layers based on importance and access patterns
- SQLite ideal for skill/procedural storage due to fast reads and durability

## Hybrid Retrieval Pattern
Combine FTS5 (lexical) + vector similarity (semantic) for best recall:
- FTS5 catches exact keyword matches (tool names, error codes)
- Vector search catches conceptual matches ("how to fix auth" → OAuth patterns)
- Hermes already uses this pattern in cerebrum_memory.db — validate it's optimal

## Actionable Implications for Hermes Agent
1. **cerebrum_memory.db** already uses FTS5 for session search — consider adding vector columns for hybrid search
2. **distilled_tips** could benefit from semantic deduplication (vector similarity to detect redundant tips)
3. **kg_nodes/kg_edges** graph queries could be accelerated with materialized CTEs for common traversal patterns
4. **Connection pooling** — use `timeout=5` on all connections (already doing this) plus WAL mode for concurrent reads

## Sources
- sqliteai/sqlite-memory: https://github.com/sqliteai/sqlite-memory
- AI Agent Memory with SQLite: https://www.welcomedeveloper.com/posts/ai-agent-memory-sqlite/
- Multi-layer memory (Redis+SQLite): https://www.reddit.com/r/SideProject/comments/1re4rpt/


## Sources

- https://github.com/sqliteai/sqlite-memory
- https://www.welcomedeveloper.com/posts/ai-agent-memory-sqlite/
- https://www.reddit.com/r/SideProject/comments/1re4rpt/
