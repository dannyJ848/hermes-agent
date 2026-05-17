# rl-training-deep-research-agents-search-r1

*Researched: 2026-04-09 23:52 CDT*

# RL Training for Deep Research Agents (Search-R1++)

**Paper:** arxiv 2602.19526 — "How to Train Your Deep Research Agent?" (Feb 2026)

## Key Findings

1. **REINFORCE > PPO > GRPO** for deep research agent RL training. REINFORCE delivers superior performance with fewer search actions. GRPO shows poorest stability among policy methods.

2. **Fast Thinking > Slow Thinking** prompt templates yield greater stability and better performance for research agents.

3. **F1-based reward underperforms EM** due to training collapse from answer avoidance. Fix: incorporate action-level penalties → surpasses EM reward.

4. **Search-R1++** baseline: improves Search-R1 from 0.403 → 0.442 (Qwen2.5-7B) and 0.289 → 0.331 (Qwen2.5-3B).

## Implications for Hermes/SOMA

- For Hermes RL training environments (Atropos), prefer REINFORCE over GRPO for tool-calling agent tasks
- Fast Thinking templates are better for multi-round retrieval agents
- Action-level penalties prevent answer avoidance collapse
- Simple policy methods can outperform complex ones for agentic RL


## Sources

- https://www.emergentmind.com/papers/2602.19526
- https://arxiv.org/abs/2602.19526
