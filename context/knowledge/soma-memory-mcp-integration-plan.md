# soma-memory-mcp-integration-plan

*Researched: 2026-04-03 07:09 CDT*

# SOMA Integration Plan: Memory + MCP Architecture (April 2026)

**Date:** April 3, 2026
**Synthesized from:** agent-memory-architectures-survey-2026.md, medical-mcp-ecosystem-scan-april-2026.md

## The Convergence

Two major trends converge for SOMA's architecture:

1. **Agent Memory** is moving from "stuff everything in context" to selective, structured, multi-modal memory (LOCOMO benchmark proves selective memory achieves 94% of full-context accuracy at 10x lower cost)
2. **Medical MCP Servers** are proliferating, providing standardized interfaces to medical knowledge (healthcare-mcp-public alone covers FDA, PubMed, ICD-10, clinical trials, DICOM)

## Proposed Architecture: "SOMA Memory Stack v2"

### Layer 1: Factual Memory (What SOMA knows)
**Current:** Static encyclopedia entries, hardcoded bilingual terms
**Proposed:** Hybrid approach:
- **Static core:** Anatomy facts, bilingual EN/ES terms (loaded from bundled data)
- **Dynamic enrichment:** MCP calls to healthcare-mcp-public for drug interactions, clinical guidelines
- **Storage:** On-device SQLite for cached facts, remote MCP for fresh data
- **Token budget:** ~1,800 tokens per query (per LOCOMO benchmark — 94% accuracy)

### Layer 2: Experiential Memory (What the user has learned)
**Current:** Nonexistent
**Proposed:** Learning analytics:
- Track which anatomy structures the user has explored
- Record quiz performance per topic
- Identify weak areas for adaptive review
- **Storage:** On-device SQLite, synced to cloud
- **Format:** Structured entities (per memory survey's "graph-enhanced" approach)

### Layer 3: Working Memory (Current interaction state)
**Current:** React component state (ephemeral)
**Proposed:** Persistent working memory:
- Currently selected anatomy structure + related systems
- Active exploration mode (dissection, cross-section, info panel)
- Language preference + audience level (Layman/Student/Professional)
- **Storage:** In-memory with periodic snapshots

### Layer 4: MCP Integration Layer (External knowledge)
**New component:** MCP client in SOMA app
- **Primary server:** healthcare-mcp-public (comprehensive medical data)
- **Imaging server:** mcp-slicer (3D medical image processing, potential mesh pipeline replacement)
- **Content server:** medadapt-content-server (educational content pipeline)
- **Fallback:** Bundled static data when offline

## Technical Implementation Roadmap

### Phase 1: Memory Foundation (Week 1-2)
- Add SQLite database to SOMA app for persistent storage
- Define schema for factual + experiential memory tables
- Implement basic memory CRUD operations

### Phase 2: MCP Client (Week 3-4)
- Implement MCP client in TypeScript (use @modelcontextprotocol/sdk)
- Connect to healthcare-mcp-public for drug/clinical data
- Add caching layer for offline capability

### Phase 3: Graph-Enhanced Retrieval (Week 5-6)
- Add entity-relationship extraction from anatomy data
- Build graph-based retrieval for related structures
- Implement the "explore related" feature using graph traversal

### Phase 4: Adaptive Learning (Week 7-8)
- Track user interactions per anatomy structure
- Build spaced repetition algorithm for quiz review
- Implement personalized learning path based on experiential memory

## Key Metrics to Track
- **Memory accuracy:** Test against LOCOMO-style benchmarks
- **Latency:** Target <1s for memory retrieval (per LOCOMO findings)
- **Token cost:** Target ~1,800 tokens per query (selective approach)
- **Offline capability:** Must work without MCP servers (fallback to static data)
- **Mobile performance:** Memory operations must not block UI thread

## Risk Assessment
- **MCP server availability:** External servers may go down → mitigated by caching
- **Privacy:** Medical queries contain sensitive data → all MCP calls must be anonymous
- **Mobile constraints:** SQLite + graph operations on mobile → benchmark before committing
- **Spanish language coverage:** MCP servers primarily serve English content → need translation layer (GEPA-optimized prompts?)


## Sources

- https://arxiv.org/abs/2512.13564
- https://mem0.ai/blog/state-of-ai-agent-memory-2026
- https://github.com/sunanhe/awesome-medical-mcp-servers
- https://github.com/Cicatriiz/healthcare-mcp-public
