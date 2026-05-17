# kumiho-graph-native-cognitive-memory

*Researched: 2026-04-05 08:55 CDT*

# Kumiho: Graph-Native Cognitive Memory for AI Agents (arXiv 2603.17244, Mar 2026)

**Author:** Young Bin Park / Kumiho Inc.

## Key Innovations

### 1. Graph-Native Memory with Formal Belief Revision
- Memory stored as a **property graph** with Item–Revision model (versioned memories)
- Formally grounded in **AGM belief revision semantics** — memories can be updated, contradicted, and revised with mathematical guarantees
- Avoids the Flouris Impossibility result through intentional divergence design
- Edges are first-class reasoning structures (not just links)

### 2. Nine-Stage "Dream State" Consolidation Pipeline
- Asynchronous, event-driven consolidation (like human sleep consolidation)
- LLM-assessment protocol for evaluating memory quality during consolidation
- Safety guards prevent corrupt or hallucinated memories from propagating
- **LLM-decoupled operation** — consolidation runs independently of the agent's main loop

### 3. Hybrid Retrieval (Symbolic + Sub-Symbolic)
- Two-branch pipeline: embedding-based (vector) + graph-structured (symbolic)
- Max-fusion preserves precision even as corpus grows
- Client-side LLM reranking for final selection
- Bridges symbolic and sub-symbolic representations

### 4. Memory Type Taxonomy
- Working memory: library-level fast access
- Long-term memory: property graph with versioning
- BYO-storage architecture: metadata over content (bring your own storage backend)

### 5. MCP Integration
- Atomic memory writes via Model Context Protocol
- Human-auditable memory operations
- Tool taxonomy for standardized memory access

## Relevance to Evey/Cerebrum
- Our Cerebrum's 4-tier biomimetic model shares DNA with Kumiho's approach
- **Dream State consolidation** mirrors our subconscious loop but with formal guarantees
- **Belief revision semantics** could strengthen our epistemic trust scoring (F-G-R Trust Tuple)
- **Hybrid retrieval** validates our Qdrant + Honcho dual-store approach
- AGM compliance gives a formal framework for memory conflict resolution we lack

## Benchmarks
- Evaluated on LoCoMo and LoCoMo-Plus benchmarks
- 26% improvement over Mem0 in conflict resolution (from related work comparison)
- Token compression validated in case study

## Source
- Paper: https://arxiv.org/html/2603.17244v1
- Reference implementation: Kumiho (kumiho.io)


## Sources

- https://arxiv.org/html/2603.17244v1
