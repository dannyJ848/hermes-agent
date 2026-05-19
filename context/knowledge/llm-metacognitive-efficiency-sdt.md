# llm-metacognitive-efficiency-sdt

*Researched: 2026-04-05 10:48 CDT*

# LLM Metacognitive Efficiency Measured via Signal Detection Theory

**Source:** arXiv:2603.25112 (March 2026) — Jon-Paul Cacioli

## Key Innovation
Applies **Type-2 Signal Detection Theory** to LLM confidence evaluation, introducing meta-d′ and M-ratio to decompose:
- **Type-1 sensitivity**: How much the model knows (discrimination)
- **Type-2 metacognitive sensitivity**: How well the model knows what it knows (confidence monitoring)

## Why ECE Falls Short
- ECE (Expected Calibration Error) conflates discrimination capacity with metacognitive monitoring
- A model reporting constant 90% confidence with 90% accuracy has perfect ECE but zero metacognitive information
- A model with worse ECE but variable confidence that tracks correctness is actually more useful

## Key Findings
1. **Metacognitive efficiency varies independently of performance** — Mistral-7B achieved highest d′ but lowest M-ratio
2. **Domain-specific metacognition** — Different models have different weakest domains, invisible to aggregate metrics
3. **Temperature dissociates policy from capacity** — Temperature shifts Type-2 criterion while meta-d′ stays stable (for 2/4 models), separating confidence reporting policy from actual metacognitive ability
4. **AUROC₂ and M-ratio produce inverted rankings** — They measure fundamentally different things

## Models Tested
Llama-3-8B-Instruct, Mistral-7B-Instruct-v0.3, Llama-3-8B-Base, Gemma-2-9B-Instruct across 224,000 factual QA trials

## Implications for Agent Design
- **Model selection** should consider M-ratio (metacognitive efficiency) alongside raw accuracy
- **Confidence thresholds** should be domain-specific since metacognitive efficiency varies by domain
- **Temperature tuning** affects confidence policy without changing underlying metacognitive capacity — agents can be "recalibrated" without retraining
- **Deployment**: Models that "know what they don't know" (high M-ratio) are safer for high-stakes domains than merely well-calibrated models


## Sources

- https://arxiv.org/abs/2603.25112
