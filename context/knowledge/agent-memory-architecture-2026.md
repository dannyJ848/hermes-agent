# agent-memory-architecture-2026

*Researched: 2026-04-12 18:57 CDT*

# Agent Memory Architecture Research (Apr 2026)

## SYNAPSE (arXiv 2601.02744) — Spreading Activation Memory
- **Authors**: Hanqi Jiang et al., Jan 2026
- **Key Innovation**: Memory as dynamic graph where relevance emerges from *spreading activation* rather than pre-computed similarity links
- **Triple Hybrid Retrieval**: Fuses geometric embeddings with activation-based graph traversal
- **Features**: Lateral inhibition + temporal decay to highlight relevant sub-graphs while filtering interference
- **Benchmark**: Significantly outperforms SOTA on LoCoMo benchmark for temporal and multi-hop reasoning
- **Solves**: "Contextual Tunneling" problem — where agents get stuck in narrow context windows

## Multi-Layer Memory Framework (arXiv 2603.29194) — Mar 2026
- **Authors**: Payal Fofadiya, Sunil Tiwari
- **Architecture**: Working → Episodic → Semantic layers with adaptive retrieval gating
- **Key Technique**: Retention regularization prevents semantic drift across sessions
- **Results**: 46.85% success rate, 0.618 F1, 56.90% six-period retention, false memory rate only 5.1%
- **Context efficiency**: Only 58.40% context usage — huge savings
- **Relevance**: Directly applicable to Hermes' cerebrum memory architecture (sensory→working→episodic→semantic)

## Implications for Hermes Cerebrum
1. **Spreading activation** could replace pure cosine-similarity retrieval in cerebrum — relevance propagates through graph edges
2. **Lateral inhibition** prevents memory interference — one concept doesn't bleed into unrelated ones
3. **Retention regularization** — formal loss function for forgetting that we could apply to memory_decay
4. **Adaptive retrieval gating** — only promote working→episodic when confidence threshold met
5. **Context budget tracking** — we should measure context utilization % not just raw token count

## Agent Memory Paper List (GitHub: Shichun-Liu/Agent-Memory-Paper-List)
- Actively maintained with 2026 papers
- MemRL: Self-evolving agents via runtime RL on episodic memory (Jan 2026)
- Agentic Memory: Unified long-term and short-term memory (Jan 2026)


## Sources

- https://arxiv.org/abs/2601.02744
- https://arxiv.org/html/2603.29194v1
- https://github.com/Shichun-Liu/Agent-Memory-Paper-List
