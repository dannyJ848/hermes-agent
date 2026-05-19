# emergent-coordination-multi-agent-llm

*Researched: 2026-04-13 21:03 CDT*

# Emergent Coordination in Multi-Agent Language Models

**Paper:** Emergent Coordination in Multi-Agent Language Models (2025)

## Key Insight
Multi-agent LLM systems CAN exhibit emergent synergistic coordination, but only when agents are given **Theory of Mind (ToM) prompting** — explicit instructions to model other agents' behaviors. Simple persona assignment is NOT enough.

## The Three Intervention Conditions Tested
1. **Plain** — Basic task instructions only → oscillation, no coordination
2. **Persona** — Each agent gets distinct personality/traits → some differentiation but no goal-directed complementarity
3. **Theory of Mind (ToM)** — Personas + instruction to model others' behaviors → identity-linked differentiation + goal-directed complementarity

## Methodology
- Used a Group Guessing Game: agents propose integers whose sum must match a hidden target
- No inter-agent communication; only group-level "too high" or "too low" feedback
- Identical strategies cause oscillation (everyone adjusts same direction) — only complementary strategies succeed
- Measured using information decomposition (Partial Information Decomposition framework)

## Actionable Takeaway for Agent Design
When building multi-agent systems, don't just assign roles/personas. Add **explicit ToM instructions**: "Consider what the other agents are likely doing and adjust your strategy to complement theirs." This is what transforms parallel workers into a coordinated team.

## Synergy Measurement
- They use information-theoretic measures to quantify synergy (information only available jointly, not individually)
- Synergy = redundant information subtracted from total mutual information
- This gives a principled way to measure whether agents are truly coordinating vs. just independently performing well


## Sources

- https://pages.cs.wisc.edu/~thodima/blog/2025/emergent-coordination-in-multiagent-language-models/
- https://arxiv.org/abs/2505.14986
