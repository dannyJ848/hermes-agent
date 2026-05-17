# evotool-self-evolving-tool-optimization

*Researched: 2026-04-12 08:40 CDT*

# EvoTool: Self-Evolving Tool-Use Policy Optimization in LLM Agents

**Paper:** arXiv:2603.04900 (Mar 2026) — Shuo Yang et al.

## Key Innovation
EvoTool decomposes agent tool-use into 4 modular components: **Planner → Selector → Caller → Synthesizer**, and optimizes each independently via evolutionary (gradient-free) methods rather than monolithic RL.

## Three Core Mechanisms
1. **Trajectory-Grounded Blame Attribution** — diagnostic traces localize failures to specific modules (which module caused the error?)
2. **Feedback-Guided Targeted Mutation** — edits only the blamed module via natural-language critique
3. **Diversity-Aware Population Selection** — preserves complementary candidates to avoid local optima

## Results
- +5 points over strong baselines on both GPT-4.1 and Qwen3-8B across 4 benchmarks
- Superior efficiency and transferability vs monolithic approaches
- Gradient-free: no backprop needed, works with API-only models

## Relevance to Hermes
- Hermes already has modular tool dispatch (registry.py → model_tools.py → handle_function_call)
- The blame attribution pattern maps directly to our delegation quality tracking
- Could implement: track which module (tool selection, argument formatting, result parsing) causes failures, then mutate only that module's prompts/rules
- Tool Intelligence data already provides per-tool success rates — EvoTool provides a framework for acting on that data


## Sources

- https://arxiv.org/abs/2603.04900
