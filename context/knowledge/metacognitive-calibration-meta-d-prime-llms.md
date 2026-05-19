# metacognitive-calibration-meta-d-prime-llms

*Researched: 2026-04-05 09:19 CDT*

# Measuring Metacognition of AI: meta-d′ Framework (arXiv 2603.29693, Mar 2026)

## Key Finding
Servajean & Servajean (RIKEN / Paul-Valéry University) propose **meta-d′** (from signal detection theory) as the gold standard for measuring AI metacognitive sensitivity — the ability to generate confidence ratings that distinguish correct from incorrect responses.

## Framework
- **meta-d′ / d′ ratio** = metacognitive efficiency. Compares observed metacognitive sensitivity to the theoretical optimum given task performance.
- Enables 3-axis comparison: (1) LLM vs optimality, (2) LLM vs LLM on same task, (3) same LLM across tasks.
- SDT also measures whether LLMs become more conservative when risks are high (decision regulation).

## Experiments
- Tested on GPT-5, DeepSeek-V3.2-Exp, Mistral-Medium-2508.
- Experiment 1: Primary judgment + confidence rating → meta-d′ calculation.
- Experiment 2: Primary judgment only, manipulating risk → SDT analysis of decision caution.

## Relevance to Evey
- Our metacognitive calibration tracker (59% baseline) could adopt meta-d′ as a more rigorous metric than simple accuracy/confidence correlation.
- Model-free alternatives exist if computing d′ is impractical.
- Risk-adjusted decision regulation maps directly to our delegation routing (high-risk tasks → conservative model selection).
- Paper argues against ad-hoc metacognition metrics in favor of psychophysical rigor.

## Source
- arXiv:2603.29693 (March 31, 2026)
- https://arxiv.org/html/2603.29693v1


## Sources

- https://arxiv.org/html/2603.29693v1
