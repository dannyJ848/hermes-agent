# RL Training: MT-GRPO for Multi-Turn Tool-Calling Agents

*Researched: 2026-04-10 13:37 CDT*

# MT-GRPO: Multi-Turn GRPO for Tool-Calling Agents

**Source:** arXiv 2604.02869 (April 2025)

## Key Innovation
Iterative Reward Calibration (IRC) — designs per-turn rewards using empirical discriminative analysis of rollout data. Part of the MT-GRPO framework (Multi-Turn Group Relative Policy Optimization).

## Problem Addressed
Training tool-calling agents with RL on multi-turn tasks remains challenging due to:
- Sparse outcome rewards (reward only at end of task)
- Credit assignment across multiple tool calls
- Balancing exploration vs exploitation in long trajectories

## Technical Approach
- Generalized Token-level reward assignment across multi-turn interactions
- Empirical discriminative analysis of rollout data to calibrate per-turn rewards
- Extends GRPO from single-turn to multi-turn settings

## Relevance to Hermes Agent
1. **Atropos environments** — IRC methodology maps to reward shaping for tool-calling training
2. **Tool intelligence scoring** — Per-turn reward calibration mirrors tool_intelligence quality scoring
3. **Distillation pipeline** — The discriminative analysis approach could improve tip quality scoring
4. **Agent loop optimization** — Multi-turn reward design could reduce completion bias

## Related
- MERL TR2026-026: Task Reasoning LLM Agents
- TRL GRPO implementation (HuggingFace)
- DAPO, RLVR post-training techniques


## Sources

- https://arxiv.org/abs/2604.02869
- https://richlyai.com/blog/multi-turn-rl-for-tool-calling-agents-with-reward-calibration-ai-news/
