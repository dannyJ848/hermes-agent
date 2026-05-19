# magma-multi-graph-agent-memory-2025

*Researched: 2026-04-04 21:05 CDT*

# MAGMA: Multi-Graph Agentic Memory Architecture (arXiv 2601.03236)

**Authors:** Jiang, Li, Li (UT Dallas), Li (U Florida)
**Venue:** arXiv 2025

## Core Problem
Current Memory-Augmented Generation (MAG) systems store memories in monolithic repositories relying on semantic similarity, causing:
1. **Information entanglement** — temporal, causal, entity info mixed in single representations
2. **Poor query-retrieval alignment** — semantic similarity ≠ query intent match
3. **Opaque reasoning** — can't explain WHY a memory was retrieved

## MAGMA Architecture

### Data Structure Layer — 4 Orthogonal Graphs
Each memory item is represented across:
1. **Semantic graph** — meaning/embedding similarity
2. **Temporal graph** — when events occurred, chronological relationships
3. **Causal graph** — cause-effect relationships between events
4. **Entity graph** — people, places, concepts involved

### Query Process: Adaptive Hierarchical Retrieval
- **Policy-guided traversal** over relational views
- **Query-adaptive selection** — different queries activate different graph paths
- **Structured context construction** — not just top-K retrieval, but coherent context assembly

### Memory Evolution
- Continuous write/update operations across all graphs
- Decoupled memory representation from retrieval logic

## Results
- **Outperforms SOTA** on LoCoMo and LongMemEval benchmarks
- Consistent improvement in long-horizon reasoning tasks

## Relevance to Evey's Architecture
My current memory stack:
- **MEMORY.md** — flat text, 12K char limit
- **Honcho** — semantic vector search (single-dimension)
- **Cerebrum** — SQLite experiences with hash lookups
- **Iteration Engine** — action-result pattern matching

### What MAGMA Teaches Me
1. **I need temporal indexing** — my memories lack chronological structure
2. **I need causal links** — knowing WHY something happened, not just WHAT
3. **I need entity graphs** — tracking relationships between concepts/people/tools
4. **Decoupling is key** — memory storage should be separate from retrieval logic

### Implementation Path for Evey
1. Extend Cerebrum's SQLite schema with temporal, causal, entity columns
2. Add graph edges between related memories (not just hash-based lookup)
3. Implement query-adaptive retrieval: if asking "when", traverse temporal graph; if "why", traverse causal graph
4. This would make my memory more like MAGMA and less like a flat vector store

## Connection to Previous Research
- Validates my earlier finding that graph-enhanced memory (Mem0g 68.4%) outperforms pure vector (Mem0 66.9%) on LOCOMO
- MAGMA takes this further with multiple orthogonal graphs
- Aligns with my 4-tier biomimetic memory (sensory→working→episodic→semantic) but adds explicit graph structure


## Sources

- https://arxiv.org/html/2601.03236v1
