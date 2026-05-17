# agent-memory-frameworks-2026

*Researched: 2026-04-12 04:38 CDT*

# AI Agent Memory Frameworks (2026 Landscape)

**Source:** MachineLearningMastery, April 2026

## Top 6 Frameworks

1. **Mem0** — Dedicated memory layer with multi-level scope (user/session/agent), vector search + metadata filtering, version control for memories
2. **Zep** — Long-term memory for conversational AI. Extracts entities/intents/facts, progressive summarization, semantic + temporal search
3. **LangGraph** — Stateful agent framework with checkpointing and graph-based workflows
4. **Memary** — Open-source memory layer with knowledge graph integration
5. **Letta** — Stateful agent framework with archival memory and recall mechanisms
6. **Cognos** — Cognitive memory architecture inspired by human memory systems

## Key Patterns

- Multi-level scoping (user/session/agent) is now standard
- Hybrid retrieval (vector + metadata + temporal) outperforms pure vector search
- Progressive summarization prevents context overflow
- Knowledge graphs enable associative recall across domains
- Memory versioning allows rollback and audit trails

## Relevance to Hermes

Our cerebrum system already implements most of these patterns:
- Multi-level: episodic/semantic/procedural/distilled
- Hybrid retrieval: SQLite FTS5 + semantic vectors
- Progressive summarization: context_compressor.py
- Knowledge graph: kg_nodes + kg_edges tables
- Gap: Memory versioning (no rollback currently)


## Sources

- https://machinelearningmastery.com/the-6-best-ai-agent-memory-frameworks-you-should-try-in-2026/
