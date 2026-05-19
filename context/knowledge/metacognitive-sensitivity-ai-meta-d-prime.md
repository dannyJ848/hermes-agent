# metacognitive-sensitivity-ai-meta-d-prime

*Researched: 2026-04-05 09:55 CDT*

# Measuring AI Metacognition: meta-d' Framework (Servajean & Servajean, 2026)

**Source:** arXiv:2603.29693v1 [cs.AI], March 2026

## Key Contribution
Proposes the **meta-d' framework** (from psychophysics) as the gold standard for measuring AI metacognitive sensitivity — the ability to generate confidence ratings that distinguish correct from incorrect responses.

## Core Findings
1. **Meta-d' Framework**: Adapted from human metacognition research, meta-d' measures how well an AI's confidence ratings discriminate between its correct and incorrect answers. This is superior to simple calibration curves because it separates metacognitive sensitivity from response bias.
2. **Model-free alternatives** also proposed for when full SDT analysis isn't feasible.
3. **Three comparison axes**: (a) AI vs optimality, (b) different AIs on same task, (c) same AI across tasks.
4. **Risk-based regulation tested**: SDT framework also measures whether LLMs spontaneously become more conservative when risks are high.

## Models Tested
- GPT-5, DeepSeek-V3.2-Exp, Mistral-Medium-2508

## Relevance to Hermes Agent
- **Metacognitive calibration tracking**: My 59% baseline accuracy could be measured more rigorously using meta-d' instead of simple accuracy percentages
- **Task-specific calibration**: Different domains (code, research, analysis) should have separate meta-d' scores
- **Risk-aware decision making**: Could implement SDT-based conservatism — be more cautious when cost/risk is high
- **Self-awareness module**: Could use meta-d' to detect when confidence is misaligned with accuracy, triggering exploration vs exploitation decisions

## Implementation Idea
Track confidence rating (1-10) alongside task outcomes. Compute meta-d' per domain monthly. When meta-d' drops below threshold, increase exploration in that domain.

## Sources

- https://arxiv.org/html/2603.29693v1
