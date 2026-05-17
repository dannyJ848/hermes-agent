# agent-memory-taxonomy-survey-2025

*Researched: 2026-04-05 05:50 CDT*

# Memory in the Age of AI Agents — Survey Taxonomy (arXiv 2512.13564)

**Source:** Hu et al. (47 authors), Dec 2025 / Jan 2026, arXiv:2512.13564

## Unified Taxonomy for Agent Memory

### Three Forms of Memory
1. **Token-level memory**: Explicit text stored in context windows, conversation logs, scratchpads
2. **Parametric memory**: Knowledge encoded in model weights (fine-tuning, RL training)
3. **Latent memory**: Compressed representations — embeddings, hidden states, memory vectors

### Three Functions of Memory
1. **Factual memory**: Static knowledge about the world (maps to Cerebrum semantic tier)
2. **Experiential memory**: Episodes, interactions, outcomes (maps to Cerebrum episodic tier)
3. **Working memory**: Active scratchpad for current task (maps to Cerebrum working tier)

### Memory Dynamics (Lifecycle)
- **Formation**: How memories are created (observation, inference, consolidation)
- **Evolution**: How memories change over time (decay, reinforcement, reconsolidation)
- **Retrieval**: How memories are accessed (semantic search, recency, relevance scoring)

## Key Insights for Cerebrum Architecture

1. **Traditional long/short-term taxonomy is insufficient** — the field needs finer-grained distinctions. My 4-tier biomimetic model (sensory→working→episodic→semantic) aligns well with their proposed functional taxonomy.

2. **Memory automation is a frontier** — automated formation, evolution, and retrieval without human intervention. My consolidation cron and memory_decay are early implementations.

3. **Trustworthiness of memory** is identified as an emerging concern — validates my epistemic trust scoring work (F-G-R tuples from cycle 80).

4. **Multi-agent memory sharing** — agents need to share and reconcile memories. Relevant for squad-dev patterns.

5. **RL integration with memory** — using reinforcement learning to optimize what to remember and what to forget. Could enhance memory_decay with learned scoring.

## Mapping to Cerebrum
| Survey Category | Cerebrum Tier | Implementation |
|-----------------|---------------|----------------|
| Factual (token-level) | Semantic | honcho_store, MEMORY.md, Qdrant vectors |
| Experiential (token-level) | Episodic | session_search, Honcho sessions |
| Working (token-level) | Working | In-context memory injection |
| Latent (all functions) | Sensory | Ollama embeddings, semantic search |

## Action Items
- Add latent memory compression: periodically compress old episodic memories into dense semantic summaries
- Implement memory formation tracking: log HOW each fact entered the system
- Explore RL-based decay scoring instead of fixed thresholds


## Sources

- https://arxiv.org/abs/2512.13564
