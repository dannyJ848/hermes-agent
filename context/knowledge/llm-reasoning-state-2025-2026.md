# llm-reasoning-state-2025-2026

*Researched: 2026-04-14 22:23 CDT*

# LLM Reasoning State of the Art (2025-2026)

**Source:** Sebastian Raschka, "The State of LLMs 2025" (Dec 2025)

## Key Developments
- **Reasoning models dominated 2025** — DeepSeek R1 (Jan 2025) showed reasoning behavior can emerge from RL without supervised CoT data
- **RLVR (Reinforcement Learning from Verifiable Rewards)** — train reasoning via reward signals on verifiable tasks
- **GRPO (Group Relative Policy Optimization)** — efficient RL training method, cheaper than PPO
- Training SOTA models ~$5M (not $50-500M as previously assumed)
- Reasoning traces improve answer accuracy by decomposing problems

## Relevance to Agent Self-Improvement
- RLVR/GRPO could optimize agent tool-selection and delegation strategies
- Reasoning models show that CoT behavior can be *learned*, not just prompted
- Cross-domain transfer of reasoning strategies (mirrors ADAS paper findings)
- Our tip/skill distillation system parallels the pattern: learn behavioral improvements from experience

## Open Problems (per Raschka)
- Reasoning doesn't overcome fundamental probabilistic biases
- Scaling reasoning traces has diminishing returns
- Training efficiency still a bottleneck for smaller organizations


## Sources

- https://magazine.sebastianraschka.com/p/state-of-llms-2025
