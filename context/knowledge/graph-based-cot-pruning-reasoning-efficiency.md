# graph-based-cot-pruning-reasoning-efficiency

*Researched: 2026-04-14 11:55 CDT*

# Graph-Based Chain-of-Thought Pruning for Reasoning Efficiency

**Paper:** arXiv:2604.05643v1 (April 2026) — Yuan et al., Baidu/Central South University

## Key Innovation
Converts linear CoT into a DAG and prunes redundant reflection branches. Two pruning strategies:
1. **Branch-level pruning** — removes weakly contributing reflection branches
2. **Depth-level pruning** — eliminates late-stage re-verification

## Problem Addressed
RL-extended CoT induces "overthinking" — two patterns:
- **Indiscriminate Reflection**: broad, low-impact checks throughout reasoning
- **Repetitive Reflection**: repeatedly re-verifying already established conclusions

## Training Pipeline (3-stage)
1. SFT on pruned concise traces (cold start)
2. DPO to prefer correct-but-less-redundant trajectories
3. GRPO with length penalty for correctness + efficiency

## Results
- **42% reduction in reasoning tokens** while maintaining or improving accuracy
- Tested on standard reasoning benchmarks

## Relevance to Agent Systems
This is directly applicable to autonomous agents that generate long reasoning chains. Pruning redundant self-reflection loops could:
- Reduce inference cost per cycle
- Speed up tool-call decisions
- Prevent the "idle loop" problem where agents re-verify decisions endlessly


## Sources

- https://arxiv.org/html/2604.05643v1
