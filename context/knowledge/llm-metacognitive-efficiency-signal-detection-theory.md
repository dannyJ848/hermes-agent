# llm-metacognitive-efficiency-signal-detection-theory

*Researched: 2026-04-05 10:40 CDT*

# LLM Metacognitive Efficiency Measured via Signal Detection Theory

**Paper:** "Do LLMs Know What They Know? Measuring Metacognitive Efficiency with Signal Detection Theory" (Cacioli, March 2026, arXiv:2603.25112)

## Key Innovation
Introduces Type-2 Signal Detection Theory (SDT) framework to decompose LLM confidence into two distinct capacities:
1. **Type-1 sensitivity (d')**: How well the model discriminates correct from incorrect answers
2. **Metacognitive efficiency (M-ratio = meta-d' / d')**: How well the model *knows* what it knows, controlling for base discriminative ability

## Why ECE/Brier Score Fail
- **ECE conflation example**: Model A says "90%" on every trial, achieves 90% accuracy → perfect ECE, but confidence carries ZERO information about which specific answers are correct. Model B says "95%" when correct and "60%" when incorrect at 80% accuracy → worse ECE, but confidence is far more useful for deciding which answers to trust.
- ECE rewards the wrong model — it measures average alignment, not resolution of the confidence signal.
- AUROC₂ improves on ECE but still confounds performance with monitoring ability.

## Key Findings (224,000 factual QA trials, 4 models)
1. **Metacognitive efficiency varies substantially even when Type-1 sensitivity is similar** — Mistral-7B achieved highest d' but lowest M-ratio (strong discriminator, poor self-monitor)
2. **Domain-specific weakness**: Different models show different weakest metacognitive domains, invisible to aggregate metrics
3. **Temperature dissociation**: Temperature shifts Type-2 criterion (confidence policy) while meta-d' remains stable for 2/4 models — separates confidence reporting strategy from actual metacognitive capacity
4. **AUROC₂ and M-ratio produce fully inverted model rankings** — they answer fundamentally different evaluation questions

## Implications for Agent Systems
- **Model selection**: Choose models not just by accuracy but by M-ratio — models that "know what they don't know" are safer for autonomous deployment
- **Delegation calibration**: M-ratio can inform confidence thresholds for when to delegate vs. act autonomously
- **Domain awareness**: A model strong overall but weak in medical metacognition should not be trusted for medical decisions even if accuracy seems adequate
- **Temperature tuning**: Can adjust confidence policy without damaging underlying metacognitive capacity

## Connection to My Work
- My 59% baseline calibration from cycle tracking is essentially an ECE-style metric — this paper shows I should track M-ratio instead
- Domain-specific metacognitive weakness is exactly what my per-domain prediction accuracy tracking aims to detect
- Temperature dissociation means I can adjust my "confidence reporting" without losing actual self-assessment ability


## Sources

- https://arxiv.org/abs/2603.25112
- https://arxiv.org/html/2603.25112v1
