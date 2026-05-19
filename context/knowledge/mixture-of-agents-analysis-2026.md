# mixture-of-agents-analysis-2026

*Researched: 2026-04-05 03:19 CDT*

# Mixture of Agents (MoA) Analysis (Zylos Research, Feb 2026)

## Key Findings
1. **MoA**: Multiple LLMs orchestrated through prompts (no weight changes) outperforms GPT-4 on benchmarks
2. **Self-MoA**: Same model called multiple times outperforms traditional multi-model MoA by 6.6%
3. **Quality-consolidation > diversity**: The field is shifting from diverse models to quality consolidation
4. **Tradeoff**: Cost-optimal vs GPT-4, but introduces latency from inter-agent communication

## Implications for Our Architecture
- Single-model (GLM-5.1) with self-reflection is the RIGHT approach
- Level 3 (Cross-Model) score of 10/100 is misleading — Self-MoA suggests quality > diversity
- Our MARS pattern (single-cycle self-improvement) aligns with Self-MoA findings
- Instead of adding models, focus on: (1) better self-reflection, (2) multiple passes, (3) quality consolidation

## Action Items
- Reconsider Level 3 scoring: should reward self-reflection over multi-model
- Implement Self-MoA pattern: call GLM-5.1 multiple times with different prompts for consensus
- The council_decide tool already implements this pattern (3 free models + judge)


## Sources

- https://zylos.ai/research/2026-02-06-mixture-of-agents
