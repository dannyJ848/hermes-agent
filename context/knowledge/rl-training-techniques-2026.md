# rl-training-techniques-2026

*Researched: 2026-04-10 05:42 CDT*

# RL Training Techniques for LLM Agents (2026)

## Key Papers & Techniques

### MT-GRPO + GTPO for Tool-Calling (arxiv:2604.02869, Apr 2026)
- **First application** of Multi-Turn GRPO + GTPO for realistic tool-calling agents (Tau-Bench airline benchmark)
- **Iterative Reward Calibration (IRC)**: Naive dense per-turn rewards DEGRADE performance by up to 14pp due to advantage misalignment. IRC uses empirical discriminative analysis to calibrate rewards.
- **GTPO Hybrid Advantage**: Eliminates advantage misalignment between reward discriminativeness and advantage direction
- **Dead Turn Gradient Focusing**: Prevents gradient dilution from turns with no useful signal
- **Results**: Qwen3.5-4B improved 63.8%→66.7% on Tau-Bench (exceeding GPT-4.1 and GPT-4o). Qwen3-30B-A3B improved 58.0%→69.5% (approaching Claude Sonnet 4.5 at 70.0%)
- **Key insight**: Sparse rewards accidentally work better than naive dense rewards. Learning rate accounts for 70% of improvement, gradient focusing 25%, advantage misalignment fix 5%.

### Post-Training Stack (2025-2026 Survey)
**RLHF is dead.** Every major model (DeepSeek-R1, Nemotron 3 Super, GPT-5.3 Codex) uses a new stack:
1. **SFT** (1-10M curated examples) → teaches format
2. **Preference Optimization** (SimPO/KTO/ORPO) → aligns values
3. **RL with Verifiable Rewards** (GRPO/DAPO) → discovers new strategies

**GRPO**: Eliminates critic model. Samples 8-64 responses per prompt, normalizes rewards within group. Provably optimal within class of policy gradient methods.
**DAPO**: Stabilizes long-horizon RL. Clip-Higher (prevents entropy collapse), Dynamic Sampling, Token-level Policy Gradient Loss, Overlong Reward Shaping.
**SimPO**: No reference model needed. Uses average log probability as implicit reward. Outperforms DPO by 6.4pts AlpacaEval 2.
**KTO**: Binary feedback (thumbs up/down) instead of pairwise preferences.
**ORPO**: Merges SFT + alignment into single stage.

### Agentic Training
- **GiGPO** (NeurIPS 2025): Group-in-Group Policy Optimization for LLM agent training. Evaluated on ALFWorld, WebShop, search-augmented QA.
- **NVIDIA NeMo Gym**: Interactive RL environments for training LLM agents. Multi-turn rollouts, tool-calling verification.
- **veRL**: Volcano Engine RL for LLMs. Supports hybrid-policy optimization, rStar2-Agent for multi-step tool-calling math.

## Relevance to Hermes Agent
- MT-GRPO + IRC directly applicable to training Hermes for tool-calling (terminal, file ops, web research)
- Sparse rewards (task success/fail) may work better than dense per-step rewards for agent training
- SimPO's reference-free approach reduces training infrastructure requirements
- DAPO's techniques for long-chain-of-thought stability relevant for multi-tool agent trajectories


## Sources

- https://arxiv.org/html/2604.02869v1
- https://llm-stats.com/blog/research/post-training-techniques-2026
- https://neurips.cc/virtual/2025/poster/118123
- https://github.com/verl-project/verl
