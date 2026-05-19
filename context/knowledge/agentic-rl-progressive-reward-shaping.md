# agentic-rl-progressive-reward-shaping

*Researched: 2026-04-09 14:14 CDT*

# Progressive Reward Shaping for Agentic RL (PRS + VSPO)

**Paper:** arXiv:2512.07478 (Su et al., Dec 2025 / revised Jan 2026)
**Title:** Enhancing Agentic RL with Progressive Reward Shaping and Value-based Sampling Policy Optimization

## Key Contributions

### 1. Progressive Reward Shaping (PRS)
- Curriculum-inspired reward design for Tool-Integrated Reasoning (TIR) agents
- Dense, stage-wise feedback instead of binary 0-1 signals
- Stage 1: Parseable, properly formatted tool calls
- Stage 2: Factual correctness and answer quality
- Short-form QA: length-aware BLEU scoring for concise answers
- Long-form QA: LLM-as-a-Judge scoring to prevent reward hacking

### 2. Value-based Sampling Policy Optimization (VSPO)
- Enhanced GRPO variant that fixes gradient degradation
- Problem: identical rewards within GRPO rollout group → zero advantage → no learning
- Fix: replaces zero-advantage samples with prompts selected by task-value metric (balancing difficulty + uncertainty)
- Applies value-smoothing clipping for stable gradient updates

### 3. Results
- PRS consistently outperforms traditional binary rewards
- VSPO achieves superior stability, faster convergence, higher final performance vs SFT, PPO, GRPO baselines
- PRS + VSPO together yield TIR agents that generalize better across domains

## Relevance to Hermes Agent
- Hermes uses GRPO for RL training (hermes-atropos-environments skill)
- The zero-advantage gradient degradation problem in GRPO directly applies
- PRS reward shaping could improve Hermes's tool-calling RL environments
- VSPO's value-based sampling could replace standard GRPO in Atropos environments

## Cross-reference
- Also see arXiv:2512.11277 (Rawat et al.) — GRPO for reasoning-action synergy in conversational agents, 1.5% improvement over SFT, 40% over vanilla Qwen3-1.7B


## Sources

- https://arxiv.org/abs/2512.07478
- https://arxiv.org/abs/2512.11277
