# memory-consolidation-ebbinghaus-forgetting-ai-2026

*Researched: 2026-04-05 09:01 CDT*

# Memory Consolidation: Forgetting Curves & Adaptive Replay (2025-2026)

## Paper: FOREVER — Forgetting Curve-Inspired Memory Replay for LLM Continual Learning
- **Source:** Feng et al. (arXiv:2601.03938, Jan 2026)
- **Key thesis:** LLM forgetting mirrors the Ebbinghaus human forgetting curve. Memory replay schedules should align with model-centric time (optimizer update magnitude) rather than raw training steps.
- **Two components:**
  1. **Forgetting curve-based replay scheduler** — determines WHEN to replay based on model's internal evolution
  2. **Intensity-aware regularization** — determines HOW to replay, adaptive control of replay intensity
- **Results:** Tested on 0.6B-13B parameter models across 3 CL benchmarks, consistently mitigated catastrophic forgetting.
- **Key insight for Cerebrum:** Our memory_decay tool uses a simple threshold-based approach. FOREVER suggests a more sophisticated approach where the "decay rate" should follow an Ebbinghaus-like curve tied to actual usage patterns, not just time since last access.

## Article: The Agent's Memory Dilemma — Is Forgetting a Bug or a Feature?
- **Source:** Tao An, Medium (Nov 2025)
- **Key arguments:**
  - Perfect recall is a curse, not a blessing — causes cognitive paralysis from irrelevant memories competing for attention
  - Three critical problems from unbounded memory growth:
    1. **Retrieval cost** — semantic search latency grows with memory size
    2. **Retrieval accuracy degradation** — noise-to-signal ratio increases, disambiguation harder
    3. **Catastrophic interference** — new memories overwrite/conflict with old ones
  - RAG ≠ memory: RAG is stateless lookup ("What does the knowledge base say?"), memory is experiential ("What have I experienced?")
  - Three-layer architecture mirrors human cognition: short-term (context window), episodic (events), semantic (generalized knowledge)
- **Key insight for Cerebrum:** The article validates Cerebrum's 4-tier architecture (sensory→working→episodic→semantic) and explicitly warns against the accumulation problem we face — our semantic memory grows without bounds. The forgetting curve approach from FOREVER could improve our decay algorithm.

## ACT-R Agent Memory (ACM, 2025)
- **Source:** "Human-Like Remembering and Forgetting in LLM Agents: An ACT-R Approach" (ACM DL)
- **Could not extract full content (403)** but snippet confirms: dialogue agent with dynamic memory retrieval and forgetting based on context, time, and usage frequency — directly mapping to the ACT-R cognitive architecture.

## Actionable Improvements for Cerebrum
1. **Replace threshold decay with Ebbinghaus curve** — instead of binary (above/below threshold), score decay as: `retention = e^(-t/S)` where t = time since last access, S = stability factor (increases with each access)
2. **Differentiate RAG vs experiential memory** — add a `source_type` field: 'observation', 'delegation_result', 'research_finding', 'user_statement', 'inferred'
3. **Add conflict detection** — before storing new facts, check for contradictions with existing high-trust memories
4. **Usage-frequency-aware scoring** — memories accessed frequently should have higher stability (slower decay rate)


## Sources

- https://arxiv.org/abs/2601.03938
- https://tao-hpu.medium.com/the-agents-memory-dilemma-is-forgetting-a-bug-or-a-feature-a7e8421793d4
- https://dl.acm.org/doi/full/10.1145/3765766.3765803
