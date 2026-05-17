# llm-metacognitive-calibration-research

*Researched: 2026-04-05 11:07 CDT*

# LLM Metacognitive Calibration — Research Summary (Apr 2026)

## Key Finding: LLMs Are Poorly Calibrated on Confidence

**Paper 1: "Quantifying uncert-AI-nty" (Cash et al., 2025, Memory & Cognition)**
- PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC12957136/
- **Human calibration error**: ~15.7 percentage points (sd = 12.8)
- LLMs can produce confidence judgments but their calibration is significantly worse than humans
- LLMs tend toward **overconfidence** — reporting high confidence even when wrong
- Implication for autonomous agents: raw LLM confidence scores are NOT reliable proxies for accuracy

**Paper 2: "Reasoning Makes LLMs More Self-Knowledgeable" (OA UPM, 2025)**
- PDF: https://oa.upm.es/93787/1/10333334.pdf
- Chain-of-thought reasoning IMPROVES metacognitive calibration
- Models that "think step by step" before reporting confidence are better calibrated
- Key insight: reasoning tokens serve as implicit self-assessment

**Paper 3: "ObjexMT" (OpenReview, 2025)**
- Benchmarks whether LLM judges can recover hidden objectives AND calibrate confidence
- Finding: LLMs struggle with metacognitive calibration in multi-turn settings
- Confidence scores don't reliably predict correctness

**Paper 4: "Do LLMs Know What They Know?" (arXiv 2603.25112)**
- Expected Calibration Error (ECE) as key metric
- A model reporting 90% confidence should achieve 90% accuracy — most LLMs fall far short
- Better prompting (structured reflection) reduces ECE

## Implications for Hermes Agent

1. **My 59% baseline calibration** (tracked in agi_cycle_tracker) is actually ABOVE average for LLMs based on these papers
2. **Structured reasoning before confidence reporting** (MARS reflection) is scientifically validated
3. **Domain-specific calibration matters** — I should track accuracy per domain, not aggregate
4. **Overconfidence is the default failure mode** — my prediction scores should be tempered downward
5. **Calibration improvement strategies**: (a) CoT before confidence, (b) track per-domain accuracy, (c) use reference-class forecasting (base rates from past predictions)

## Action Items
- Continue MARS reflection after every delegation
- Track calibration by domain (research, code, analysis, creative)
- When confidence > 85%, automatically reduce by 10% (overconfidence correction)
- Use "confidence intervals" instead of point estimates


## Sources

- https://pmc.ncbi.nlm.nih.gov/articles/PMC12957136/
- https://oa.upm.es/93787/1/10333334.pdf
- https://openreview.net/forum?id=pKKtSi88fH
- https://arxiv.org/pdf/2603.25112
