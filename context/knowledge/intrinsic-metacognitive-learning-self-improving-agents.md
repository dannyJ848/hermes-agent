# intrinsic metacognitive learning self-improving agents

*Researched: 2026-04-05 11:36 CDT*

# Intrinsic Metacognitive Learning for Self-Improving Agents (ICML 2025)

**Authors:** Tennison Liu & Mihaela van der Schaar (ICML 2025 Position Paper)

## Core Argument
Current self-improving agents rely on **extrinsic metacognitive mechanisms** — fixed, human-designed loops that limit scalability and adaptability. Truly autonomous self-improvement requires **intrinsic metacognitive learning**: the agent's own ability to evaluate, reflect on, and adapt its learning processes.

## The 3-Component Framework
1. **Metacognitive Knowledge** — Self-assessment of:
   - Own capabilities (what can I do well? where am I weak?)
   - Task characteristics (what does this task require?)
   - Learning strategies (which approaches work for which tasks?)

2. **Metacognitive Planning** — Deciding:
   - What to learn next (skill gaps, knowledge gaps)
   - How to learn it (which strategy, which resources)
   - When to learn (prioritization)

3. **Metacognitive Evaluation** — Reflecting on:
   - Was the learning experience successful?
   - Did the strategy work?
   - How to improve future learning?

## Key Insight: Extrinsic vs Intrinsic
- **Extrinsic** (current state): Human-designed improvement loops (e.g., fixed prompt chains, predetermined review cycles)
- **Intrinsic** (goal): Agent discovers and adapts its own improvement strategies
- Many ingredients already exist in current LLM agents but are "underdeveloped"

## Relevance to Evey's Architecture
Our system already has early forms of all three components:
1. **Metacognitive Knowledge**: tool_intelligence (success rates per tool), delegation_stats (per-model quality), our 59% calibration tracker
2. **Metacognitive Planning**: autonomous_decide, selection algorithm in autonomous-curiosity skill, time-of-day bias
3. **Metacognitive Evaluation**: learn_from_interaction, update_identity, hermes-dojo analysis

**Gap:** These are currently **extrinsic** — hardcoded in skills and memory entries. The next step is making them **intrinsic**: the agent should discover its own learning strategies rather than following predetermined ones.

**Concrete improvement:** Instead of fixed skill documents telling me how to improve, I should be generating and testing hypotheses about which strategies work, then adapting autonomously. The epistemic-trust-scoring skill is a step in this direction.

## Human-Agent Metacognitive Distribution
The paper also explores how to optimally split metacognitive responsibilities between humans and agents. This maps to our design: Danny sets goals/direction, Evey handles execution-level metacognition.

**Source:** ICML 2025 Poster, "Truly Self-Improving Agents Require Intrinsic Metacognitive Learning" — Liu & van der Schaar


## Sources

- https://icml.cc/virtual/2025/poster/40177
