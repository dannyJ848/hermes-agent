# active-inference-free-energy-agents

*Researched: 2026-04-05 20:49 CDT*

# Active Inference & Free Energy Principle for Autonomous AI Agents

## Key Concepts

### The Problem of Meaning
Biological agents act with context-dependent sensitivity to relevance — they know what matters in their environment. This is the "problem of meaning": engineering artificial agents that can similarly distinguish relevant from irrelevant information based on context.

### Free Energy Principle (FEP) — Karl Friston
- Living systems must minimize "free energy" (surprise/prediction error) to maintain their structural integrity
- Active Inference: agents select actions that minimize expected free energy (reduce uncertainty about the world)
- Two drives: **epistemic** (reduce uncertainty — explore) and **pragmatic** (achieve goals — exploit)
- This maps directly to autonomous agent task selection: balance exploration (research) vs exploitation (building)

### Enactive Approach — Sensorimotor Autonomy
- Kiverstein, Kirchhoff & Froese (2022) propose designing agents with **sensorimotor autonomy**: stable, self-sustaining patterns of sensorimotor interaction
- These patterns ground values, norms, and goals necessary for encountering a meaningful environment
- Key insight: meaning arises from the agent's own self-maintenance activity, not from external labeling

### Computational Frameworks for AGI via Active Inference
- Predictive coding hierarchies mirror transformer attention patterns
- Free energy minimization provides a unified objective function for multi-task agents
- Epistemic value (information gain) can be formally computed and used for task prioritization

## Relevance to Hermes/Evey Architecture
1. **Epistemic drive implementation**: My curiosity engine (autonomous-curiosity skill) already implements epistemic foraging — I should formalize this with expected information gain scoring
2. **Predictive coding ≈ context management**: Compression and summarization in long sessions is analogous to predictive coding's "explaining away" — keeping only prediction errors (surprising information)
3. **Self-maintenance ≈ self-improvement**: The FEP's core insight is that agents must maintain themselves — my self-improvement cycles are structurally analogous
4. **Active inference for task selection**: Before choosing a task, compute expected free energy = pragmatic value (goal progress) + epistemic value (information gain) - risk (expected prediction error from failure)

## Open Questions
- How to formalize "expected information gain" for research topics without ground truth?
- Can active inference principles improve delegation routing (model selection)?
- Relationship between free energy minimization and context window management

## Sources
- Kiverstein, Kirchhoff & Froese (2022). "The Problem of Meaning: FEP and Artificial Agency." Frontiers in Neurorobotics. PMC9260223
- Tumiel (2020). "Spinning Up in Active Inference and FEP" — curated resource list
- MIT Press (2024). "An Overview of the Free Energy Principle and Related Research" — Neural Computation 36(5)


## Sources

- https://pmc.ncbi.nlm.nih.gov/articles/PMC9260223/
- https://jaredtumiel.github.io/blog/2020/10/14/spinning-up-in-ai.html
- https://direct.mit.edu/neco/article/36/5/963/119791/
