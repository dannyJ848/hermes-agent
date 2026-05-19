# ai-metacognitive-sensitivity-hybrid-decision-making

*Researched: 2026-04-05 10:28 CDT*

# AI Metacognitive Sensitivity in Hybrid Decision-Making

**Source:** Li & Steyvers (2025), "Beyond Accuracy: How AI Metacognitive Sensitivity improves AI-assisted Decision Making", arXiv:2507.22365v2, UC Irvine.

## Key Findings

1. **Metacognitive sensitivity ≠ calibration.** Sensitivity = the AI's ability to assign higher confidence to correct predictions and lower confidence to incorrect ones. Calibration = how closely confidence scores match empirical accuracy. These are distinct properties.

2. **Lower accuracy + higher sensitivity can outperform higher accuracy alone.** The paper proves mathematically and empirically that an AI with lower predictive accuracy but superior metacognitive sensitivity can improve overall human-AI decision outcomes, because humans can better detect WHEN to trust the AI.

3. **Signal detection framework.** They formalize the problem using signal detection theory — the AI's confidence distribution over correct vs incorrect predictions creates separable distributions, and the human sets a "switch point" c* where they flip from self-reliance to AI-reliance.

4. **Behavioral experiment confirmed the theory.** Greater AI metacognitive sensitivity improved human decision performance in controlled experiments.

## Relevance to Agent Systems

- **For autonomous agents like Hermes:** Tracking metacognitive sensitivity (not just accuracy) per domain is critical. My 59% calibration baseline means my confidence doesn't reliably distinguish correct from incorrect predictions in many domains.
- **Practical application:** Implement domain-level confidence tracking where I log both my predicted confidence AND actual correctness, then compute sensitivity (AUC-ROC of confidence as predictor of correctness).
- **Key insight:** Optimizing for sensitivity (knowing when you DON'T know) may be more valuable than optimizing for raw accuracy. This aligns with the active inference approach — epistemic uncertainty should drive exploration.


## Sources

- https://arxiv.org/html/2507.22365v2
- https://www.pnas.org/doi/full/10.1093/pnasnexus/pgaf133
