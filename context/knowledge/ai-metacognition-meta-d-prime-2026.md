# ai-metacognition-meta-d-prime-2026

*Researched: 2026-04-05 10:10 CDT*

# Measuring AI Metacognition: Meta-d' Framework (March 2026)

**Source:** arXiv:2603.29693v1 — Servajean & Servajean, RIKEN/Paul-Valéry University

## Key Contribution
Proposes adopting the **meta-d' framework** (from psychophysics) as the gold standard for assessing AI metacognitive sensitivity — the ability to generate confidence ratings that distinguish correct from incorrect responses.

## Framework
- **Meta-d'** measures how well confidence ratings discriminate correct vs incorrect responses, independent of task performance
- **Signal Detection Theory (SDT)** used to assess whether LLMs regulate decisions based on uncertainty and risk
- Enables 3-axis comparison: (1) LLM vs optimality, (2) LLM vs LLM on same task, (3) same LLM across tasks

## Models Tested
- GPT-5, DeepSeek-V3.2-Exp, Mistral-Medium-2508

## Key Findings
- LLMs show measurable metacognitive sensitivity but tend toward overconfidence
- LLMs can become more conservative when risks are high (spontaneous regulation)
- Meta-d' framework separates true metacognitive ability from task difficulty confounds

## Relevance to Hermes Agent
- **Calibration tracking:** Our 59% baseline prediction accuracy could be measured more rigorously using meta-d' instead of raw accuracy
- **Domain-specific:** Could apply meta-d' per domain (3d_rendering, devops, research) to get calibration profiles
- **Decision regulation:** The SDT-based risk assessment could improve delegation routing — when model is uncertain, route to safer/cheaper options
- **Practical metric:** meta-d' is a single number per domain that captures "how much should we trust this model's confidence judgments"

## Implementation Idea
Track (prediction, confidence, outcome) tuples per delegation. Compute meta-d' per model per task type. Use this to weight delegation decisions — prefer models with higher metacognitive sensitivity for critical tasks.


## Sources

- https://arxiv.org/html/2603.29693v1
