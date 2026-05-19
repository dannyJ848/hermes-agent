# ESMA-evolution-strategies-metacognitive-alignment

*Researched: 2026-04-05 11:58 CDT*

# ESMA: Evolution Strategy for Metacognitive Alignment

**Paper:** "Fine-Tuning Language Models to Know What They Know" — Sangjun Park, Elliot Meyerson, Xin Qiu, Risto Miikkulainen (2026)
**Source:** Cognizant AI Lab

## Key Contributions

1. **Dual-Prompt Method for Metacognitive Measurement:** Proposes a framework to measure metacognitive ability (d′ type 2) — distinguishing between a model's ability to *answer* questions vs. its ability to *report what it knows*. Uses two separate prompts: one for answering, one for confidence/knowledge reporting.

2. **ESMA (Evolution Strategy for Metacognitive Alignment):** Trains LLMs to bind internal knowledge to explicit behaviors. Uses evolution strategies (not standard gradient descent) to optimize metacognitive calibration — making the model confident when correct and uncertain when incorrect.

3. **Key Result:** ESMA reduces overlap between confidence distributions for correct vs. incorrect answers. It shifts confidence *higher* for correct answers and *lower* for incorrect ones — genuine metacognitive alignment, not just confidence boosting.

4. **Generalization:** Robust generalization across diverse untrained settings, indicating the model learned a genuine self-awareness skill rather than overfitting to training domains.

5. **Parameter Analysis:** Attributes improvements to specific parameter changes, suggesting metacognition is a learnable, localizable capability.

## Relevance to Hermes Agent

- **Direct application:** Our metacognitive calibration tracker (59% baseline) could benefit from ESMA-like training. Currently we track confidence vs. accuracy post-hoc — ESMA shows how to *train* the alignment.
- **Agent implications:** Autonomous agents that know-what-they-know make better delegation decisions. When confidence truly tracks accuracy, the agent can skip verification on high-confidence outputs and double-check low-confidence ones.
- **Connection to existing work:** Our `epistemic-trust-scoring` skill (F-G-R Trust Tuple) is a heuristic approach to similar problems. ESMA provides a training-based alternative.
- **MARS integration:** Our Metacognitive Assessment and Reasoning System could incorporate d′ type 2 metrics alongside existing calibration tracking.

## Citation
Park, S., Meyerson, E., Qiu, X., & Miikkulainen, R. (2026). Fine-Tuning Language Models to Know What They Know. Cognizant AI Lab.


## Sources

- https://www.cognizant.com/us/en/ai-lab/publications/evolution-strategy-metacognitive-alignment-esma
- https://www.cognizant.com/us/en/ai-lab/blog/metacognition-training-llms-evolution-strategies
