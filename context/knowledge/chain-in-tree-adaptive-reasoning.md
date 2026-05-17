# chain-in-tree-adaptive-reasoning

*Researched: 2026-04-19 19:54 CDT*

# Chain-in-Tree: Adaptive Branching for LLM Tree Search

**Paper:** arXiv:2509.25835v4 | **Repo:** github.com/xinzhel/chain_in_tree

## Summary
Chain-in-Tree (CiT) reduces LLM tree search cost by 75-85% by adaptively deciding WHEN to branch. Instead of branching at every reasoning step (ToT, MCTS), CiT chains linearly through confident steps and only branches at uncertain decision points.

## Key Techniques
- **BN-DP (Direct Prompting):** Evaluator model judges branching necessity (scale 1-4). Proven to never increase invocations.
- **BN-SC (Self-Consistency):** If majority of k candidates agree, chain instead of branch.

## Results
- 75-85% runtime/token reduction across GSM8K, Math500, BlocksWorld
- Negligible accuracy loss with strong evaluator (Qwen3-32B)
- Framework-agnostic plugin for ToT-BS, ReST-MCTS, RAP

## Agent Application
The chaining-vs-branching paradigm directly maps to agent task delegation:
- **Chain** (linear): routine tool calls, simple lookups, file reads
- **Branch** (explore): ambiguous research, multi-path debugging, uncertain decisions
- A lightweight "branching necessity evaluator" could gate delegation vs direct execution

## Sources

- https://arxiv.org/html/2509.25835v4
- https://github.com/xinzhel/chain_in_tree
