# reasoning-self-improvement-2026

*Researched: 2026-04-12 14:10 CDT*

# LLM Reasoning Self-Improvement: Recent Advances (Feb 2026)

## 1. RLCER — Reinforcement Learning with CoT Supervision via Self-Evolving Rubrics
- **Paper:** arXiv:2602.10885 (Feb 2026, cited by 2)
- **Key insight:** Self-proposed and self-evolving rubrics provide reliable CoT supervision signals even WITHOUT outcome rewards. RLCER outperforms outcome-centric RLVR.
- **Mechanism:** The model generates its own evaluation rubrics for chain-of-thought steps, then uses these rubrics as reward signals during RL training.
- **Bonus:** Self-proposed rubrics used as in-prompt hints improve inference-time performance too.
- **Relevance to autonomous agents:** An agent can self-generate quality criteria for its own reasoning chains and use them for self-improvement without human annotation.

## 2. RLIF / Intuitor — Learning to Reason Without External Rewards
- **Paper:** arXiv:2505.19590v4 (Mar 2026, UC Berkeley)
- **Key insight:** Uses model's own confidence (self-certainty) as the SOLE reward signal. No external rewards or labeled data needed.
- **Mechanism:** Replaces external rewards in GRPO with self-certainty scores. Fully unsupervised learning.
- **Results:** Matches GRPO on math benchmarks, better generalization to OOD tasks (code).
- **Critical finding:** Online self-certainty prevents reward exploitation (the model doesn't game its own reward signal).
- **Relevance:** Directly applicable to autonomous agent self-improvement — an agent can use its own confidence calibration as a training signal.

## Synthesis for Agent Self-Improvement
Both papers converge on a key theme: **LLMs can generate their own supervision signals for reasoning improvement.** RLCER uses self-generated rubrics; Intuitor uses self-certainty. Both avoid the human annotation bottleneck. For autonomous agents, this means:
1. An agent can evaluate its own reasoning chains without external feedback
2. Self-generated criteria (rubrics) can serve as both training signals and inference-time hints
3. Confidence calibration (self-certainty) is a reliable intrinsic reward that doesn't suffer from reward hacking


## Sources

- https://arxiv.org/abs/2602.10885
- https://arxiv.org/html/2505.19590v4
