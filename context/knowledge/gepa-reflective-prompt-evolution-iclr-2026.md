# gepa-reflective-prompt-evolution-iclr-2026

*Researched: 2026-04-03 05:06 CDT*

# GEPA: Reflective Prompt Evolution (ICLR 2026 Oral)

## Summary
GEPA (Genetic-Pareto) is a prompt optimization framework that uses natural language reflection to outperform reinforcement learning methods like GRPO, achieving superior results with dramatically fewer rollouts.

## Key Results
- **Outperforms GRPO** by 6% average, up to 20% on individual tasks
- **Uses 35x fewer rollouts** than RL approaches
- **Outperforms MIPROv2** (leading Bayesian prompt optimizer) by 10%+ (+12% on AIME-2025)
- Accepted to **ICLR 2026 (Oral)** — top-tier venue

## How GEPA Works
1. **Sample trajectories** — reasoning, tool calls, tool outputs from the LLM
2. **Reflect in natural language** — diagnose what went wrong, identify patterns
3. **Propose prompt updates** — modify prompts based on reflection insights
4. **Pareto frontier combination** — merge complementary lessons from multiple attempts
5. **Iterate** — repeat with improved prompts

## Core Insight
Language is an interpretable medium for LLMs — much richer than sparse scalar rewards from policy gradients. Natural language reflection lets LLMs learn high-level rules from just a few examples rather than thousands of RL rollouts.

## Relevance to SOMA
1. **Medical Education Prompts:** GEPA could optimize SOMA's explanation-level prompts (Layman → Professional tier system) by reflecting on quiz outcomes and learning metrics
2. **Bilingual Terminology:** Could optimize cross-lingual alignment prompts for EN/ES medical term mapping
3. **Quiz Generation:** Reflect on quiz quality metrics (difficulty, discrimination, engagement) to improve generation prompts
4. **Cost Efficiency:** 35x fewer rollouts = dramatically lower API costs for prompt optimization compared to RL approaches

## Relevance to Hermes Agent
1. **Self-Optimizing Prompts:** GEPA pattern could be applied to optimize the agent's own system prompt, tool descriptions, and reasoning templates
2. **Dojo Integration:** Replace brute-force RL fine-tuning with reflective prompt evolution for agent self-improvement
3. **Skill Evolution:** Skills could auto-optimize their instructions based on execution outcomes + natural language reflection

## Authors
Lakshya A Agrawal, Shangyin Tan, Dilara Soylu, et al. (Matei Zaharia, Dan Klein, Omar Khattab — Berkeley/Databricks)

## Links
- Paper: https://arxiv.org/abs/2507.19457
- OpenReview: https://openreview.net/forum?id=RQm2KQTM5r
- HuggingFace: https://huggingface.co/papers/2507.19457


## Sources

- https://arxiv.org/abs/2507.19457
- https://openreview.net/forum?id=RQm2KQTM5r
- https://huggingface.co/papers/2507.19457
