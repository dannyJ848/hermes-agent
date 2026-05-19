# GRPO-to-DAPO-to-GSPO-RL-training-evolution

*Researched: 2026-04-09 22:48 CDT*

# GRPO → DAPO → GSPO: Evolution of RL Training for LLMs

## Source
HuggingFace Blog: "From GRPO to DAPO and GSPO: What, Why, and How" by Yihua Zhang (NormalUhr), Aug 2025
URL: https://huggingface.co/blog/NormalUhr/grpo-to-dapo-and-gspo

## Key Insights

### GRPO (Group Relative Policy Optimization)
- Removes dependency on value model (unlike PPO), improving scalability
- Uses importance ratio clipping at token level
- Training objective: `J_GRPO(θ) = E[1/G Σ 1/|o_i| Σ min(r_i,t(θ)·A_i, clip(r_i,t(θ), 1-ε, 1+ε)·A_i) - β·KL]`
- Advantage: `A_i = (r_i - mean(rewards)) / std(rewards)`
- **Limitation**: Good tokens can get capped too early by clipping

### DAPO (Dynamic Adaptive Policy Optimization) — 4 Key Improvements
1. **Clip-Higher**: Raises upper bound `1+ε_high` while keeping `1-ε_low` fixed, preventing good tokens from being capped prematurely
2. **Dynamic Sampling**: Prevents massive computation waste from ineffective samples — only trains on samples with mixed positive/negative rewards
3. **Token-Level Gradient Loss**: Ensures long responses don't dilute valuable gradient signals by normalizing per-token rather than per-sequence
4. **Overlong Reward Shaping**: Handles reward assignment for responses that exceed length limits

### GSPO (Group Sequence Policy Optimization) — For MoE Architectures
- **Problem**: GRPO's per-token importance sampling creates huge variance in Mixture-of-Experts architectures due to dynamic expert activation
- **Solution**: Shifts optimization granularity from token-level to **sequence-level**
- Uses "Routing Replay" to stabilize MoE training
- Fundamentally reduces high variance and structural noise from routing decisions

## Relevance to SOMA/Hermes
- GRPO is the training method used for Hermes agent RL environments (see `mlops/training/grpo-rl-training` skill)
- DAPO improvements (especially dynamic sampling and clip-higher) could improve Hermes fine-tuning stability
- GSPO is relevant if we train MoE models for medical domain tasks
- Token-level vs sequence-level optimization tradeoff applies to tool-calling reward models

## Also Found
- "ALTK-Evolve: On-the-Job Learning for AI Agents" (IBM Research, Apr 2026) — on-the-fly agent learning
- "Multimodal Embedding & Reranker Models with Sentence Transformers" (Apr 2026) — relevant to medical image retrieval


## Sources

- https://huggingface.co/blog/NormalUhr/grpo-to-dapo-and-gspo
- https://huggingface.co/blog/ibm-research/altk-evolve
- https://huggingface.co/blog/multimodal-sentence-transformers
