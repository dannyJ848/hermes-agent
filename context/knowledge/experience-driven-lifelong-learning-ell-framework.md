# experience-driven-lifelong-learning-ELL-framework

*Researched: 2026-04-12 04:38 CDT*

# Experience-Driven Lifelong Learning (ELL) Framework

**Source:** arxiv:2508.19005 (Cai et al., East China Normal University / Shanghai AI Lab)
**Date:** 2025-2026

## Core Framework — 4 Principles

1. **Experience Exploration:** Agents learn through self-motivated interaction with dynamic environments, navigating interdependent tasks and generating rich experiential trajectories.
2. **Long-term Memory:** Agents preserve and structure historical knowledge — personal experiences, domain expertise, commonsense reasoning — into a persistent memory system.
3. **Skill Learning:** Agents autonomously improve by abstracting recurring patterns from experience into reusable skills, actively refined and validated for new tasks.
4. **Knowledge Internalization:** Agents internalize explicit/discrete experiences into implicit/intuitive capabilities as "second nature."

## StuLife Benchmark

Simulates a student's holistic college journey across 3 phases and 10 sub-scenarios. Includes:
- In-class tasks (course selection, library study)
- Daily campus tasks (club activities, advisor meetings)
- Examination tasks (testing accumulated knowledge)

## Agent Failure Modes Identified

1. **Long-Term Memory Failure** — forgetting previously learned facts
2. **Proactive Initiative Failure** — not acting without explicit prompting
3. **Tool-Use & Long-Context Consistency Failure** — contradictions across long sessions
4. **Goal Decomposition Failure** — inability to break complex goals into steps
5. **Proactive Planning & Strategic Memory Failure** — poor forward planning
6. **Signal-vs-Noise Prioritization Failure** — inability to filter important from irrelevant

## Relevance to Hermes/Cerebrum

- Maps to our 4-tier memory: episodic→semantic→procedural→distilled tips
- Knowledge internalization = our distillation pipeline (experience→tip→behavioral rule)
- Failure mode #6 (signal-vs-noise) directly explains our low optimization/recovery tip survival rates
- StuLife benchmark pattern could inspire agent self-evaluation scenarios


## Sources

- https://arxiv.org/html/2508.19005v5
