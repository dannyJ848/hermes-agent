# sqlite-agent-memory-patterns

*Researched: 2026-04-08 02:11 CDT*

# SQLite & Agent Memory Patterns (2025-2026)

## Key Insight
Letta benchmarks show plain filesystem scores 74% on memory tasks, beating specialized vector-store libraries. For agent memory, SQLite + FTS5 + simple schemas outperform complex vector DB pipelines at small-medium scale.

## Architecture Patterns
1. **Tulving's Taxonomy Applied:** Semantic (facts), Episodic (sessions), Procedural (skills) — maps directly to SQLite tables
2. **Cost Reality:** Full retrieval pipeline (embed + rerank + LLM) costs $0.002-0.01/query at low volume
3. **Reflect Pattern:** Session-end learning loops emerging as standard — matches our distillation pipeline
4. **Knowledge Graphs:** Temporal KGs (Zep/Graphiti) add value mainly for multi-agent, not single-agent
5. **SQLite FTS5:** Sufficient for most agent memory queries; vector search only needed for semantic similarity

## Relevance to Hermes/Cerebrum
- Our cerebrum_memory.db (212 nodes, 538 edges, 135 tips) validates the SQLite approach
- FTS5 session search is fast and free — no embedding cost
- The distilled_tips table is effectively procedural memory
- The kg_nodes/kg_edges tables are lightweight semantic memory without vector overhead

## Sources
- spikelab memory architecture gist (Feb 2026) — 60+ sources surveyed
- Letta/Mem0 benchmarks showing filesystem > vector stores for basic memory


## Sources

- https://gist.github.com/spikelab/7551c6368e23caa06a4056350f6b2db3
