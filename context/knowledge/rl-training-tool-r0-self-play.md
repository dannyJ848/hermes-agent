# rl-training-tool-r0-self-play

*Researched: 2026-04-09 23:28 CDT*

# Tool-R0: Self-Evolving LLM Agents for Tool-Learning from Zero Data

**Paper:** arXiv 2602.21320 (2025) — UIUC + ETH Zurich
**Authors:** Emre Can Acikgoz, Cheng Qian, Jonas Hübotter, Heng Ji, Dilek Hakkani-Tür, Gokhan Tur

## Key Innovation
Tool-R0 trains tool-calling agents from scratch using self-play RL with **zero pre-existing data**. Two models co-evolve:
- **Generator:** Proposes challenging tasks at the Solver's competence frontier
- **Solver:** Learns to solve tasks using real-world tool calls

## Reward Design (3 components)
1. **Format Reward (r_fmt):** Tags and parseability of tool calls
2. **Validity Reward (r_valid):** Available tools, gold-calls, value grounding
3. **Curriculum Reward (r_curr):** Difficulty & semantic alignment

## Results
- 92.5% relative improvement over base model
- Surpasses fully supervised tool-calling baselines without any training data

## Relevance to Hermes/Atropos
- Self-play loop directly applicable to Hermes agent RL training environments
- Curriculum reward design maps to Hermes distillation tip confidence scoring
- Zero-data assumption means we can train tool-calling without manual annotation
- Generator-Solver co-evolution could replace manual task specification in Atropos envs


## Sources

- https://arxiv.org/html/2602.21320v1
