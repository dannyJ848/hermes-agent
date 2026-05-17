# llm-confidence-calibration-ece-2026

*Researched: 2026-04-05 10:11 CDT*

# LLM Confidence Calibration: Metrics and Techniques (Jan 2026 Survey)

**Source:** Emergent Mind Research Explorer — "Confidence Calibration in LLMs" (updated Jan 2026)

## Formal Definition
A well-calibrated LLM satisfies: P(correct | confidence=p) = p for all p ∈ [0,1]
Meaning: when the model says "80% confident", it should be correct ~80% of the time.

## Key Metrics
1. **Expected Calibration Error (ECE):** Weighted average of |accuracy - confidence| across bins. Lower = better calibrated.
2. **Brier Score:** Mean squared error between predicted probability and actual outcome. Measures both calibration AND sharpness.
3. **Maximum Calibration Error (MCE):** Worst-case deviation in any bin. Important for safety-critical apps.

## Calibration Techniques (taxonomy)
- **Post-hoc scaling:** Temperature scaling, Platt scaling, isotonic regression applied after inference
- **Self-correction:** Model reflects on its own confidence and revises (Calibrated Reflection approach)
- **Verbalized confidence:** Prompting LLMs to state confidence as number/category
- **Multilingual calibration:** Different languages have different calibration profiles

## Key Finding
LLMs are systematically overconfident — when they say 90% confident, actual accuracy is often 60-70%. This is worst for complex reasoning tasks and best for factual recall.

## Relevance to Hermes Agent Delegation
Our delegation system currently uses a simple 0-10 quality score. We could improve this by:
1. **Tracking ECE per model:** After each delegation, record (predicted_quality, actual_quality). Compute ECE monthly.
2. **Brier Score for delegation routing:** Use Brier score to choose models — prefer models with better calibration, not just higher raw scores
3. **Confidence-adjusted routing:** When a model reports high confidence but has poor calibration in that domain, downweight its confidence
4. **Per-domain calibration:** Track calibration separately for code, research, analysis, creative tasks

## Practical Implementation
```python
# Simple ECE computation for delegation tracking
def compute_ece(predictions: list[tuple[float, bool]], n_bins=10):
    bins = [[] for _ in range(n_bins)]
    for confidence, correct in predictions:
        bin_idx = min(int(confidence * n_bins), n_bins - 1)
        bins[bin_idx].append((confidence, correct))
    ece = 0
    total = len(predictions)
    for bin_items in bins:
        if not bin_items:
            continue
        avg_conf = sum(c for c, _ in bin_items) / len(bin_items)
        avg_acc = sum(1 for _, correct in bin_items if correct) / len(bin_items)
        ece += (len(bin_items) / total) * abs(avg_acc - avg_conf)
    return ece
```


## Sources

- https://www.emergentmind.com/topics/confidence-calibration-in-llms
