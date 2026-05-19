# experiential-reflective-learning-erl-2026

*Researched: 2026-04-12 06:23 CDT*

# Experiential Reflective Learning (ERL) for Self-Improving LLM Agents

**Paper:** arXiv:2603.24639 (March 2026), ICLR 2026 MemAgents Workshop
**Authors:** Marc-Antoine Allard, Arnaud Teinturier, Victor Xing, Gautier Viaud

## Core Idea
ERL is a self-improvement framework where agents reflect on task trajectories and outcomes to generate **heuristics** — actionable lessons that transfer across tasks. At test time, relevant heuristics are retrieved based on the current task and injected into the agent's context.

## Key Results
- **+7.8% success rate** over ReAct baseline on Gaia2 benchmark
- Outperforms prior experiential learning methods
- Selective retrieval is essential (ablation proven)
- Heuristics provide more transferable abstractions than few-shot trajectory prompting

## Relevance to Hermes Cerebrum
Our `distilled_tips` table implements essentially the same architecture:
1. **Experience accumulation** → cerebrum logs tool calls, errors, outcomes
2. **Reflection** → distillation pipeline extracts tips from experiences
3. **Heuristic storage** → `distilled_tips` with confidence scores
4. **Selective retrieval** → domain_certainty.py prioritizes exploration
5. **Context injection** → tips injected into system prompt

### What ERL Validates in Our System
- Tip-based (heuristic) distillation is superior to few-shot trajectory replay
- Selective retrieval matters (our explore_priority scoring aligns)
- Single-attempt experiences CAN yield transferable knowledge

### What We Could Improve
- ERL uses task-description-based retrieval; we could improve our `apply_learnings` to match task descriptions more precisely
- Their "selective retrieval is essential" finding supports tightening our extraction criteria (our optimization tips have 1% survival — we're already filtering)

## Broader Context (O-Mega 2026 Guide)
- HyperAgents (Meta/UBC/Oxford/NYU): metacognitive self-improvement, imp@50=0.630 on Olympiad math grading (vs 0.0 for hand-designed systems)
- METR benchmarks: autonomous task completion doubling every 4 months (accelerated from 7 months)
- Memory systems (Mem0, MemOS, SimpleMem) emerging as the bottleneck for persistent learning

## Sources
- https://arxiv.org/abs/2603.24639
- https://o-mega.ai/articles/self-improving-ai-agents-the-2026-guide


## Sources

- https://arxiv.org/abs/2603.24639
- https://o-mega.ai/articles/self-improving-ai-agents-the-2026-guide
