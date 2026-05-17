# rl-training-tool-r0-self-play-zero-data

*Researched: 2026-04-10 21:35 CDT*

# Tool-R0: Self-Evolving LLM Agents for Tool-Learning from Zero Data

**Paper:** arXiv 2602.21320v1
**Authors:** Emre Can Acikgoz, Cheng Qian, Jonas Hübotter, Heng Ji, Dilek Hakkani-Tür, Gokhan Tur (UIUC / ETH Zurich)

## Key Innovation
Self-play RL framework for training tool-calling agents with **zero human data**:
- **Generator** proposes targeted challenging tasks at the Solver's competence frontier
- **Solver** learns to solve them with real-world tool calls
- Both initialized from the same base LLM and co-evolve with complementary rewards

## Reward Design (3-component)
1. **Format Reward** (r_fmt): Tags and parseability
2. **Validity Reward** (r_valid): Available tools, gold-calls, value grounding
3. **Curriculum Reward** (r_curr): Difficulty & semantic alignment (for generator)

## Results
- 92.5% relative improvement over base model
- Surpasses fully supervised tool-calling baselines under same setting
- Works across different tool-use benchmarks

## Relevance to Hermes/Atropos
- Directly applicable to Hermes Atropos environments for tool-calling training
- Self-play approach eliminates the data curation bottleneck
- Curriculum reward design could inform Hermes environment reward shaping
- The Generator-Solver co-evolution pattern mirrors potential Hermes self-improvement loops

## Key Insight
Self-play creates a self-evolving cycle that scales without human data — critical for superintelligent agent development. The generator produces tasks at the frontier of solver capability, creating an automatic curriculum.


## Sources

- https://arxiv.org/html/2602.21320v1
