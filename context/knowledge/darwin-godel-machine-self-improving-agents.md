# darwin-godel-machine-self-improving-agents

*Researched: 2026-04-07 12:14 CDT*

# Darwin Gödel Machine: Self-Improving Agents (ICLR 2026)

Source: arXiv:2505.22954 (Jenny Zhang, Shengran Hu, Cong Lu, Robert Lange, Jeff Clune)
Accepted at ICLR 2026

## Core Idea
The Darwin Gödel Machine (DGM) iteratively modifies its own code and empirically validates each change using benchmarks. Inspired by Darwinian evolution + open-endedness research.

## Problem It Solves
- Today's AI has human-designed, fixed architectures
- Gödel machine proposed self-improvement with provably beneficial changes — but proving benefit is impossible in practice
- DGM relaxes this: uses empirical validation instead of proofs

## Key Mechanisms
1. **Self-modifying code** — agent changes its own codebase
2. **Iterative improvement** — each change validated on benchmarks
3. **Improving ability to improve** — meta-learning: gets better at modifying itself
4. **Darwinian evolution** — population of code variants, survival of fittest
5. **Open-ended search** — no fixed target, continuously explores

## Relevance to Hermes AGI
- Our self-improvement loop (subconscious, Dojo, skill patches) is a primitive DGM
- We empirically validate via delegation scoring, tool stats, tip confidence
- Upgrade path: formalize self-modification with benchmark validation
- Could implement: auto-patch skills based on failure patterns → validate via tool stats

## Authors
Jenny Zhang, Shengran Hu, Cong Lu, Robert Lange, Jeff Clune (Meta AI / UBC)


## Sources

- https://arxiv.org/abs/2505.22954
- https://iclr.cc/virtual/2026/poster/10007327
