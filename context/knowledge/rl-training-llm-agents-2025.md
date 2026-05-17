# rl-training-llm-agents-2025

*Researched: 2026-04-09 18:03 CDT*

# RL Training for LLM Agents — Key Techniques (2024-2025)

## DeepSeek-R1 (Jan 2025, arxiv:2501.12948)
- Incentivizes reasoning capability in LLMs via pure RL (no supervised fine-tuning needed for reasoning chains)
- Demonstrates that RL alone can emergently produce chain-of-thought reasoning, self-verification, and reflection behaviors
- Uses GRPO (Group Relative Policy Optimization) from DeepSeekMath — a memory-efficient PPO variant
- Key insight: reward shaping for reasoning (format rewards + accuracy rewards) produces emergent behaviors without explicit training on chain-of-thought data

## GRPO — Group Relative Policy Optimization (DeepSeekMath, Feb 2024, arxiv:2402.03300)
- Variant of PPO that reduces memory usage by eliminating the critic (value) network
- Uses group-level relative rewards — compares outputs within a group rather than against an absolute baseline
- Achieves 51.7% on MATH benchmark (competition level) with 7B model
- Key for agent training: lower memory footprint means longer trajectories and more complex tool-use sequences can be trained

## Implications for Agent RL Training
1. **Critic-free RL**: GRPO eliminates the value network, making multi-turn agent training feasible (lower GPU memory per trajectory)
2. **Emergent reasoning**: Pure RL can produce self-correction and verification — critical for agent tool-use
3. **Group comparison**: Relative reward within trajectory groups is more stable than absolute reward for tool-calling quality
4. **Scalability**: DeepSeek-R1 showed this works at 671B parameter scale with MoE architecture

## Open Questions for Agent Training
- How to define reward for multi-step tool calling sequences (intermediate vs final reward)
- Whether GRPO works for online RL where the agent interacts with real tools during training
- Multi-turn RL: DeepSeek-R1 uses single-turn reasoning, but agents need multi-turn trajectories


## Sources

- https://arxiv.org/abs/2501.12948
- https://arxiv.org/abs/2402.03300
