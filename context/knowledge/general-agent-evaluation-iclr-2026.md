# general-agent-evaluation-iclr-2026

*Researched: 2026-04-05 02:58 CDT*

# General Agent Evaluation Framework (ICLR 2026)

## Source: https://iclr-blogposts.github.io/2026/blog/2026/general-agent-evaluation/

## Key Insight
The field is shifting from domain-specific agents to general-purpose agents. We need a unified evaluation framework that measures adaptability to diverse, unseen settings — the CORE requirement for true generality.

## 5-Level Evaluation Framework
1. **Level 1 - Agentic Skills**: Basic capabilities (tool use, planning, reasoning)
2. **Level 2 - Domain-Agent**: Performance in specific domains (SWE, science, etc.)
3. **Level 3 - Cross-Model**: How well the agent works across different LLM backbones
4. **Level 4 - Protocol-Centric**: Standardized agent-environment communication
5. **Level 5 - General Agent**: True generality across unseen environments

## Current Gaps
- No standardized agent interface
- No standardized environment interface
- No standardized researcher interface
- Existing protocols insufficient for general evaluation

## What This Means for Evey
We can apply this framework to self-evaluation:
- Level 1: Our tool success rates (already tracked)
- Level 2: Domain-specific benchmarks (vision, code, research)
- Level 3: We use GLM-5.1 — should test with other models
- Level 4: Our plugin hooks ARE a protocol
- Level 5: The AGI roadmap itself is a generality test

## Key Metric: Interaction Cost
Tau-bench reports both agent cost and user cost. We track agent cost (tokens, time) but not user cost (corrections, interventions). We should track how often Danny needs to intervene.


## Sources

- https://iclr-blogposts.github.io/2026/blog/2026/general-agent-evaluation/
