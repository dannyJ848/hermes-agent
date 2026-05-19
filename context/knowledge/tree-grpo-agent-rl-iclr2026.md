# tree-grpo-agent-rl-iclr2026

*Researched: 2026-04-11 08:57 CDT*

# Tree-GRPO: Tree Search for LLM Agent RL (ICLR 2026)

**Source:** AMAP-ML/Tree-GRPO (Alibaba/AMAP, Xiamen University, SUSTech)

## Key Innovation
Replaces independent chain-based rollouts with tree-search rollouts for LLM agent RL training. Two major advantages:
1. **Less rollout budget** — fewer tokens and tool-calls needed per training step
2. **Higher performance** — tree structure enables better credit assignment across multi-step agent trajectories

## Why It Matters for Hermes
- Hermes agent loops are multi-step tool-call chains (avg 5-15 tools per task)
- Standard GRPO treats each rollout as independent — wastes compute on failed trajectories
- Tree-GRPO reuses shared prefixes across rollouts, dramatically reducing training cost
- Could be applied to Hermes Atropos environments for RL fine-tuning

## Training Targets
- SingleHopQA, MultiHopQA, WebAgent tasks
- Uses veRL framework (supports distributed RL training)
- Scripts: `train_webagent_tree_search.sh`, `train_webagent_grpo.sh`

## Relation to Post-Training 2026 Stack
Per llm-stats survey (Mar 2026), the modern pipeline is:
1. SFT (1-10M curated examples)
2. Preference Optimization (DPO variants)
3. RL with verifiable rewards (GRPO → Tree-GRPO for agents)

GRPO's advantage: group-relative normalization (reward_i - mean) / std — no critic model needed. Provably optimal within broad class of policy gradient methods.

DAPO (ByteDance): Clip-Higher for entropy maintenance, token-level policy gradient for long CoT, dynamic sampling for stable gradients.


## Sources

- https://github.com/AMAP-ML/Tree-GRPO
- https://llm-stats.com/blog/research/post-training-techniques-2026
- https://arxiv.org/pdf/2509.21240
