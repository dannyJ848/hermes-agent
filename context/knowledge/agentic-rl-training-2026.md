# agentic-rl-training-2026

*Researched: 2026-04-10 00:45 CDT*

# Agentic RL Training for LLM Agents (2026)

## Key Findings

### Turn-PPO: Turn-Level Advantage Estimation (arXiv 2512.17008)
- **Problem:** GRPO applied to multi-turn tasks has notable limitations — high sampling variance in environment interactions, uniform advantage across unequal turns
- **Solution:** Turn-PPO operates on turn-level MDP instead of token-level MDP
- PPO is more robust than GRPO for multi-turn agentic settings
- Results on WebShop and Sokoban demonstrate effectiveness with/without long reasoning
- Key insight: different turns in a trajectory contribute unequally to final reward — same advantage to all tokens is inaccurate

### GPT-OSS Agentic RL Training (HuggingFace Blog, Jan 2026)
- Agentic RL extends traditional LLM training by optimizing entire decision-making processes through environment interaction
- Unlike single-turn RL or offline preference methods, trains policies by collecting on-policy data as agent plans, invokes tools, observes outcomes
- Credit assignment across long-horizon decisions (query reformulation, tool selection, execution order)
- Uses verl framework with GRPO/PPO algorithms
- Fixes needed for MoE models: on-policy integrity restoration, attention sink support in FlashAttentionV3
- GPT-OSS-20B shows comparable performance to o3-mini/o4-mini

### ARPO — Agentic Reinforced Policy Optimization
- Designed for agentic systems that plan, act, use tools, and revise decisions over time
- Extension of GRPO++ techniques for agentic contexts

### Retool: RL for Strategic Tool Use in LLMs (arXiv 2504.11536)
- Focuses specifically on training models to use tools strategically via RL

## Implications for Hermes Agent
1. **Turn-PPO is directly relevant** — Hermes operates in multi-turn tool-use scenarios. Current GRPO-based training could benefit from turn-level advantage estimation.
2. **Credit assignment across tool calls** — different tool calls in a trajectory contribute differently to success. Turn-level MDP formulation captures this.
3. **On-policy data collection** — agentic RL requires active interaction, not static datasets. Hermes's cron-driven autonomous loops naturally produce trajectory data.
4. **verl framework** — production-ready for multi-turn RL training, compatible with Hermes's training environments in environments/


## Sources

- https://arxiv.org/html/2512.17008v2
- https://huggingface.co/blog/LinkedIn/gpt-oss-agentic-rl
- https://www.reddit.com/r/reinforcementlearning/comments/1rqovpv/looking_for_case_studies_on_using_rl_ppogrpo_to/
