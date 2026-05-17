# metacognitive-efficiency-llm-signal-detection

*Researched: 2026-04-05 09:26 CDT*

# Metacognitive Efficiency in LLMs: Signal Detection Theory Approach

**Paper:** "Do LLMs Know What They Know? Measuring Metacognitive Efficiency with Signal Detection Theory" (arXiv:2603.25112, March 2026, Jon-Paul Cacioli)

## Key Innovation
Decomposes LLM metacognition into two distinct capacities using Type-2 Signal Detection Theory:
- **Type-1 sensitivity (d')**: How much the model knows (factual accuracy)
- **Type-2 metacognitive sensitivity (meta-d')**: How well the model knows what it knows
- **M-ratio = meta-d'/d'**: Metacognitive efficiency — the ratio of metacognitive sensitivity to perceptual sensitivity

## Key Findings
1. **Metacognitive efficiency varies independently from factual knowledge.** Mistral-7B achieved highest d' but lowest M-ratio — it knows the most but is worst at knowing what it doesn't know.
2. **Domain-specific weakness invisible to aggregate metrics.** Different models show different weakest knowledge domains in metacognition.
3. **Temperature shifts confidence policy, NOT metacognitive capacity.** For 2/4 models, changing temperature shifted Type-2 criterion while meta-d' remained stable — dissociating confidence reporting from actual metacognitive ability.
4. **AUROC₂ and M-ratio produce inverted rankings.** Standard metacognitive metrics answer fundamentally different questions.

## Implications for Agent Design
- **Calibration ≠ Metacognition.** A model can appear well-calibrated (low ECE) through criterion placement without actually having good metacognitive sensitivity.
- **For autonomous agents**, M-ratio matters more than ECE — you need models that flag uncertainty on genuinely unknown items, not just models that sound appropriately confident.
- **Domain-specific calibration** is critical — an agent's reliability varies by knowledge domain, not just by model.
- **Temperature tuning** affects confidence reporting but NOT underlying metacognitive capacity — it's cosmetic, not structural.

## Relevance to Evey/SOMA
- Our metacognitive calibration tracker (59% baseline) should track M-ratio per domain, not just accuracy
- Delegation model selection should consider M-ratio: models with higher metacognitive efficiency will better self-report when they're uncertain
- Temperature adjustments for delegation confidence are not fixing the underlying problem — model selection is


## Sources

- https://arxiv.org/abs/2603.25112
