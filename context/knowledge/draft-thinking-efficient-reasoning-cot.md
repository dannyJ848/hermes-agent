# draft-thinking-efficient-reasoning-cot

*Researched: 2026-04-14 14:31 CDT*

# Draft-Thinking: Efficient Reasoning in Long CoT LLMs

**Source:** arXiv 2603.00578 (Feb 2026)

## Key Innovation
Addresses systematic overthinking in long CoT by training models to learn concise "draft-style" reasoning that retains only critical steps. Uses progressive curriculum learning + iterative RL.

## Results
- MATH500: 82.6% reasoning budget reduction at only 2.6% performance drop
- Unlike post-hoc compression, reshapes the reasoning mechanism itself

## 2026 Reasoning Landscape
- Modern reasoning models (GPT-5.4, Claude 4.6) have internalized CoT
- Explicit step-by-step prompting can DEGRADE performance on reasoning models
- Prompting in 2026 = cognitive frame selection, not script engineering
- Key techniques: adaptive depth, thinking budgets, Design/Evaluate framework

## Agent Implications
- Hermes agent loops could apply draft-style reasoning to reduce token waste
- Adaptive reasoning depth = metacognitive budgeting based on task complexity
- Self-reflection and planning phases could use concise draft structure

## Sources

- https://arxiv.org/html/2603.00578v1
- https://karozieminski.substack.com/p/ai-prompting-techniques-reasoning-models-2026
