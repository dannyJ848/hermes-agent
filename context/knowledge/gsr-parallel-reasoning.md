# gsr-parallel-reasoning

*Researched: 2026-04-14 20:16 CDT*

# Generative Self-Refinement (GSR) — Parallel Test-Time Reasoning

**Source:** Wang et al. (Microsoft Research), OpenReview
**Date Retrieved:** 2026-04-14

## Key Innovation
GSR trains a single model to generate N candidate solutions in parallel, then synthesizes a superior solution by critiquing and merging those candidates. Unlike Best-of-N or majority voting, it can produce correct answers even when ALL candidates are wrong.

## Critical Findings
1. **Refinement is a distinct skill** — larger models (32B+) naturally self-refine; smaller models need explicit training
2. **Hybrid training beats pure distillation**: 45.6% vs 37.5% on AIME24
3. **Cross-model refinement**: GSR-7B improved DeepSeek-R1-Distill from 66.7% → 74.6%
4. **Context rot** with 32+ candidates; generalizes from 4 to 10 at test-time

## Relevance to Hermes
- Mirrors reflect_on_output / validate_output patterns
- Could improve delegation via multi-approach synthesis
- "Refinement as distinct skill" insight → train specific refinement behavior

## Sources

- https://openreview.net/forum?id=nbhDNDDZMe
- https://magazine.sebastianraschka.com/p/state-of-llms-2025
