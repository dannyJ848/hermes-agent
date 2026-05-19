# agent-reasoning-mcts-2026

*Researched: 2026-04-12 23:56 CDT*

# Agent Reasoning: MCTS-Based Tool Planning (2026)

## ToolTree (ICLR 2026, Yang et al.)
- Monte Carlo Tree Search applied to LLM agent tool planning
- **Key innovation:** Dual-stage LLM evaluation + bidirectional pruning (pre-execution and post-execution)
- Outperforms greedy/reactive tool selection by ~10% across 4 benchmarks (GTA, m&m, ToolBench, RestBench)
- Explores tool usage trajectories with foresight, accounting for inter-tool dependencies
- Code: https://github.com/SYang2000/ICLR_2026_ToolTree

## DMA-MCTS (Dynamic Memory-Augmented MCTS)
- Integrates dynamic memory into MCTS for LLM task planning
- Memory provides context across search iterations, improving planning quality

## ExACT: Reflective MCTS + Self-Learning (OpenReview 2026)
- Reflective Monte Carlo Tree Search (R-MCTS) for autonomous AI agents
- Self-learning mechanism: agents learn from their own exploration trajectories
- Combines reflection with tree search for improved autonomous exploration

## Key Trend (2026)
The field is moving from linear reasoning chains (CoT, ReAct) to **tree-structured search** (MCTS variants) for agent planning. The insight: greedy next-step selection fails on multi-step tasks with inter-tool dependencies. MCTS enables lookahead and backtracking.

## Relevance to Hermes Agent
- ToolTree's dual-feedback pruning could improve Hermes' tool selection — currently relies on model intuition
- MCTS-based planning could reduce the "wrong tool → retry" pattern seen in weak tools (browser_navigate: 0%, cached_delegate: 0%)
- The awesome-agentic-reasoning repo (1.2k stars) is an excellent ongoing resource for tracking this space

## Source
- Survey: "Agentic Reasoning for Large Language Models: A Survey" (arxiv, Jan 2026)
- Awesome list: https://github.com/weitianxin/Awesome-Agentic-Reasoning


## Sources

- https://arxiv.org/html/2603.12740v1
- https://github.com/weitianxin/Awesome-Agentic-Reasoning
- https://openreview.net/forum?id=GBIUbwW9D8
