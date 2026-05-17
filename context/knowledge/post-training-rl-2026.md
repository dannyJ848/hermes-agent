# post-training-rl-2026

*Researched: 2026-04-10 09:50 CDT*

# Post-Training RL 2026: GRPO, DAPO, Agentic Training

RLHF replaced by 3-stage pipeline: SFT → Preference Optimization → Environment RL.

**GRPO** eliminates critic model, uses group-relative advantages (reward_i - mean)/std. Provably optimal. Used in DeepSeek-R1.

**DAPO** stabilizes long CoT with Clip-Higher, Dynamic Sampling, Token-level PG Loss.

**Agentic Training**: NVIDIA NeMo Gym provides multi-turn RL environments. Multi-Turn RL paper (arxiv 2604.02869) addresses reward calibration for tool-calling. GiGPO (NeurIPS 2025) uses group-in-group optimization for ALFWorld/WebShop.

**Key insight for Hermes**: Tool-calling reward design needs multi-turn calibration. GRPO group sampling is the right approach for Hermes RL environments.

## Sources

- https://llm-stats.com/blog/research/post-training-techniques-2026
- https://arxiv.org/html/2604.02869v1
- https://neurips.cc/virtual/2025/poster/118123
