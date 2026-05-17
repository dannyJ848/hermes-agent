# tree-grpo-rl-agent-training

*Researched: 2026-04-10 06:26 CDT*

# Tree-GRPO: Tree Search for LLM Agent RL Training (ICLR 2026)

**Source:** AMAP-ML/Tree-GRPO (GitHub, 327 stars, Alibaba Group + Xiamen University)
**Authors:** Yuxiang Ji, Ziyu Ma, Yong Wang, Guanhua Chen, Xiangxiang Chu, Liaoni Wu
**Accepted:** ICLR 2026 (Jan 27, 2026)

## Key Innovation
Extends GRPO (Group Relative Policy Optimization) with tree search for multi-step agent RL training. Standard GRPO treats each rollout independently; Tree-GRPO explores multiple action branches at each decision point, building a search tree over agent trajectories.

## Architecture
- Built on VERL framework (Alibaba's RL for LLM library)
- Training scripts for: multi-hop QA, single-hop QA, web agent tasks
- Supports both local retrieval and Bing search as tool backends
- Search-R1 integration for retrieval-augmented reasoning

## Why It Matters for SOMA/Hermes
1. **Tool-integrated reasoning:** The approach specifically trains agents to use search tools within reasoning chains
2. **Multi-step planning:** Tree search captures the branching nature of real agent decisions (not just single-turn)
3. **Web agent training:** Direct training scripts for web navigation agents — relevant to browser automation
4. **VERL compatibility:** Uses VERL which supports distributed training on GPU clusters

## Related Work Noted
- GiGPO (Group-in-Group Policy Optimization, NeurIPS 2025): Evaluates on ALFWorld, WebShop, and search-augmented QA
- MERL's "Training Task Reasoning LLM Agents for Multi-turn Task Planning" (2026): Multi-turn task planning with tools and memory

## Actionable Insight
If we want to fine-tune Hermes for better tool use, Tree-GRPO provides a framework that handles multi-step agent trajectories (not just single prompt-response pairs). The tree search component is key — it captures the exploration/exploitation tradeoff that flat GRPO misses.


## Sources

- https://github.com/AMAP-ML/Tree-GRPO
- https://neurips.cc/virtual/2025/poster/118123
- https://www.merl.com/publications/docs/TR2026-026.pdf
