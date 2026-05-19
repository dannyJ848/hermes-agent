# meta-d-prime-llm-metacognition-measurement

*Researched: 2026-04-05 10:19 CDT*

# Meta-d' Framework for Measuring LLM Metacognition (Servajean et al., 2026)

**Paper:** "Measuring the metacognition of AI" (arXiv:2603.29693, Mar 2026)
**Authors:** Servajean & Servajean (RIKEN / Paul-Valéry University)

## Key Framework: Meta-d'
The paper argues for adopting the **meta-d'** framework (from signal detection theory) as the gold standard for assessing AI metacognitive sensitivity — specifically, the ability to generate confidence ratings that distinguish correct from incorrect responses.

### Three Comparison Axes
1. **LLM vs. optimality** — How close is the model to ideal metacognitive calibration?
2. **LLM vs. LLM** — Which model has better metacognitive sensitivity on a given task?
3. **Same LLM across tasks** — Does metacognitive ability transfer or is it task-specific?

### Decision Regulation via SDT
Beyond confidence calibration, the paper applies SDT to measure whether LLMs **spontaneously regulate decisions** based on uncertainty and risk — becoming more conservative when risks are high.

### Models Tested
- GPT-5
- DeepSeek-V3.2-Exp
- Mistral-Medium-2508

### Experiment Design
1. **Confidence experiments:** LLM performs primary judgment → confidence rating. Meta-d' computed to assess calibration quality.
2. **Risk experiments:** LLM performs judgment without confidence, while risk is manipulated. SDT measures whether the model shifts decision criteria.

## Relevance to Hermes Agent
- Meta-d' provides a rigorous mathematical framework for measuring Evey's metacognitive calibration (currently tracked at ~59% baseline accuracy)
- Could replace subjective confidence scores with calibrated meta-d' values
- The SDT-based risk regulation paradigm could improve task selection — making the agent more conservative on high-risk operations
- Model-free alternatives to meta-d' exist for simpler implementation

## Implementation Idea
Track per-tool and per-domain confidence vs. accuracy. Compute meta-d' as the ratio of metacognitive sensitivity to type-1 sensitivity. Use this to identify domains where the agent is overconfident or underconfident.


## Sources

- https://arxiv.org/html/2603.29693v1
- https://journals.sagepub.com/doi/10.1177/09637214251391158
- https://academic.oup.com/pnasnexus/article/4/5/pgaf133/8118889
