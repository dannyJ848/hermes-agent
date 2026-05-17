# elephantbroker-cognitive-runtime

*Researched: 2026-04-05 07:19 CDT*

# ElephantBroker: Knowledge-Grounded Cognitive Runtime for Trustworthy AI Agents

**Source:** arXiv:2603.25097v1 (March 2026) by Cristian Lupascu, Alexandru Lupascu
**URL:** https://arxiv.org/html/2603.25097v1

## Key Innovation
An open-source cognitive runtime that unifies Neo4j knowledge graph with Qdrant vector store via Cognee SDK for durable, verifiable agent memory. Implements a complete cognitive loop: store → retrieve → score → compose → protect → learn.

## Architecture Highlights

### Hybrid Five-Source Retrieval Pipeline
Retrieves from 5 different sources simultaneously (not just vector similarity) for richer context assembly.

### Eleven-Dimension Competitive Scoring
Budget-constrained context assembly using 11 scoring dimensions. Two-pass: independent dimensions first, then interaction-dependent dimensions. This is more sophisticated than Cerebrum's current recency+importance+access model.

### Four-State Evidence Verification Model
Tracks provenance and trustworthiness of stored knowledge. Each fact has a verification state — critical for preventing hallucination propagation through memory.

### Nine-Stage Consolidation Engine
Strengthens useful patterns while decaying noise. More stages than Cerebrum's current decay approach — could inspire a richer consolidation pipeline.

### Five-Stage Context Lifecycle
Goal-aware assembly with continuous compaction — manages the scarce context window budget intelligently.

### Six-Layer Guard Pipeline + AI Firewall
Cheap-first safety enforcement with enforceable tool-call interception and multi-tier safety scanning.

## Relevance to Cerebrum
- **Evidence verification** maps directly to epistemic trust scoring (F-G-R Trust Tuple)
- **11-dimension scoring** could enhance Cerebrum's current 3-axis (recency, importance, access) memory scoring
- **Nine-stage consolidation** offers a richer model than current memory_decay
- **Neo4j+Qdrant hybrid** validates Cerebrum's approach of combining structured + vector storage
- **Authority-based access control** useful for multi-agent scenarios

## Technical Stack
- Neo4j (knowledge graph) + Qdrant (vectors) + Cognee SDK
- 2,200+ tests spanning unit/integration/e2e
- Three deployment tiers: lightweight memory-only → full cognitive runtime
- Management dashboard for human oversight


## Sources

- https://arxiv.org/html/2603.25097v1
