# tool-r0-self-evolving-tool-learning

*Researched: 2026-04-07 01:15 CDT*

## Tool-R0: Zero-Data Self-Play for Tool Learning

**Paper:** arxiv 2602.21320 (Feb 2026), UIUC + ETH Zurich

**Key insight:** LLM agents can learn tool use from scratch via self-play RL — no human-annotated data needed. A Generator proposes tasks at the Solver's frontier; the Solver learns to solve them with real tool calls. Both co-evolve.

**Results:** 92.5% improvement over base model, surpasses supervised baselines.

**Reward design:** Format (parseability), Validity (tool grounding), Curriculum (progressive difficulty), Accuracy (task completion).

**Hermes application:** The Generator-Solver pattern maps to skill_factory — Generator creates practice scenarios, Solver attempts them. Curriculum reward aligns with dojo difficulty estimation.

**Risk:** Self-play can overfit to synthetic task distributions that don't reflect real-world tool usage patterns.


## Sources

- https://arxiv.org/abs/2602.21320
