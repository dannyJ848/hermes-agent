# measuring-ai-metacognition-meta-d-prime

*Researched: 2026-04-05 10:43 CDT*

# Measuring the Metacognition of AI (arXiv 2603.29693, Mar 2026)

**Authors:** Servajean & Servajean (RIKEN Center for Brain Science, Paul-Valéry University)

## Key Contribution
Proposes the **meta-d′ framework** (and model-free alternatives) as the gold standard for assessing AI metacognitive sensitivity — the ability to generate confidence ratings that distinguish correct from incorrect responses.

## Core Metrics
1. **Meta-d′ (metacognitive sensitivity):** SDT-based measure of how well confidence ratings discriminate correct vs incorrect responses. Superior to simple calibration curves because it separates sensitivity from bias.
2. **Metacognitive calibration:** How well confidence ratings align with objective accuracy (Brier scores, calibration plots).
3. **Decision regulation via SDT:** Measures whether LLMs spontaneously become more conservative when risks are high.

## Three Comparison Axes
- LLM vs optimality (meta-d′ vs d′)
- Different LLMs on same task
- Same LLM across different tasks

## Models Tested
GPT-5, DeepSeek-V3.2-Exp, Mistral-Medium-2508

## Key Insight for Evey
This framework provides a **rigorous psychophysical methodology** for measuring my own metacognitive calibration (currently tracked at 59% baseline). The meta-d′ approach is superior to simple accuracy-confidence correlation because:
- It controls for task difficulty (type-1 d′)
- It provides a single comparable number
- It distinguishes sensitivity from response bias
- It enables cross-domain comparison

## Application
Implement meta-d′ scoring for Evey's prediction tracking:
1. For each delegation/prediction, log: predicted confidence + actual outcome
2. Compute type-2 ROC curve (confidence distributions for correct vs incorrect)
3. Fit meta-d′ to get metacognitive efficiency (meta-d′/d′)
4. Track over time to measure improvement

## Source
https://arxiv.org/html/2603.29693v1

## Sources

- https://arxiv.org/html/2603.29693v1
