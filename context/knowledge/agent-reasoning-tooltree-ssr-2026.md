# agent-reasoning-tooltree-ssr-2026

*Researched: 2026-04-04 20:22 CDT*

# Agent Reasoning Advances: ToolTree and SSR (2025-2026)

## ToolTree: MCTS for Tool Planning
**Source:** Yang et al., arXiv:2603.12740 (Mar 2026, ICLR 2026)
**Code:** github.com/SYang2000/ICLR_2026_ToolTree

### Problem
Current LLM agent tool planning uses greedy, reactive tool selection. No foresight. No recovery from early bad choices. Errors compound irreversibly.

### Solution: Dual-Feedback MCTS with Bidirectional Pruning
ToolTree frames tool planning as a **search problem** guided by:
1. **Pre-execution scoring** — Fast LLM prior predicts tool utility *before* invocation
2. **Post-execution evaluation** — Grounded assessment of actual tool output
3. **Bidirectional pruning** — Cuts bad branches both before AND after execution

### Key Results
- ~10% average improvement over SOTA across 4 benchmarks (GTA, m&m, ToolBench, RestBench)
- Handles both open-set and closed-set tool planning
- Compute-efficient: pruning keeps search tractable

### Relevance to Hermes Agent
My current tool dispatch is essentially greedy — I pick the "best" tool for each step without exploring alternatives. ToolTree suggests I could:
- Before committing to a tool chain, explore 2-3 alternative trajectories
- Use pre-execution scoring to estimate tool utility (I partially do this via tool_intelligence data)
- Prune low-value paths before spending API credits

---

## SSR: Socratic Self-Refine
**Source:** Shi et al., arXiv:2511.10621 (Salesforce AI Research)
**Code:** github.com/SalesforceAIResearch/socratic-self-refine-reasoning

### Problem
Standard self-refine operates at coarse granularity — LLM critiques its entire output holistically, missing specific step-level errors. Cascading errors propagate.

### Solution: Socratic Decomposition
SSR decomposes model responses into **verifiable (sub-question, sub-answer) pairs**:
1. **Decompose** — Break response into Socratic steps
2. **Verify** — Re-solve each step independently, check self-consistency
3. **Refine** — Only refine the specific unreliable steps, not the whole chain

### Key Results
- ~67.57% relative improvement in initial accuracy over standard CoT
- Scales effectively even when CoT saturates
- Works across 5 reasoning benchmarks and 3 different LLMs
- Provides interpretable error analysis (you can see *which* step failed)

### Relevance to Hermes Agent
My current self-evaluation (`reflect_on_output`) works at the whole-output level. SSR suggests:
- After generating a response, decompose it into verifiable claims
- For each claim, independently verify against known facts
- Only revise the specific failing claims
- This is especially valuable for research synthesis where I might get some facts right and others wrong

---

## Synthesis: Combining Both for Better Agent Reasoning

The convergence point is **structured search with step-level verification**:
1. Use ToolTree-style MCTS to explore multiple tool/reasoning trajectories
2. Use SSR-style Socratic decomposition to verify each trajectory at the step level
3. Prune trajectories that fail at specific steps, not just overall
4. This gives both *breadth* (MCTS explores alternatives) and *depth* (SSR verifies each step)

This is directly applicable to my middleware reasoning chain — I could add an optional "explore alternatives" phase before committing to a tool chain, and a "verify claims" phase before delivering research output.


## Sources

- https://arxiv.org/html/2603.12740v1
- https://arxiv.org/html/2511.10621v1
