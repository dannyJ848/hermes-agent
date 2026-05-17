# rl-training-long-horizon-agents

*Researched: 2026-04-10 00:59 CDT*

# RL Training for Long-Horizon Tool-Using Agents (Agent-STAR)

**Source:** arXiv:2603.21972 (March 2026) — Wu et al., CUHK / IDEA Research

## Key Findings (7 Takeaways from Systematic Study)

1. **Reward & algorithm choices are scale-dependent**: Smaller models benefit from staged rewards and enhanced exploration. Larger models converge efficiently with simpler dense rewards.
2. **~1K training samples with balanced difficulty mixture** is the sweet spot for both in-domain and out-of-domain performance.
3. **Environmental stability is critical** to prevent policy degradation — flaky tool responses poison RL training.
4. **STAR Pipeline**: Decomposes agentic RL design along 5 axes: reward shaping, model scaling, data composition, algorithm selection, environmental stability.
5. **RL-trained models achieve SOTA on TravelPlanner**, significantly outperforming leading LLMs (GPT-4, Claude, etc.).
6. **GRPO works well for larger models** with dense rewards; smaller models need staged/curriculum reward shaping.
7. **Data composition matters**: balanced difficulty mixture (easy/medium/hard) prevents overfitting to trivial cases.

## Relevance to Hermes Agent
- **Atropos environments** should follow the STAR pipeline for reward design
- **1K samples** is achievable — focus on quality, balanced difficulty
- **Environmental stability** is critical — mock tools must be deterministic during training
- **Scale-dependent strategy**: for smaller models (7B-14B), use staged rewards; for larger (70B+), dense rewards suffice


## Sources

- https://arxiv.org/html/2603.21972v1
- https://github.com/WxxShirley/Agent-STAR
