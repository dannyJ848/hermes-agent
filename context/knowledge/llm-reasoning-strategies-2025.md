# llm-reasoning-strategies-2025

*Researched: 2026-04-14 23:05 CDT*

# LLM Reasoning Strategies (2025-2026 Survey)

## Taxonomy

### Post-Hoc Reasoning (no weight changes)
- **Chain-of-Thought (CoT):** Break problems into steps; reveal intermediate reasoning
- **ReAct:** Interleave reasoning traces with tool calls (Thought → Action → Observation loop)
- **Self-Reflection:** Model critiques its own outputs and revises
- **Knowledge Graph Integration:** Structured triples for precise reasoning paths

### Reinforcement Learning Paradigm
- **Verbal RL (Reflexion):** Plain-language feedback loops until logic stabilizes
- **Reward-Based:** PPO, GRPO (group-normalized), DPO (pairwise preference)
- **Search + Planning Hybrids:** RL policy + MCTS

### Test-Time Compute (TTC)
- **Forest-of-Thought:** Multiple parallel reasoning paths woven into solution
- **Iterative Refinement:** Draft multiple → select best via voting

### Self-Training
- **Bootstrapping:** Generate CoT → select best → retrain
- **Self-Consistency:** Multiple reasoning lines → internal voting

## Key Models
- **OpenAI o1:** RL "thinking", spots mistakes mid-reasoning, fast on coding
- **DeepSeek R1:** Large-scale RL (skips SFT), higher science/math accuracy

## Hermes Relevance
- aggressive_continue + SILENT guard = verbal RL (Reflexion pattern)
- tool_planner = MCTS-inspired search + planning hybrid
- distilled tips = self-training/bootstrapping loop
- Next: Forest-of-Thought for parallel delegation paths

## Sources

- https://futureagi.com/blog/llm-reasoning-2025/
- https://www.superannotate.com/blog/llm-agents
- https://www.promptingguide.ai/techniques/react
