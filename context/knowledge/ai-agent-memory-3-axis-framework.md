# ai-agent-memory-3-axis-framework

*Researched: 2026-04-05 05:12 CDT*

# AI Agent Memory Systems: 3-Axis Framework (Hu et al. 2025 + Kinney 2026)

**Sources:**
- Hu et al., "Memory in the Age of AI Agents" (Dec 2025, 107-page survey)
- Steve Kinney, "Memory Systems for AI Agents" (March 31, 2026)

## The Old Taxonomy is Dead
Short-term vs long-term memory doesn't capture what modern agent memory does.

## New 3-Axis Framework: Forms × Functions × Dynamics

### Forms (Where does memory live?)
- Text-based (natural language)
- Structured (key-value, triples, tables)
- Embeddings (vector stores)
- Parameterized (model weights/fine-tuning)

### Functions (Why does the agent need memory?)
- Identity: Who am I? What are my preferences?
- Context: What's the current task? What happened recently?
- Knowledge: Domain facts, procedures, skills
- Social: User preferences, interaction patterns

### Dynamics (How does memory operate over time?)
- **Reading**: How is memory retrieved? (similarity search, recency, importance)
- **Writing**: How is memory stored? (extraction, consolidation, compression)
- **Refinement**: How does memory evolve? (decay, contradiction resolution, merging)
- **Forgetting**: How is memory pruned? (importance decay, relevance filtering)

## Key Research Highlights
- **A-Mem**: Zettelkasten-style linked notes → 85-93% token reduction
- **StructMemEval**: Simple retrieval can outperform complex hierarchies
- **Memori**: Semantic triples → 81.95% accuracy at 5% of full context cost

## Relevance to Cerebrum/Evey Architecture

| Research Concept | Our Implementation | Gap |
|---|---|---|
| Forms: Text + Vectors | MEMORY.md (text) + Honcho (vectors) | Missing structured triples |
| Functions: Identity | SOUL.md + identity updates | ✅ Covered |
| Functions: Context | Session context + working memory | ✅ Covered |
| Functions: Knowledge | Knowledge base + skills | ✅ Covered |
| Dynamics: Refinement | Decay scoring + consolidation | Missing contradiction resolution |
| Dynamics: Forgetting | memory_decay tool | ✅ Covered |

## Actionable: Implement Contradiction Detection
When storing new semantic memory, compare against existing memories using embedding similarity. If similarity > 0.85 but content differs significantly, flag as contradiction and queue for resolution rather than storing both.


## Sources

- https://stevekinney.com/writing/agent-memory-systems
- https://arxiv.org/abs/2504.XXXXX
