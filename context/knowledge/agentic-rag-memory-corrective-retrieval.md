# agentic-rag-memory-corrective-retrieval

*Researched: 2026-04-05 06:47 CDT*

# Agentic RAG: Memory Management and Corrective Retrieval

**Source:** "Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG" — arXiv:2501.09136v4 (Apr 2026)

## Key Architectures Relevant to Cerebrum

### Corrective RAG (CRAG)
- After retrieval, an evaluator scores document quality/relevance
- If quality is low, triggers corrective actions: web search, re-retrieval, or fallback
- **Application to Cerebrum:** Before serving a memory, score its trust/relevance. If below threshold, trigger re-grounding (search for current source) or flag as uncertain.

### Adaptive Agentic RAG
- System dynamically chooses retrieval strategy based on query complexity
- Simple queries → fast retrieval; complex queries → multi-step retrieval with reflection
- **Application:** Cerebrum should have fast-path (semantic search) and deep-path (reflection + multi-source verification)

### Hierarchical Agentic RAG
- Multi-tier retrieval: router → specialist agents → synthesizer
- Maps to Cerebrum's 4-tier architecture (sensory → working → episodic → semantic)

## Practical Lessons (from §10)
1. **Retrieval quality remains the primary bottleneck** — garbage in, garbage out. Our embedding quality and chunking strategy matter more than the agent architecture.
2. **Agent autonomy requires explicit constraints** — unconstrained agents hallucinate. Trust scoring IS a constraint mechanism.
3. **Evaluation must account for process, not just outcomes** — track how memories were formed, not just whether they're useful now.
4. **Domain knowledge significantly amplifies benefits** — our medical terminology grounding gives Cerebrum an edge over generic RAG.

## Open Research Issues (§12.3)
- Memory management and long-term adaptation is identified as a key unsolved challenge
- No standard benchmarks for agent memory quality over time
- Trade-off between memory freshness and stability not well characterized

## Actionable for Cerebrum
Implement a **CRAG-inspired memory gate**: before returning a semantic fact, evaluate its trust score. If below threshold:
1. Attempt re-grounding (search for current source)
2. If re-grounding succeeds, update trust score
3. If fails, mark memory as "unverified" and decay faster
This creates a self-healing memory system.


## Sources

- https://arxiv.org/html/2501.09136v4
