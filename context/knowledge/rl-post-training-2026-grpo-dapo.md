# rl-post-training-2026-grpo-dapo

*Researched: 2026-04-11 16:32 CDT*

# Post-Training in 2026: GRPO, DAPO, RLVR & Beyond

## Key Insights

### The New 3-Stage Pipeline (replaces old RLHF)
1. **SFT** (1-10M curated examples) — teaches format, structured output, instruction following
2. **Preference Optimization** (DPO variants) — aligns with human values
3. **RL** (verifiable rewards, environment feedback) — produces reasoning capabilities

### GRPO (Group-Relative Policy Optimization)
- Eliminates the critic model entirely (halves memory usage)
- Samples 8-64 responses per prompt, normalizes rewards within group: `(reward_i - mean) / std`
- Provably optimal — policy gradient is a U-statistic, asymptotically equivalent to oracle with ideal value function
- Used in DeepSeek-R1, DeepSeekMath

### DAPO (Dynamic Advantage Policy Optimization)
- ByteDance/Tsinghua 2025 — stabilizes long-horizon RL for reasoning
- 4 techniques: Clip-Higher (prevent entropy collapse), Dynamic Sampling (filter uninformative), Token-level PG Loss (prevent vanishing gradients in long CoT), Overlong Reward Shaping
- Critical for training models that produce long chain-of-thought

### Agentic Training (Most Relevant to Hermes)
- "The newest frontier is training models for multi-step tool use and autonomous workflows"
- Requires RL environments, not static datasets
- GRPO works well here — group sampling naturally handles multi-turn trajectories

### Relevance to Hermes Agent
- Hermes's tool-calling could benefit from GRPO fine-tuning with tool-execution rewards
- The Atropos environment framework aligns with "RL environments for agents" paradigm
- DAPO's token-level loss is relevant for long agent sessions with many tool calls
- Key lesson: post-training now accounts for majority of usable capability (pretraining is just foundation)

## Sources
- https://llm-stats.com/blog/research/post-training-techniques-2026
- https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide/training-ai-agents-with-rl


## Sources

- https://llm-stats.com/blog/research/post-training-techniques-2026
- https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide/training-ai-agents-with-rl
