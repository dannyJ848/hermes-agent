# self-revising-agent-llm-attribution

*Researched: 2026-04-09 10:44 CDT*

# How Much LLM Does a Self-Revising Agent Actually Need? (Apr 2026)

**Paper:** arXiv:2604.07236

## Key Question
Which part of an agent's competence comes from the LLM itself, and which comes from explicit structure around it? Current agents place world modeling, planning, and reflection all inside a single LLM loop, making this attribution impossible.

## Why It Matters for Agent Design
- **Scaffolding vs capability:** Agents that seem "smart" may be benefiting more from prompt engineering, tool scaffolding, and retry logic than from actual model reasoning. Knowing the difference lets you allocate resources better.
- **Smaller model opportunities:** If most capability comes from structure (skills, memory injection, tool routing), then you can use cheaper models for routine tasks and reserve expensive models for genuine reasoning.
- **Architecture insight:** Separates what should be in the model (semantic understanding, generalization) from what should be in the system (tool dispatch, retry logic, memory management).

## Relevance to Hermes
This directly validates Hermes's architecture: skills, memory injection, and tool routing ARE the "explicit structure" that makes a modest model perform like a frontier model. The paper suggests measuring which agent behaviors degrade when you swap the LLM to identify what's truly model-dependent vs structure-dependent.

## Actionable Insight
Run an A/B experiment: delegate identical tasks to different models and score results. Tasks where all models score similarly are "structure-driven" (the scaffolding does the work). Tasks with high variance are "model-driven" (genuine reasoning needed). Use this to optimize model routing.

## Sources

- https://arxiv.org/abs/2604.07236
