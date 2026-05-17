# darwin-godel-machine-2025

*Researched: 2026-04-05 18:12 CDT*

# Darwin Gödel Machine (DGM) — arXiv:2505.22954

**Authors**: Jenny Zhang, Shengran Hu, Cong Lu, Robert Lange, Jeff Clune (May 2025, revised Mar 2026)

## Core Concept
A self-improving system that iteratively modifies its own code and empirically validates each change using coding benchmarks. Combines Darwinian evolution with Gödel Machine self-reference.

## Architecture

### 1. Agent Archive
Maintains a growing tree/archive of generated coding agents. Each node is a complete agent implementation. The archive forms a tree because each new agent is derived from a parent.

### 2. Foundation Model as Mutator
A foundation model (LLM) samples an agent from the archive and creates a "new, interesting version" by modifying its code. This includes:
- Better code editing tools
- Long-context window management
- Peer-review mechanisms

### 3. Empirical Validation
Every code change is tested against coding benchmarks (SWE-bench, Polyglot). Only changes that improve benchmark scores are kept.

### 4. Open-Ended Exploration
The archive grows through parallel exploration of many different paths. Not greedy — allows exploring "interesting" directions even if not immediately optimal.

## Results
- SWE-bench: 20.0% → 50.0% (fully autonomous improvement)
- Polyglot: 14.2% → 30.7%
- Significantly outperforms baselines without self-improvement or open-ended exploration

## Key Insight: Bootstrapping
The system improves its ability to improve itself. Better code editing tools → better ability to write better code editing tools → recursive improvement spiral.

## Safety
Experiments done with sandboxing and human oversight.

## Relevance to Evey
- Our meta_self_modifier.py is a primitive version of this
- **GAP**: No agent archive — we only have one "current" version, no tree of variants
- **GAP**: No empirical validation of code changes — we don't benchmark our modifications
- **ENHANCEMENT**: Could maintain a git branch per "agent version" and benchmark each
- **ENHANCEMENT**: The "interestingness" heuristic for mutation direction could enhance our distillation
- **CRITICAL**: The bootstrapping insight applies — improving tool use tools should be a priority


## Sources

- https://arxiv.org/abs/2505.22954
