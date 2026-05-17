# gepa-prompt-optimization-production-2026

*Researched: 2026-04-07 13:43 CDT*

# GEPA Prompt Optimization — Production Ready (Feb 2026)

## Key Updates
- GEPA (Genetic-Pareto Prompt Evolution) now integrates with **Pydantic AI** and **Pydantic Evals**
- Uses `Agent.override()` to inject candidate prompts during optimization without modifying agent definitions
- Gradient-free optimizer using natural language reflection (not policy gradients)
- **Outperforms MIPROv2** by 10%+ (e.g., +12% on AIME-2025)
- Decagon published production optimization guide for GEPA

## Why This Matters for Hermes
- The `hermes-agent-self-evolution` skill already references GEPA/DSPy
- GEPA could optimize Hermes' system prompts (tool dispatch, delegation, self-correction)
- The Pydantic Evals integration provides a ready-made evaluation harness
- Could be applied to SOMA's medical prompt templates

## Integration Path
1. Define evaluation cases for key Hermes behaviors (tool calling, delegation, self-correction)
2. Run GEPA against current system prompts
3. Compare evolved prompts vs. originals on evaluation metrics
4. Deploy winners via skill patches

## Sources
- https://pydantic.dev/articles/prompt-optimization-with-gepa
- https://arxiv.org/abs/2507.19457
- https://github.com/gepa-ai/gepa
- https://decagon.ai/blog/optimizing-gepa-for-production


## Sources

- https://pydantic.dev/articles/prompt-optimization-with-gepa
- https://arxiv.org/abs/2507.19457
- https://github.com/gepa-ai/gepa
