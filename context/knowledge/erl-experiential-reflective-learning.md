# erl-experiential-reflective-learning

*Researched: 2026-04-07 12:10 CDT*

# Experiential Reflective Learning (ERL) — arXiv:2603.24639

**Status**: Published at ICLR 2026 MemAgents Workshop

## Key Technique
ERL enables rapid environment adaptation by reflecting on task trajectories and outcomes to generate structured **heuristics** with explicit trigger conditions and recommended actions.

## Architecture
1. **Heuristic Generation**: After each task, reflect on trajectory + outcome (success/failure) → generate (condition, recommendation, analysis)
2. **Retrieval-Augmented Execution**: For new tasks, LLM scores stored heuristics for relevance → inject top-k into system prompt
3. **No repeated rollouts needed** — extracts heuristics from SINGLE-ATTEMPT trajectories

## Key Findings
- +7.8% over ReAct baseline on Gaia2 benchmark
- **Selective retrieval is essential** — injecting all heuristics hurts (ExpeL's approach)
- Heuristics >> few-shot trajectory prompting for transfer
- Failure heuristics favor Search tasks; success heuristics favor Execution tasks
- Top-k=5 heuristics is optimal

## Integration into Evey (Apr 7, 2026)
Wired into distillation plugin v2.2 pre_llm_call:
- Extract task keywords from user message (stop-word filtered)
- Match against `condition` and `recommendation` columns in `distilled_tips`
- Prioritize task-relevant tips over globally weakest tool tips
- Dual retrieval: ERL task-relevant + classic weakest-tools

## Divergence from Paper
- We use keyword LIKE matching instead of LLM-scored relevance (zero cost)
- We combine with existing SWIRL prediction + AUQ uncertainty + Polaris patches


## Sources

- https://arxiv.org/abs/2603.24639
