# deepfact-audit-then-score-trust-verification

*Researched: 2026-04-05 07:40 CDT*

# DeepFact: Audit-then-Score for Fact Verification in AI Agents

**Source:** arxiv 2603.05912v1 (March 2026) — Huang et al.

## Key Findings

### The 60% Ceiling
Expert annotators hit a ~60% accuracy ceiling when verifying claims in AI-generated research reports. Static ground truth benchmarks degrade over time as models evolve. This directly validates the need for dynamic trust scoring in agent memory systems like Cerebrum.

### Audit-then-Score (AtS) Protocol
Two-phase verification:
1. **Audit Phase:** An auditor (human or agent) reviews claims and identifies errors/gaps
2. **Score Phase:** Claims are scored against audited evidence, with iterative refinement

Key insight: auditing consolidates evidence, while verifiers expand coverage. Multiple audit rounds progressively improve accuracy.

### Agents as Auditor Proxies
- LLM agents can serve as effective auditors (non-regressive — they don't degrade quality)
- Agent auditors complement human annotators rather than replacing them
- Grouping claims reduces cost with minimal quality trade-off

### Relevance to Cerebrum Trust Scoring
- The F-G-R Trust Tuple (Formation, Grounding, Recency) in our epistemic-trust-scoring skill aligns with AtS's multi-round verification
- The 60% ceiling suggests single-pass trust scoring is insufficient — iterative auditing is needed
- Risk-weighted claim sampling (importance + risk stratification) could improve our memory decay prioritization
- Domain drift and fragmentation amplify annotation burden — relevant to Cerebrum's cross-domain knowledge

### Architecture Implications
- Trust scoring should be multi-round, not single-pass
- Higher-risk memories (those informing decisions) should get more audit cycles
- Agent-based self-auditing of stored facts is viable and cost-effective


## Sources

- https://arxiv.org/html/2603.05912v1
