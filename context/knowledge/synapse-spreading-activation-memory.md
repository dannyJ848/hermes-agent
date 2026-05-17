# synapse-spreading-activation-memory

*Researched: 2026-04-05 06:10 CDT*

# Synapse: Spreading Activation for Agent Memory (Jan 2026, arXiv 2601.02744)

## Key Innovation
Synapse replaces static vector similarity retrieval with **spreading activation** over a unified episodic-semantic graph — directly inspired by cognitive science models of human memory.

## Architecture
- **Unified Episodic-Semantic Graph**: Episodes and semantic facts coexist as nodes with typed edges
- **Spreading Activation**: Relevance emerges dynamically via activation propagation, not pre-computed similarity
- **Lateral Inhibition**: Suppresses interference from irrelevant sub-graphs during retrieval
- **Temporal Decay**: Older memories lose activation naturally
- **Triple-Signal Hybrid Retrieval**: Fuses geometric embeddings (vector similarity) + activation-based graph traversal + a third signal

## Cognitive Mechanisms
1. **Initialization**: Query activates seed nodes
2. **Propagation with Fan Effect**: Activation spreads to connected nodes, diminishing with distance
3. **Lateral Inhibition**: Competing paths suppress each other (focuses retrieval)
4. **Sigmoid Activation**: Non-linear gating prevents runaway activation

## Key Results (LoCoMo Benchmark)
- Outperforms SOTA on complex temporal reasoning tasks
- Outperforms SOTA on multi-hop reasoning tasks
- Solves "Contextual Tunneling" problem (over-focus on narrow context)
- More token-efficient than exhaustive-context baselines
- Stronger advantage on weaker LLM backbones

## Relevance to Cerebrum
- Cerebrum's 4-tier architecture (sensory→working→episodic→semantic) already implements episodic-semantic separation
- **Missing piece**: Spreading activation for retrieval — Cerebrum currently uses vector similarity only
- **Lateral inhibition** could improve recall precision by filtering noise
- **Temporal decay** matches Cerebrum's existing decay mechanism but Synapse's sigmoid gating is more principled
- **Triple-signal retrieval** could replace current dual-signal (semantic + recency) approach

## Potential Integration
- Add activation scores to cerebrum_memory.db nodes
- Implement spreading activation as a post-retrieval re-ranker
- Fan effect: limit propagation to 2-3 hops
- Lateral inhibition: suppress nodes below median activation after propagation

## Citation
Jiang, H., Chen, J., Pan, Y., et al. "Synapse: Empowering LLM Agents with Episodic-Semantic Memory via Spreading Activation." arXiv:2601.02744v3 (2026).


## Sources

- https://arxiv.org/html/2601.02744v3
