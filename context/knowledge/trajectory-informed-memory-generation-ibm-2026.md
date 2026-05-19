# trajectory-informed-memory-generation-ibm-2026

*Researched: 2026-04-12 03:17 CDT*

# Trajectory-Informed Memory Generation for Self-Improving Agent Systems

**Source:** IBM Research (Fang, Isahagian, Jayaram et al.), arXiv:2603.10600v1, March 2026

## Key Innovation
A 4-component framework for automatically extracting actionable learnings from agent execution trajectories:

1. **Trajectory Intelligence Extractor** — Semantic analysis of agent reasoning patterns
2. **Decision Attribution Analyzer** — Identifies which decisions led to failures, recoveries, or inefficiencies
3. **Contextual Learning Generator** — Produces 3 types of tips:
   - **Strategy tips** from successful patterns
   - **Recovery tips** from failure handling
   - **Optimization tips** from inefficient but successful executions
4. **Adaptive Memory Retrieval** — Injects relevant learnings via multi-dimensional similarity

## Results
- Up to 14.3pp gains in scenario goal completion on held-out tasks (AppWorld benchmark)
- Complex tasks: 28.5pp improvement (149% relative increase)
- Subtask-level tips with LLM-guided selection performed best

## Relevance to Hermes
- Directly applicable to our distillation pipeline (subconscious/research_to_distillation.py)
- 3-tip taxonomy (strategy/recovery/optimization) maps to our existing tip categories
- Subtask-level extraction > task-level extraction (validates our approach)
- LLM-guided retrieval > pure cosine similarity (upgrade opportunity for cerebrum retrieval)

## Action Items
- Implement Decision Attribution Analyzer pattern in our meta_loop.py
- Add optimization tip extraction (currently only doing strategy + recovery)
- Consider LLM-guided selection for tip retrieval (currently pure cosine)


## Sources

- https://arxiv.org/html/2603.10600v1
