# rl-training-llm-advances-2025

*Researched: 2026-04-09 23:43 CDT*

# RL Training for LLMs — 2025-2026 Advances

## Key Developments

### DeepSeek R1 & RLVR (Jan 2025)
- Reinforcement Learning with Verifiable Rewards (RLVR) + GRPO algorithm
- Open-weight reasoning model comparable to proprietary models
- Training cost: ~$294K on top of DeepSeek V3 (which was ~$5M)
- Key insight: "V" in RLVR = verifiable rewards → deterministic correctness labels
- Eliminates bottleneck of expensive human preference labels (RLHF) or written responses (SFT)
- Enables scaling compute during post-training to unlock new capabilities

### GRPO (Group Relative Policy Optimization)
- Modified policy optimization that works well for generation models
- Flow-GRPO extends to generation models with stable RL alignment
- Superior to PPO for LLM reasoning tasks due to simpler reward shaping
- Active research area: arxiv 2603.06623 surveys advances

### Training Pipeline (2025 State of Art)
1. Pre-training (still expensive but ~10x cheaper than assumed)
2. SFT (supervised fine-tuning for instruction following)
3. RLHF or RLVR (post-training for alignment and reasoning)
4. GRPO as preferred RL algorithm for reasoning capabilities

### Implications for Agent Training
- RLVR is ideal for tool-calling agents — tool outputs are naturally verifiable (success/failure)
- GRPO could optimize Hermes agent's tool selection and delegation strategies
- Cost democratization means open-source agent fine-tuning is now accessible

## Sources
- Sebastian Raschka, "The State of LLMs 2025", Dec 2025
- arxiv 2603.06623, "Advances in GRPO for Generation Models: A Survey"


## Sources

- https://magazine.sebastianraschka.com/p/state-of-llms-2025
- https://arxiv.org/abs/2603.06623
