# agent-memory-taxonomy-experiential

*Researched: 2026-04-11 23:44 CDT*

# Agent Memory Taxonomy: Forms, Functions, and Dynamics

**Source:** "Memory in the Age of AI Agents" (arXiv:2512.13564, Dec 2025, revised Jan 2026)
**Authors:** Yuyang Hu + 46 others (Philip Torr, Shuicheng Yan, etc.)

## Key Taxonomy

### Memory Forms (how memory is realized):
1. **Token-level memory** — context window, conversation history, retrieved passages
2. **Parametric memory** — weights learned during training/fine-tuning (model internalization)
3. **Latent memory** — compressed representations, embeddings, latent states

### Memory Functions (what memory stores):
1. **Factual memory** — knowledge, facts, world state (like semantic memory)
2. **Experiential memory** — episode traces, past interactions, learned procedures (like episodic memory)
3. **Working memory** — scratchpad for current task, transient state

### Memory Dynamics (how memory evolves):
- **Formation** — how memories are created (observation, consolidation, distillation)
- **Evolution** — how memories change over time (decay, reinforcement, restructuring)
- **Retrieval** — how memories are accessed (recency, relevance, association)

## Relevance to Hermes/Cerebrum Architecture

Our cerebrum_memory.db implements this taxonomy:
- `distilled_tips` = experiential memory (distilled from past sessions)
- `kg_nodes/kg_edges` = factual memory (knowledge graph)
- `stop_detection_log` = working memory dynamics
- The domain_certainty.py explorer = memory evolution via active inference

## Emerging Frontiers (from paper):
- Memory automation (auto-consolidation without human triggers)
- RL integration (reinforcement learning for memory management policies)
- Multimodal memory (visual, audio, not just text)
- Multi-agent memory (shared memory between agents)
- Trustworthiness (privacy, adversarial memory injection)

## Actionable Insight
The paper validates our 3-tier cerebrum approach. Key gap: we lack **RL-based memory management** — currently using heuristic scoring. A reinforcement approach could learn which memories to keep/discard based on downstream task performance.


## Sources

- https://arxiv.org/abs/2512.13564
