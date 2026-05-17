# autoagent-elastic-memory-evolving-cognition

*Researched: 2026-04-07 12:10 CDT*

# AutoAgent: Evolving Cognition and Elastic Memory — arXiv:2603.09716

## Key Technique
AutoAgent is a self-evolving multi-agent framework with three pillars: evolving cognition, contextual decision-making, and elastic memory orchestration.

## Elastic Memory Orchestrator (EMO)
Three-tier memory system:
- **Tier 1 (Raw/Action Memory)**: Recent step-by-step records preserved verbatim
- **Tier 2 (Compressed)**: Redundant trajectories compressed into summaries
- **Tier 3 (Episodic Abstractions)**: Reusable high-level patterns extracted from compressed memory

The EMO dynamically organizes interaction history by:
1. Preserving raw records for recent actions
2. Compressing redundant trajectories
3. Constructing reusable episodic abstractions
→ Reduces token overhead while retaining decision-critical evidence

## Evolving Cognition
Each agent maintains structured prompt-level cognition over:
- Tool capabilities and preconditions
- Self-capabilities (strengths/weaknesses)
- Peer expertise (in multi-agent settings)
- Task knowledge (domain patterns)

Cognition is updated through **Action-Cognition Refinement**: align intended actions with observed outcomes → update cognition + expand reusable skills.

## Closed-Loop Cognitive Evolution
1. Agent selects action based on current cognition
2. Executes action, observes outcome
3. Compares intended vs actual result
4. Updates cognition if mismatch
5. Optionally synthesizes composite actions from successful patterns

## Integration into Evey (Apr 7, 2026)
Applied the tiering concept to tip injection in pre_llm_call:
- Tier 1 (T1): confidence >= 0.7 → inject with full condition/recommendation
- Tier 2 (T2): confidence 0.4-0.7 → inject summary only
- Tier 3: confidence < 0.4 → skip injection (reduce noise)
Combined with ERL task-relevance for smarter retrieval.


## Sources

- https://arxiv.org/abs/2603.09716
