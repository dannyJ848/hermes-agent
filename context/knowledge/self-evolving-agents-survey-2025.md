# self-evolving-agents-survey-2025

*Researched: 2026-04-12 12:28 CDT*

# Self-Evolving Agents: Survey (arXiv 2507.21046v4)

## Key Insights for Hermes Agent Self-Improvement

**Framework:** Defines self-evolving agents across 4 axes: WHAT to evolve (models, context, tools, architecture), WHEN (intra-test-time vs inter-test-time), HOW (reward-based, imitation, evolutionary), WHERE (general vs specialized domains).

**Relevant to our system:**
1. **Memory Evolution** (Section 3.2.1): Aligns with our cerebrum memory consolidation + distillation pipeline
2. **Tool Evolution** (Section 3.3): Autonomous tool discovery + mastery through iterative refinement — our tool_planner.py does this
3. **Prompt Optimization** (Section 3.2.2): Our distilled tips serve as optimized prompts injected at inference time
4. **Population-based Evolution** (Section 5.3): Multi-agent evolution — relevant for squad-dev and teammcp patterns
5. **Medical Domain** (Section 6.2): Specialized self-evolution for medical agents — directly applicable to SOMA

**Actionable takeaways:**
- Our domain_certainty.py implements a form of "curriculum learning" for exploration (Section 2.2)
- The distillation pipeline is essentially "intra-test-time in-context learning" self-evolution
- Missing from our stack: explicit reward-based evolution (Section 5.1) — our tips have no reward signal
- Future: implement implicit reward tracking based on tip survival rates (upvote/downvote already exist)

**Evaluation gaps identified:** Adaptivity, retention, generalization metrics are underserved in current benchmarks. Our meta_loop.py survival rate tracking partially addresses this.

Source: Huan-ang Gao et al., Princeton/Tsinghua/CMU, 2025

## Sources

- https://arxiv.org/html/2507.21046v4
