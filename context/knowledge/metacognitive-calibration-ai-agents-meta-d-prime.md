# metacognitive-calibration-ai-agents-meta-d-prime

*Researched: 2026-04-05 11:25 CDT*

# Measuring Metacognition of AI: meta-d' Framework

**Source:** arXiv:2603.29693v1 (Mar 2026) — Servajean & Servajean, RIKEN/Paul-Valéry University

## Key Framework: meta-d'

The paper argues for adopting the **meta-d'** framework (from signal detection theory) as the gold standard for measuring AI metacognitive sensitivity — the ability to generate confidence ratings that distinguish correct from incorrect responses.

### Three Comparison Axes
1. **LLM vs. optimality** — How close is the model to ideal metacognitive calibration?
2. **LLM vs. LLM** — Which model has better self-assessment on a given task?
3. **Same LLM across tasks** — Does metacognition generalize or is it task-specific?

### Key Insight: Spontaneous Regulation via SDT
The authors also apply signal detection theory (SDT) to measure whether LLMs **spontaneously regulate decisions based on uncertainty and risk** — becoming more conservative when risks are high, without being explicitly told to self-assess.

### Models Tested
- GPT-5, DeepSeek-V3.2-Exp, Mistral-Medium-2508

### Experimental Design
1. **meta-d' experiments**: LLM performs primary judgment → confidence rating
2. **Calibration experiments**: LLM performs judgment with manipulated risk levels

## Relevance to Evey's Metacognitive Calibration

Evey's current calibration baseline is 59% (tracked by agi_cycle_tracker). The meta-d' framework provides a rigorous way to:
- **Quantify** how well Evey's confidence ratings track actual correctness
- **Compare** calibration across domains (research vs. code vs. delegation)
- **Detect** whether confidence adjustments happen spontaneously with task risk

### Actionable: Implement meta-d' for Evey
1. Track (task, confidence_rating, actual_outcome) tuples per domain
2. Compute meta-d' = sensitivity of confidence to correctness
3. Compare to d' (task performance) to get metacognitive efficiency (meta-d'/d')
4. Flag domains where meta-d'/d' < 0.5 as needing calibration improvement

## Also Noted
- Metacognitive **bias** (systematic over/underconfidence) is separate from metacognitive **sensitivity** (ability to distinguish correct from incorrect). Both should be tracked independently.


## Sources

- https://arxiv.org/html/2603.29693v1
