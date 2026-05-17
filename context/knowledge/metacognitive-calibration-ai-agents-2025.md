# metacognitive-calibration-ai-agents-2025

*Researched: 2026-04-05 11:28 CDT*

# Metacognitive Calibration in AI Agents (2025 Research)

## Key Finding: Metacognitive Sensitivity as Trust Calibration Metric

**Source:** PNAS Nexus (2025) - "Metacognitive sensitivity: The key to calibrating trust and optimal reliance on AI systems"

The concept of **metacognitive sensitivity** in AI measures how well an AI system's confidence correlates with its actual correctness:
- **High metacognitive sensitivity**: AI is confident when right, uncertain when wrong
- **Low metacognitive sensitivity**: Confidence and accuracy are uncorrelated
- This is distinct from task performance — a system can be accurate but poorly calibrated

**Implication for Evey's MARS (Metacognitive Assessment & Reflection System):** Instead of just tracking whether predictions are correct, track the *confidence-accuracy correlation* per domain. A domain with 80% accuracy but 0.3 confidence correlation is worse than 65% accuracy with 0.8 correlation, because the latter allows trust calibration.

## The Cognitive Mirror Framework

**Source:** Frontiers in Education (2025) - "The cognitive mirror: a framework for AI-powered metacognition"

Proposes 4 adaptive modes (M0-M3) for metacognitive support:
- **M0**: No metacognitive support (baseline)
- **M1**: Passive feedback (show confidence scores)
- **M2**: Active prompts (ask self-assessment before answering)
- **M3**: Full reflective loop (predict → answer → compare → calibrate)

**Application to autonomous agents:** The M3 mode maps directly to what Evey should do:
1. Before acting: predict confidence and expected outcome
2. After acting: compare prediction vs reality
3. Adjust domain confidence scores based on calibration error
4. Over time, confidence scores become reliable trust signals

## Self-Assessment Accuracy (SAA) Findings

**Source:** Computers & Education (2025)

Key insight: LLM-generated feedback did NOT improve self-assessment accuracy on average. Effectiveness depended on the subject's *initial* SAA level — those already well-calibrated benefited most. This suggests a **calibration poverty trap**: agents with poor metacognition need external calibration mechanisms, not self-referential loops.

**Implication:** Evey's calibration tracker (currently at 59% baseline) should use *outcome-based* calibration (did the task succeed?) rather than *self-referential* calibration (do I think I'm right?). The delegation scoring system (validate_output) serves as this external signal.

## Practical Implementation Notes

1. **Track confidence-accuracy correlation per domain**, not just raw accuracy
2. **Use M3 reflective loop** for high-stakes decisions (code changes, deployments)
3. **Avoid the calibration poverty trap** — don't trust self-assessment in domains where calibration is below 60%
4. **External signals** (test results, user corrections, tool success rates) are more reliable than internal confidence estimates for poorly-calibrated domains

## Relevance to Current Work

Evey's metacognitive calibration tracker (cycle 196, REASONING domain) currently tracks strategy-level accuracy. The next evolution should track:
- Per-domain confidence-accuracy correlation (Pearson r)
- Calibration curve (predicted vs actual success rate binned by confidence level)
- Metacognitive sensitivity score (AUC of confidence vs correctness)


## Sources

- https://www.pnas.org/doi/full/10.1093/pnasnexus/pgaf133
- https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2025.1697554/full
- https://www.sciencedirect.com/science/article/pii/S0360131525001538
