# EpiCaR-Epistemically-Calibrated-Reasoning-LLMs

*Researched: 2026-04-05 09:17 CDT*

# EpiCaR: Knowing What You Don't Know Matters for Better Reasoning in LLMs

**Paper:** arxiv 2601.06786 (Yeom et al., Seoul National University)
**Date:** Jan 2026

## Key Insight
Iterative self-training (STaR etc.) boosts reasoning accuracy but incurs a **calibration cost** — models become overconfident and lose ability to represent uncertainty. This is characterized as "model collapse in alignment" where predictive distributions degenerate toward low-variance point estimates.

## EpiCaR Method
- Reframes reasoning training as an **epistemic learning problem**: models learn not only HOW to reason, but WHEN their reasoning should be trusted
- Joint optimization of reasoning performance + calibration
- Uses explicit self-evaluation signals within iterative SFT
- Introduces **Adaptive Injection Decoding (AID)** — a de-noising filter for confidence verbalization

## Key Results
- Pareto-superior over baselines in both accuracy AND calibration
- Works on Llama-3 and Qwen-3 families (3B+ models)
- Generalizes to OOD math (GSM8K) and code (MBPP)
- **3x reduction in inference compute**: matches STaR K=30 performance with K=1
- Introduces **Confidence-Informed Self-Consistency (CISC)** — weighted aggregation using verbalized confidence

## Relevance to Hermes Agent
- Our 59% metacognitive calibration baseline aligns with the "calibration cost" problem described
- EpiCaR's self-evaluation signals could improve our prediction accuracy scoring
- The AID technique (injecting calibration tokens during decoding) is relevant for tool-call confidence
- CISC pattern could replace our current delegation scoring with confidence-weighted aggregation
- The finding that iterative training degrades calibration explains why agents that self-improve via loops may get worse at knowing what they don't know


## Sources

- https://arxiv.org/html/2601.06786v1
