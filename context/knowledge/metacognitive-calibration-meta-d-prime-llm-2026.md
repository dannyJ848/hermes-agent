# metacognitive-calibration-meta-d-prime-LLM-2026

*Researched: 2026-04-05 10:07 CDT*

# Measuring the Metacognition of AI (arXiv:2603.29693, Mar 2026)

**Authors:** Servajean & Servajean (RIKEN / Paul-Valéry University)

## Key Contribution
Proposes the **meta-d' framework** (from psychophysics) as the gold standard for measuring LLM metacognitive sensitivity — the ability to generate confidence ratings that distinguish correct from incorrect responses.

## Core Methods
1. **Meta-d' framework**: Adapted from human metacognition research. Measures metacognitive *sensitivity* (can the model tell when it's right vs wrong?) separately from metacognitive *efficiency* (how close to optimal is this ability?).
2. **Signal Detection Theory (SDT)**: Applied to measure whether LLMs spontaneously regulate decisions based on uncertainty and risk — e.g., becoming more conservative when stakes are high.
3. **Model-free alternatives** also proposed for simpler deployment.

## Experiments
- Tested on GPT-5, DeepSeek-V3.2-Exp, Mistral-Medium-2508
- **Experiment 1**: Primary judgment → confidence rating (classic metacognition paradigm)
- **Experiment 2**: Primary judgment only, with manipulated risk levels

## Three Comparison Axes
1. Compare an LLM to optimality (meta-d' vs d')
2. Compare different LLMs on the same task
3. Compare the same LLM across different tasks

## Relevance to Hermes Agent
This directly validates Evey's metacognitive calibration tracking (59% baseline from cycle tracker). The meta-d' framework could be adapted to score Evey's prediction confidence vs actual accuracy per domain. Instead of simple "was I right?" binary scoring, meta-d' would measure whether Evey's confidence ratings (high/medium/low) actually discriminate between correct and incorrect predictions — a much richer signal.

## Implication for SOMA
If LLMs can be shown to have metacognitive sensitivity (confidence tracks accuracy), this supports building calibration-aware UI — e.g., showing confidence levels to medical students using SOMA, or having the system self-regulate detail level based on uncertainty.


## Sources

- https://arxiv.org/html/2603.29693v1
