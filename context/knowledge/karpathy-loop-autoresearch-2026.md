# karpathy-loop-autoresearch-2026

*Researched: 2026-04-11 23:37 CDT*

# The Karpathy Loop: Autonomous AI Research at Scale

**Source:** Fortune, March 17, 2026

## Summary
Andrej Karpathy built "autoresearch" — an autonomous AI coding agent that ran 700 experiments in 2 days to optimize small language model training. It discovered 20 optimizations yielding an 11% training speedup. Shopify CEO Tobias Lütke applied it to internal data: 37 experiments overnight, 19% performance gain.

## Key Insight: "The Final Boss Battle"
Karpathy called autonomous research "the final boss battle" for frontier AI labs. The pattern:
1. Spin up a swarm of agents
2. Have them collaborate to tune smaller models
3. Promote promising ideas to larger scales
4. Humans contribute "on the edges"

## Relevance to Hermes Agent
- **Validates our continuous execution loop**: Our 30-second cron cadence for autonomous research + coding is the same pattern at smaller scale
- **Swarm > single agent**: Multi-agent exploration of parameter space outperforms single-agent sequential search
- **Promote from small to large**: Test ideas cheaply, scale what works — our delegation + validate_output pipeline mirrors this

## Citation
Jeremy Kahn. "'The Karpathy Loop': 700 experiments, 2 days, and a glimpse of where AI is heading." Fortune, March 17, 2026.


## Sources

- https://fortune.com/2026/03/17/andrej-karpathy-loop-autonomous-ai-agents-future/
