# LLM metacognitive efficiency meta-d-prime M-ratio framework 2026

*Researched: 2026-04-05 10:33 CDT*

# LLM Metacognitive Efficiency: meta-d' and M-ratio Framework

**Paper:** "Do LLMs Know What They Know? Measuring Metacognitive Efficiency with Signal Detection Theory" (arXiv:2603.25112, March 2026, Jon-Paul Cacioli)

## Key Innovation
Decomposes LLM confidence evaluation into two distinct capacities using Type-2 Signal Detection Theory:
- **Type-1 sensitivity (d')**: How much the model knows (accuracy)
- **Type-2 metacognitive sensitivity (meta-d')**: How well the model knows what it knows
- **M-ratio (meta-d'/d')**: Metacognitive efficiency — independent of task performance

## Why This Matters
Standard metrics (ECE, Brier score) **conflate** these two capacities. A model can appear well-calibrated simply by adjusting confidence thresholds (criterion placement), not because it actually has good metacognition.

## Key Findings (224K QA trials across 4 LLMs)
1. **Metacognitive efficiency varies independently of accuracy.** Mistral-7B had highest d' but lowest M-ratio — it performed well but didn't "know what it didn't know."
2. **Domain-specific metacognition.** Different models show different weakest domains, invisible to aggregate metrics.
3. **Temperature manipulation shifts Type-2 criterion** (confidence policy) while meta-d' stays stable for 2/4 models — dissociating confidence policy from actual metacognitive capacity.
4. **AUROC₂ and M-ratio produce fully inverted model rankings** — they answer fundamentally different questions.

## Implications for Agent Development
- For autonomous agents, M-ratio matters more than ECE — we need agents that know what they don't know.
- Domain-specific metacognitive profiles could drive task routing (delegate tasks where model has low M-ratio).
- Temperature tuning changes confidence reporting but NOT actual metacognitive ability — superficial fix.
- Pre-registered analysis with public code/data.

## Models Tested
- Llama-3-8B-Instruct
- Mistral-7B-Instruct-v0.3
- Llama-3-8B-Base
- Gemma-2-9B-Instruct


## Sources

- https://arxiv.org/abs/2603.25112
