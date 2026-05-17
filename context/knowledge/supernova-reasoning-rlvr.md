# supernova-reasoning-rlvr

*Researched: 2026-04-09 20:55 CDT*

# SUPERNOVA: Eliciting General Reasoning in LLMs with RL on Natural Instructions

**Date:** April 9, 2026
**Authors:** Suvarna, Phan, Beikzadeh, Bansal, Gabriel
**arXiv:** 2604.08477

## Key Insight
Instruction-tuning datasets with expert-annotated ground-truth encode rich reasoning patterns that can be systematically adapted for RLVR (Reinforcement Learning with Verifiable Rewards). This extends RLVR beyond math/code to general reasoning (causal inference, temporal understanding).

## Methodology
- Data curation framework for RLVR targeting general reasoning
- 100+ controlled RL experiments analyzing data design choices
- Three key factors studied: (i) source task selection, (ii) task mixing strategies, (iii) synthetic interventions

## Key Findings
1. **Source task selection is non-trivial** — significantly impacts downstream reasoning
2. **Per-task selection > average-based selection** — selecting tasks based on individual target task performance outperforms overall average strategies
3. **Up to 52.8% improvement on BBEH** across model sizes
4. Outperforms Qwen3.5 on BBEH, Zebralogic, and MMLU-Pro

## Relevance to Agent REASONING Domain
- Directly applicable to how agents should select training data for reasoning improvement
- Task-specific selection beating average selection suggests agents need specialized reasoning paths, not general-purpose ones
- Synthetic interventions for data quality improvement parallels our distillation pipeline's quality filtering


## Sources

- https://arxiv.org/abs/2604.08477
