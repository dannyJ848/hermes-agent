# RL Training for Tool-Calling Agents — MT-GRPO + GTPO

*Researched: 2026-04-10 03:27 CDT*

# RL Training for Tool-Calling Agents (Apr 2026)

**Paper:** arXiv:2604.02869 — Multi-Turn RL for Tool-Calling Agents with Iterative Reward Calibration

## Key Results
- First MT-GRPO + GTPO applied to realistic multi-turn tool-calling (Tau-Bench)
- Qwen3.5-4B: +2.9pp, beats GPT-4.1/GPT-4o (50x smaller)
- Qwen3-30B MoE: +11.5pp, approaches Claude Sonnet 4.5

## Critical Insights
1. **Dense rewards can HURT** — up to 14pp degradation from naive per-turn rewards (advantage misalignment)
2. **IRC (Iterative Reward Calibration)** fixes this via empirical discriminative analysis
3. **GTPO hybrid advantage** eliminates advantage misalignment
4. Training reduces turns by 50%, speed by 65%, verbosity by 3.5x while improving accuracy

## Relevance to Hermes
- Applicable to Hermes Atropos RL environments
- IRC methodology improves reward design for tool-calling training
- Tau-Bench as potential evaluation benchmark


## Sources

- https://arxiv.org/html/2604.02869v1
- https://fireworks.ai/blog/best-practices-for-multi-turn-RL
