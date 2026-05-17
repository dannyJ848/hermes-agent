# supernova-rlvr-general-reasoning

*Researched: 2026-04-10 01:29 CDT*

# SUPERNOVA: RL with Verifiable Rewards for General Reasoning (Apr 2026)

**Paper:** arXiv:2604.08477 (Apr 9, 2026)
**Authors:** Suvarna, Phan, Beikzadeh, Bansal, Gabriel

## Key Findings

1. **Data curation > model architecture for RLVR.** Source task selection is non-trivial and significantly impacts downstream reasoning performance.

2. **Per-target task selection > average performance.** Selecting training tasks based on their performance for individual target tasks outperforms strategies based on overall average performance.

3. **Instruction-tuning data adapts well to RLVR.** Expert-annotated ground-truth from instruction-tuning datasets encodes rich reasoning patterns that can be systematically adapted.

4. **52.8% improvement on BBEH** across model sizes, beating Qwen3.5 baselines.

## Three Key Factors for RLVR Data Design
- (i) Source task selection — most impactful
- (ii) Task mixing strategies — composition matters
- (iii) Synthetic interventions for quality improvement

## Relevance to Hermes Agent
- Hermes RL environments (Atropos) could benefit from task-specific data curation rather than generic mixing
- The "per-target selection" insight applies to tool-calling RL: train on tasks most similar to the target agent capability
- 100+ controlled experiments provide empirical backing for data design decisions


## Sources

- https://arxiv.org/abs/2604.08477
