# a-mem-zettelkasten-agent-memory

*Researched: 2026-04-05 05:13 CDT*

# A-MEM: Agentic Memory Using Zettelkasten (NeurIPS 2025)

**Source:** arXiv:2502.12110 (NeurIPS 2025) — Wujiang Xu et al.
**Code:** https://github.com/agiresearch/A-MEM

## Core Innovation
Zettelkasten-inspired memory system that creates interconnected knowledge networks through dynamic indexing and linking. Published at NeurIPS 2025.

## Architecture: 3 Core Operations

### 1. Note Construction
When new memory is added, generates a comprehensive note with:
- Contextual descriptions
- Keywords
- Tags
- Structured attributes

### 2. Link Generation
Analyzes historical memories to identify relevant connections. Establishes links where meaningful similarities exist — creating a knowledge graph organically.

### 3. Memory Evolution
As new memories are integrated, they trigger **updates to existing memories' contextual representations and attributes**. The memory network continuously refines its understanding.

## Key Results
- **85-93% token reduction** vs baseline approaches
- Each memory operation costs < $0.0003
- Superior performance on 6 foundation models vs SOTA baselines
- Tested on SQA (Scientific Question Answering), MU, and other benchmarks

## Zettelkasten Principles Applied
1. **Atomic notes**: Each memory is a self-contained unit
2. **Linking**: Notes connect to related notes via semantic similarity
3. **Index**: Dynamic index structure for efficient navigation
4. **Evolution**: Notes update as understanding deepens (not just static storage)

## Relevance to Cerebrum/Evey

| A-MEM Feature | Our Current State | Improvement Opportunity |
|---|---|---|
| Note construction | Basic memory entries | Add structured attributes (keywords, tags, context) |
| Link generation | Honcho semantic search | Build explicit link table between related memories |
| Memory evolution | Decay-based only | Add: new memories update old memories' context |
| Token reduction | N/A | Evaluate if linking reduces retrieval costs |

## Implementation Idea for Cerebrum
Add a `memory_links` table to cerebrum_memory.db:
- `source_id → target_id` with `link_type` (supports, contradicts, elaborates, contextualizes)
- When storing new memory, run similarity search and auto-generate links
- When retrieving, follow links to get related context (like Zettelkasten browsing)
- This turns flat memory into a knowledge graph

This is a concrete, buildable improvement that directly addresses the gap identified in the 3-axis framework research.


## Sources

- https://arxiv.org/abs/2502.12110
- https://openreview.net/forum?id=FiM0M8gcct
