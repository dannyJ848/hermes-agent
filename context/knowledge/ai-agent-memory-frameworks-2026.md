# ai-agent-memory-frameworks-2026

*Researched: 2026-04-05 02:16 CDT*

# AI Agent Memory Frameworks Comparison (Apr 2026)

## Key Benchmarks (LongMemEval)
- Zep/Graphiti: 63.8% — temporal knowledge graph
- Mem0: 49.0% — dual store (vector + entity graph)
- Letta/MemGPT: OS-inspired tiered memory
- LangMem: LangChain-native

## Architecture Patterns
1. **Temporal Knowledge Graph** (Zep/Graphiti): Best for temporal reasoning. Edges have timestamps. Can answer "what did X say about Y last week?"
2. **Dual Store** (Mem0): Vector DB for similarity + Entity Graph for relationships. LLM judge for conflict resolution.
3. **Self-Managing** (Letta): LLM decides what to remember/forget via function calls.
4. **HRR + Trust** (Our Cerebrum): Holographic reduced representations with trust scoring.

## Our Gap
We have: facts with trust scores, experiences with lessons, tips with votes
We lack: Entity-relationship connections between facts

## Recommended: Lightweight Entity Graph in SQLite
```sql
CREATE TABLE entities (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    type TEXT, -- person, tool, project, concept, file
    first_seen REAL,
    last_seen REAL,
    mention_count INTEGER DEFAULT 1
);

CREATE TABLE relationships (
    id INTEGER PRIMARY KEY,
    source_id INTEGER REFERENCES entities(id),
    target_id INTEGER REFERENCES entities(id),
    rel_type TEXT, -- uses, depends_on, related_to, owns, created
    strength REAL DEFAULT 0.5,
    evidence TEXT,
    first_seen REAL,
    last_seen REAL,
    FOREIGN KEY (source_id) REFERENCES entities(id),
    FOREIGN KEY (target_id) REFERENCES entities(id)
);
```

## Implementation Priority
LOW. Our current system works well enough for single-agent operation. Entity graph becomes important for multi-agent coordination or complex reasoning across domains. Current MEMORY domain focus should be on grounding low-trust facts, not building new infrastructure.


## Sources

- https://atlan.com/know/best-ai-agent-memory-frameworks-2026/
- https://www.reddit.com/r/singularity/comments/1pn803k/lessons_from_building_a_knowledge_graph_memory/
