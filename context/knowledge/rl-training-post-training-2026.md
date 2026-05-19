# rl-training-post-training-2026

*Researched: 2026-04-10 01:49 CDT*

# Post-Training in 2026: GRPO, DAPO, RLVR & Beyond

## Summary
RLHF is dead. Every major 2025-2026 model (DeepSeek-R1, Nemotron 3 Super, GPT-5.3 Codex) uses a new post-training stack: SFT → Preference Optimization → RL with verifiable rewards.

## Key Techniques

### GRPO (Group-Relative Policy Optimization)
- Eliminates the critic model entirely (halves memory)
- Samples group of 8-64 responses per prompt
- Advantage = (reward_i - mean) / std — group-normalized
- Provably optimal: GRPO's policy gradient is a U-statistic, asymptotically equivalent to oracle with ideal value function
- Core algorithm behind DeepSeek-R1's success

### DAPO (ByteDance/Tsinghua, 2025)
- Tackles instabilities in long chain-of-thought RL training
- Clip-Higher: prevents entropy collapse, keeps model exploratory
- Dynamic Sampling: filters batches for consistent gradient signals
- Token-level Policy Gradient Loss: prevents vanishing gradients in long CoT
- Overlong Reward Shaping: reduces reward noise from truncated responses

### Agentic Training (ART - Agent Reinforcement Trainer)
- Open-source framework for RL fine-tuning of agent-capable LLMs
- No manual reward engineering — LLM judge does relative grading
- Native support for tool calls and multi-turn conversations
- Integrations with LangGraph, CrewAI, ADK
- Uses vLLM for serving + Unsloth for GRPO training
- Can fine-tune small open-source models to outperform closed-source on specific tasks

## Modern 3-Stage Pipeline
1. **SFT** (1-10M examples): Format, instruction following, structured output
2. **Preference Optimization** (DPO variants): Align with human values
3. **RL with verifiable rewards**: Math, code, tool use — model discovers new strategies

## Relevance to Hermes Agent
- GRPO pattern is directly applicable to Hermes RL environments (Atropos)
- ART's tool-call-aware training aligns with Hermes's tool dispatch
- The "no manual reward" approach using LLM judges could replace hand-crafted reward functions in agent training

## Sources
- https://llm-stats.com/blog/research/post-training-techniques-2026
- https://blog.dailydoseofds.com/p/build-agents-that-can-learn-like


## Sources

- https://llm-stats.com/blog/research/post-training-techniques-2026
- https://blog.dailydoseofds.com/p/build-agents-that-can-learn-like
