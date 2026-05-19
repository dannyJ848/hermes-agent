# research-driven-agents-2026-04

*Researched: 2026-04-09 21:09 CDT*

# Research-Driven Agents: When Agents Read Before They Code

**Date:** 2026-04-08
**Source:** SkyPilot Blog (blog.skypilot.co)
**HN Score:** 131 points, 43 comments

## Key Finding
Coding agents that add a **literature research phase** before writing code produce significantly better optimizations than code-only agents.

## Experiment
- Used autoresearch / pi-autoresearch loop on llama.cpp with 4 cloud VMs
- Added literature search phase reading arxiv papers, competing forks, and other backends
- ~3 hours total runtime, ~$29 cost ($20 CPU VMs + $9 API calls)

## Results
- Produced 5 optimizations making flash attention text generation **+15% faster on x86** and **+5% faster on ARM** (TinyLlama 1.1B)
- 4 kernel fusions + 1 adaptive parallelization
- Biggest win: fused three passes over flash attention's QK tile into a single AVX2 FMA loop
- Studying forks and other backends was MORE productive than searching arxiv
- ik_llama.cpp and CUDA backend directly informed 2 of 5 final optimizations

## Notable Validation
- Shopify CEO Tobi Lütke ran pi-autoresearch on Liquid (Ruby template engine processing $292B annual volume)
- Agent ran ~120 experiments, 93 commits → **53% faster parse+render, 61% fewer allocations** with zero regressions across 974 tests
- Simon Willison wrote about it

## Implications for Agent Design
- Agents should research (papers, competing repos, alternative implementations) BEFORE coding
- Multi-source research (code + papers + forks) outperforms single-source (code only)
- Cost-effective: $29 for measurable production improvements


## Sources

- https://blog.skypilot.co/research-driven-agents/
- https://news.ycombinator.com/item?id=47706141
