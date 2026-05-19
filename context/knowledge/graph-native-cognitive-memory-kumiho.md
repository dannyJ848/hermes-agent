# graph-native-cognitive-memory-kumiho

*Researched: 2026-04-05 04:55 CDT*

# Graph-Native Cognitive Memory for AI Agents (Kumiho)

**Source:** arXiv:2603.17244v1 (March 2026) by Young Bin Park / Kumiho Inc.

## Key Innovation
A graph-native cognitive memory architecture grounded in **formal AGM belief revision semantics** — the first system to formally prove satisfaction of belief revision postulates (K*2–K*6, Hansson's Relevance/Core-Retainment) in a property graph memory system.

## Architecture: Dual-Store Model
- **Working Memory:** Redis (library-level fast access)
- **Long-Term Memory:** Neo4j property graph (versioned, typed edges)
- **Item–Revision Model:** Immutable revisions with mutable tag pointers
- **Edge System:** Reasoning as first-class structure (typed dependency edges)

## Belief Revision Formalism
- Maps AGM postulates onto graph operations
- Uses simple propositional logic over ground triples (avoids Flouris impossibility)
- Explicitly rejects Recovery postulate (grounded in immutable versioning)
- Open questions: supplementary postulates K*7, K*8

## Dream State: Asynchronous Consolidation
- **9-stage consolidation pipeline** (event-driven)
- LLM assessment protocol for belief verification
- Safety guards during consolidation
- LLM-decoupled operation (consolidation doesn't require active LLM)

## Hybrid Retrieval
- Two-branch pipeline: fulltext + vector
- Max-fusion for score combination
- Non-degradation under corpus growth
- Client-side LLM reranking

## Relevance to Evey's Cerebrum
1. **AGM postulates** could formalize our F-G-R Trust Tuple scoring
2. **9-stage consolidation pipeline** is more rigorous than our current 4-tier decay
3. **Item–Revision model** with immutable versions solves memory overwrite issues
4. **Dream state** concept (async consolidation) validates our subconscious loop approach
5. **BYO-Storage** architecture mirrors our SQLite + Qdrant approach

## MCP Integration
Native MCP tool taxonomy with atomic memory writes and human auditability — directly relevant to Hermes plugin architecture.

## Benchmark Performance
- 89.61% on LoCoMo benchmark (matching Hindsight)
- 91.4% on extended evaluation
- Token compression validated


## Sources

- https://arxiv.org/html/2603.17244v1
