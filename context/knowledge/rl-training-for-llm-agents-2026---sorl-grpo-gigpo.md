# RL Training for LLM Agents 2026 - SORL GRPO GiGPO

*Researched: 2026-04-10 20:41 CDT*

# RL Training for LLM Agents (2026)

## SORL: Stabilizing Off-Policy RL for Long-Horizon Agent Training
- **Paper:** arXiv 2511.20718 (Li et al., GE HealthCare)
- **Problem:** PPO/GRPO unstable in multi-turn agent training due to token-level vs turn-level granularity mismatch + high-variance off-policy gradients
- **Solution:** Turn-level importance sampling + clipping-triggered normalization
- **Variants:** SO-PPO and SO-GRPO both prevent training collapse
- **Relevance to Hermes:** Directly applicable to Atropos environments for tool-calling RL

## GRPO is now default for reasoning model training
- Replaces PPO for RLVR (verifiable rewards)
- No separate critic model needed (simpler, cheaper)
- Used by DeepSeek-R1, Kimi V2

## GiGPO (Group-in-Group Policy Optimization) — NeurIPS 2025
- Multi-turn extension of GRPO
- Addresses cross-turn credit assignment in agentic tasks

## veRL — Production RL training framework
- github.com/verl-project/verl
- Supports PPO, GRPO, custom algorithms
- Production-ready, flexible

## Key Takeaway for Agent RL
Use **turn-level** importance sampling, not token-level, for multi-turn tool-calling agent training. Standard PPO/GRPO will collapse on long-horizon agent tasks without this adjustment.

## Sources

- https://arxiv.org/html/2511.20718v2
- https://cameronrwolfe.substack.com/p/grpo
- https://neurips.cc/virtual/2025/poster/118123
- https://github.com/verl-project/verl
