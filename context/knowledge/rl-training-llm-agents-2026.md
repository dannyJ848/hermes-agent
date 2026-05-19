# rl-training-llm-agents-2026

*Researched: 2026-04-10 16:31 CDT*

# RL Training for LLM Agents — 2026 Post-Training Stack

## Key Shift: RLHF → GRPO/DAPO + RLVR
RLHF with human preference labels is **dead** as the dominant post-training method. Every major 2025-2026 model (DeepSeek-R1, Nemotron 3 Super, GPT-5.3 Codex) uses a different stack.

## Modern 3-Stage Pipeline
1. **SFT** (1-10M curated examples) — teaches format, instruction following, structured output
2. **Preference Optimization** (DPO variants) — aligns with human values/preferences
3. **RL** (verifiable rewards or environment feedback) — produces reasoning capabilities through trial-and-error

## GRPO (Group-Relative Policy Optimization)
- Eliminates the critic model entirely (halves memory usage)
- Samples group of 8-64 responses per prompt, normalizes rewards against group mean/std
- Advantage = (reward_i - mean) / std
- Provably optimal within broad class of policy gradient methods (asymptotically equivalent to oracle with ideal value function)
- Used in DeepSeek-R1

## DAPO (Dynamic Advantage Policy Optimization)
- Tackles instabilities in long chain-of-thought training
- Clip-Higher: prevents entropy collapse in long outputs
- Dynamic Sampling: filters batches for consistent gradient signals
- Token-level Policy Gradient Loss: critical for long CoT (sequence-level loss causes vanishing gradients)
- Overlong Reward Shaping: reduces reward noise from truncated responses

## Agentic Post-Training
- Newest frontier: training models for multi-step tool use and autonomous workflows
- Requires RL environments that simulate real tool-use scenarios
- GiGPO (Group-in-Group Policy Optimization) — evaluated on ALFWorld, WebShop, search-augmented QA
- Multi-turn task planning with augmented LLM + tools + memory

## Implications for Hermes Agent
- Hermes's tool-use patterns could benefit from GRPO-style training
- The Atropos RL environments in hermes-agent/environments/ align with agentic post-training approach
- Token-level loss is critical for long tool-calling sequences
- Group-relative advantage computation is simple to implement


## Sources

- https://llm-stats.com/blog/research/post-training-techniques-2026
- https://neurips.cc/virtual/2025/poster/118123
- https://www.merl.com/publications/docs/TR2026-026.pdf
