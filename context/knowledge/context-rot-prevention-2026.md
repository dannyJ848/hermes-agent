# context-rot-prevention-2026

*Researched: 2026-04-05 12:06 CDT*

# Context Rot Prevention (Apr 2026)

## The Problem
All 18 frontier models tested by Chroma degrade continuously as context grows. Not a cliff -- a slope. Critical threshold at 40-60% of context window. For coding agents: 30%+ accuracy drop, 60% time spent just retrieving context.

## What We Observed
Our own agent's syntax degraded visibly at ~50-60% context fill. Corrupted Python blocks, mismatched braces, repeated patterns. The degradation is REAL and measurable in production.

## The Fix (3 layers)
1. **Compression threshold: 40%** (was 70%) -- fires BEFORE degradation starts
2. **Target ratio: 0.25** (was 0.3) -- compresses more aggressively
3. **Short cron sessions** -- max 5 tool calls per cycle. Fresh context = fresh reasoning

## Key Insight
The fix is NOT better compression. It is SHORTER SESSIONS. Each cron cycle should be 3-5 focused tool calls. Never accumulate noise across a long session.

## Config Changes
- threshold: 0.70 -> 0.40
- target_ratio: 0.30 -> 0.25
- protect_last_n: 40 -> 20
- Cron prompt: max 5 tool calls, self-terminate on degradation

## Sources
- Chroma context rot study (2026)
- arXiv 2601.15300: Intelligence Degradation in Long-Context LLMs
- Morph context rot guide


## Sources

- https://morphllm.com/context-rot
- https://arxiv.org/html/2601.15300v1
