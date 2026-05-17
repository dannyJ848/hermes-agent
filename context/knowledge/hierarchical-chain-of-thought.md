# hierarchical-chain-of-thought

*Researched: 2026-04-20 07:39 CDT*

# Hierarchical Chain-of-Thought (Hi-CoT)

**Source:** arXiv:2604.00130v1 (April 2026)

Hi-CoT alternates between `<|instruction|>` (planning) and `<|execution|>` (execution) blocks, creating "compression bottlenecks" that force concise subgoals. Results: +6.2% accuracy over CoT, -13.9% token usage, 100% on AMC/MATH500 with strict format. Key insight: standard CoT lacks compression pressure, causing redundancy. Plan-and-Solve suffers plan-execution drift. Hi-CoT forces periodic distillation. Relevant to agent systems for multi-step reasoning and delegation chains.

## Sources

- https://arxiv.org/html/2604.00130v1
