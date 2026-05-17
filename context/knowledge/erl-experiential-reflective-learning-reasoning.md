# erl-experiential-reflective-learning-reasoning

*Researched: 2026-04-12 17:40 CDT*

# Experiential Reflective Learning (ERL) — Agent Self-Improvement via Heuristics

**Paper:** arXiv:2603.24639v1 (Mar 2026) — Allard, Teinturier, Xing, Viaud (Illuin Technology)

## Core Idea
ERL enables LLM agents to self-improve without parameter updates by:
1. **Reflecting** on task trajectories and outcomes to generate reusable **heuristics** (actionable lessons)
2. **Retrieving** relevant heuristics at test time based on the current task context
3. **Injecting** top heuristics into the agent's context to guide execution

## Key Results
- **+7.8%** success rate over ReAct baseline on Gaia2 benchmark
- Outperforms ExpeL and AutoGuide (prior experiential learning methods)
- Works from **single-attempt trajectories** (no retry required)
- Heuristics generalize better than raw trajectory few-shot prompting

## Critical Insights
1. **Selective retrieval is essential** — injecting all heuristics hurts performance
2. **Failure heuristics** favor Search tasks; **success heuristics** favor Execution tasks
3. **Heuristics > trajectories** as transferable abstractions (more compact, more generalizable)
4. Quality of retrieval matters more than quantity of stored heuristics

## Relevance to Hermes Cerebrum
Our distilled_tips table in cerebrum_memory.db is essentially the same pattern as ERL's heuristic pool:
- We generate tips from session reflections (analogous to ERL's trajectory reflection)
- We inject tips into context (analogous to ERL's heuristic injection)
- Key improvement opportunity: ERL's **relevance-based retrieval** vs our current approach of bulk-injecting tips

## Improvement Ideas for Our System
1. Implement LLM-based heuristic scoring at retrieval time (ERL uses this)
2. Separate failure-mode heuristics from success-pattern heuristics (they serve different task types)
3. Track which heuristics actually improve outcomes (feedback loop)
4. Limit injected tips to top-k most relevant rather than bulk injection

## Inference-Time Scaling Categories (Raschka, Jan 2026)
From Sebastian Raschka's taxonomy of inference-time scaling methods:
1. **Chain-of-Thought Prompting** — elicit intermediate reasoning steps
2. **Self-Consistency** — sample multiple reasoning paths, majority vote
3. **Best-of-N Ranking** — generate N candidates, rank with verifier/reward model
4. **Rejection Sampling with Verifier** — keep only samples that pass verification
5. **Self-Refinement** — iterative self-critique and improvement
6. **Search Over Solution Paths** — tree/graph search (MCTS, beam search)


## Sources

- https://arxiv.org/html/2603.24639v1
- https://magazine.sebastianraschka.com/p/categories-of-inference-time-scaling
