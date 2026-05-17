# reasoning-agent-self-improvement-2026

*Researched: 2026-04-13 23:52 CDT*

# Reasoning & Agent Self-Improvement (2026)

## ERL: Experiential Reflective Learning (arxiv 2603.24639, Mar 2026)
- **Framework**: ERL enables parameter-free agent self-improvement by reflecting on task trajectories
- **Key insight**: Generates *heuristics* (actionable lessons) from experience, not raw trajectories
- **Retrieval**: Relevant heuristics retrieved per-task and injected into context (vs ExpeL which concatenates all)
- **Results**: +7.8% success on Gaia2 benchmark over ReAct baseline
- **Key ablations**:
  - Selective retrieval is essential (dumping all heuristics hurts)
  - Heuristics generalize better than few-shot trajectory prompting
  - Failure heuristics favor Search tasks; success heuristics favor Execution tasks
- **Relevance to Hermes**: Our distilled_tips system is similar to ERL's heuristics. The selective retrieval finding validates our confidence-gated approach (only tips with confidence >= 0.6 are used).

## ARC: Active Reflection-driven Context Management (arxiv 2601.12030)
- Formulates context management as active, reflection-driven process
- First framework to systematically manage agent context via active inference

## Cost of Dynamic Reasoning (arxiv 2506.04301)
- Analyzes token costs of ReAct vs Reflexion agents
- Reflexion significantly outperforms ReAct (130/134 tasks vs baseline)
- But at higher token cost — tradeoff between reasoning depth and efficiency

## Awesome Agentic Reasoning (GitHub: weitianxin/Awesome-Agentic-Reasoning)
- Comprehensive taxonomy: planning, tool use, search, self-evolution
- 1.2k stars, actively maintained
- Key categories for Hermes architecture reference

## Implications for Hermes Agent
1. Our distillation pipeline (research → distilled_tips) mirrors ERL's heuristic extraction
2. We should ensure tip retrieval is task-contextual, not blanket injection
3. Failure heuristics and success heuristics should be tagged differently for retrieval optimization


## Sources

- https://arxiv.org/html/2603.24639v1
- https://github.com/weitianxin/Awesome-Agentic-Reasoning
- https://arxiv.org/html/2506.04301v2
