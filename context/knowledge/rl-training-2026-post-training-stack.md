# rl-training-2026-post-training-stack

*Researched: 2026-04-09 23:31 CDT*

# Post-Training in 2026: GRPO, DAPO, RLVR & Beyond

**Source:** LLM Stats (Mar 2026) — practitioner's guide to techniques shipping in production models.

## Key Insight
RLHF with human preference labels is **dead**. Every major 2025-2026 model (DeepSeek-R1, Nemotron 3 Super, GPT-5.3 Codex) uses a new post-training stack.

## Modern 3-Stage Post-Training Pipeline
1. **SFT** (Supervised Fine-Tuning): Teaches format — instructions, structured outputs, conversation. Uses 1-10M curated examples. Nemotron 3 Super used 7M from 40M corpus.
2. **Preference Optimization**: Aligns with human values. DPO and variants (SimPO, KTO) live here.
3. **Reinforcement Learning**: Pushes beyond training data using verifiable rewards (math, code) or environment feedback (tool use, multi-step). Produces reasoning capabilities.

## GRPO (Group-Relative Policy Optimization)
- Eliminates the critic model entirely (doubles memory savings)
- For each prompt: samples 8-64 responses, computes advantages by normalizing reward against group mean/std
- `advantage_i = (reward_i - mean) / std`
- Theoretically a U-statistic — asymptotically equivalent to oracle with ideal value function
- Provably optimal within broad class of policy gradient methods

## DAPO (Dynamic Advantage Policy Optimization)
- ByteDance/Tsinghua 2025
- Tackles instabilities in long chain-of-thought training
- Four techniques:
  - **Clip-Higher**: Increases upper clip range to prevent entropy collapse
  - **Dynamic Sampling**: Filters batches for consistent gradient signals
  - **Token-level Policy Gradient Loss**: Solves vanishing gradients in long CoT
  - **Overlong Reward Shaping**: Reduces reward noise from length-exceeding responses
- Qwen2.5-32B trained to 50 on AIME 2024, beating DeepSeek-R1-Zero with 50% fewer steps

## Preference Optimization Successors to DPO
- **SimPO**: Uses average log probability as implicit reward, no reference model. +6.4 pts AlpacaEval 2, +7.5 pts Arena-Hard vs DPO.
- **KTO**: Binary feedback (thumbs up/down) instead of preference pairs. Scales with cheaper data.

## Relevance to Hermes Agent
- GRPO is directly applicable to agent RL training (already used in Atropos environments)
- Token-level loss matters for long tool-calling sequences
- SimPO's implicit reward approach could simplify reward model requirements
- DAPO's dynamic sampling addresses exact instabilities seen in agent trajectory training


## Sources

- https://llm-stats.com/blog/research/post-training-techniques-2026
