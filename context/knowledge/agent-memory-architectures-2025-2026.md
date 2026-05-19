# agent-memory-architectures-2025-2026

*Researched: 2026-04-04 20:50 CDT*

# Agent Memory Architectures Beyond RAG: 2025-2026

## 1. Graph-Enhanced Memory
- **GraphRAG (Microsoft)**: Two-tier graph (entity + community hierarchy), Leiden clustering, solves local scope problem
- **Mem0g**: Triple store + vector embeddings per entity, graph-aware retrieval (seed entities → 1-3 hop traversal → rerank)
- **HippoRAG 2**: Hippocampal indexing, personalized KG, RRF fusion of vector + graph scores
- **StructRAG (ICLR 2025)**: Dynamically selects best structure (graph/table/tree/algorithm) per query type
- **Key insight**: Pure vector search misses relational context. Graph traversal captures entity connections that similarity search can't.

## 2. Episodic Memory for Agents
- **ExpeL (AAAI 2025)**: Agents store trajectories → extract insights → retrieve similar-past-situation insights for new tasks
- **Three-layer pattern**: Episodic (specific experiences) → Semantic (general knowledge) → Procedural (skills)
- **Retrieval**: Embedding similarity + recency + outcome filtering
- **Key**: Store lessons learned, not raw trajectories

## 3. Memory Consolidation
- **MemoryBank (Ebbinghaus model)**: Forgetting curve R = e^(-t/S); recall boosts strength; periodic consolidation extracts semantic facts from fading episodic traces
- **Generative Replay**: LLM periodically re-summarizes accumulated memories → compressed summaries replace raw episodes
- **Synaptic Consolidation**: Accumulate interactions → fine-tune on distilled data (LoRA) → merge into weights (slow cortical learning)

## 4. Adaptive Forgetting
- **Problem without forgetting**: context pollution, storage bloat, contradiction accumulation, catastrophic retrieval
- **Expire-Span**: Learned expiration per memory; auto-deprioritize after span
- **CAFE framework**: Contradiction detection → overwrite old (version, don't delete); utility scoring = retrieval_count × avg_relevance
- **Letta/MemGPT**: Agent self-directed forgetting via explicit tool calls (core_memory_append/replace, archival_memory_insert/search)

## 5. Hybrid Retrieval
- **Consensus architecture**: Parallel retrievers (vector + BM25 + graph + SQL) → RRF fusion → reranking
- **RRF formula**: score = Σ 1/(k + rank_i) across all result lists
- **HippoRAG 2 pipeline**: OpenIE triples → entity detection → parallel KG/vector/BM25 → RRF fusion
- **Best practice**: Dense + sparse + structural retrieval combined outperforms any single method

## Practical Implications for Hermes Agent
1. Cerebrum's 4-tier model aligns with episodic→semantic consolidation (good)
2. Could benefit from graph layer on top of vector memory (entity relationships)
3. Implement generative replay: periodic LLM summarization of raw memories
4. Add contradiction detection to honcho_store (check before storing)
5. Use RRF for multi-source recall (honcho_search + knowledge_search + session_search)

## Sources

- Microsoft GraphRAG 2024-2025
- Mem0g 2025
- HippoRAG 2 (Gutiérrez et al. 2025)
- StructRAG (Zhu et al. ICLR 2025)
- ExpeL (Zhao et al. AAAI 2025)
- MemoryBank (Zhong et al. 2025)
- Letta/MemGPT 2025
