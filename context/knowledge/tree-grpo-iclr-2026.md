# tree-grpo-iclr-2026

*Researched: 2026-04-10 09:34 CDT*

# Tree-GRPO: Tree Search for LLM Agent RL (ICLR 2026)

**Source:** AMAP-ML/Tree-GRPO (Alibaba Group + Xiamen Univ + SUSTech)
**Accepted:** ICLR 2026 (Jan 27, 2026)
**GitHub:** https://github.com/AMAP-ML/Tree-GRPO (328 stars)

## Key Innovation
Combines tree search with GRPO (Group Relative Policy Optimization) for training LLM agents. Extends standard GRPO by exploring multiple action paths via tree search during training, allowing the agent to learn from both successful and failed trajectories.

## Training Tasks
- Single-hop QA (with retrieval)
- Multi-hop QA (complex reasoning chains)
- WebAgent (web navigation tasks)

## Architecture
Built on verl framework. Includes search_r1 module for retrieval-augmented reasoning. Separate launch scripts for GRPO baseline vs tree-search enhanced training.

## Relevance to Hermes
- Directly applicable to agent RL training environments (Atropos integration)
- Tree search during training could improve tool selection quality
- Multi-hop reasoning aligns with Hermes's multi-tool orchestration
- WebAgent training parallels browser automation tool use


## Sources

- https://github.com/AMAP-ML/Tree-GRPO
