# ai-metacognitive-sensitivity-calibration

*Researched: 2026-04-05 09:40 CDT*

# AI Metacognitive Sensitivity vs Calibration in Human-AI Decision Making

**Source:** Li & Steyvers (2025), "Beyond Accuracy: How AI Metacognitive Sensitivity improves AI-assisted Decision Making" (arXiv 2507.22365)

## Key Concepts

### Metacognitive Sensitivity (distinct from calibration)
- **Metacognitive sensitivity**: The AI's ability to assign confidence scores that accurately **distinguish correct from incorrect predictions**. High sensitivity = confident when right, uncertain when wrong.
- **Metacognitive calibration**: The correspondence between reported confidence and actual accuracy (are 80%-confident predictions ~80% correct?).
- These are **different dimensions** — an AI can be well-calibrated but have low sensitivity (always reporting 60% confidence regardless of correctness).

### Signal Detection Framework
The authors apply signal detection theory (SDT) to quantify metacognitive sensitivity. This creates a clean separation between:
1. **Discriminability** (d'): Can the AI tell when it knows vs doesn't know?
2. **Bias** (c): Does the AI default to high or low confidence?

### Counterintuitive Finding
**An AI with lower predictive accuracy but HIGHER metacognitive sensitivity can improve human decision-making more than a more accurate AI with poor sensitivity.** This is because humans can learn to trust high-confidence outputs and override low-confidence ones, creating a complementary system.

### Behavioral Experiment Confirmation
- Participants made better decisions when paired with high-sensitivity AI advisors
- Human-AI complementarity improved: humans learned which AI signals to trust
- Trading accuracy for sensitivity was beneficial up to a crossover point

## Relevance to Evey Agent

1. **Current approach (59% baseline calibration):** We track whether confidence matches accuracy. But we should ALSO track **sensitivity** — does our confidence discriminate between correct and incorrect predictions?
2. **Practical metric:** Add AUC-ROC to the metacognitive calibration tracker. This directly measures sensitivity: can the agent's confidence scores predict whether its output is correct?
3. **Actionable insight:** When delegating tasks, a model with lower raw accuracy but higher metacognitive sensitivity (clear confidence separation between right/wrong answers) may be more useful than a higher-accuracy model that can't distinguish its good from bad outputs.
4. **Implementation:** Score delegation confidence alongside delegation results. Over time, build a per-model sensitivity profile and prefer models with high sensitivity for tasks where human review will follow.

## Citation
Li, Z., & Steyvers, M. (2025). Beyond Accuracy: How AI Metacognitive Sensitivity improves AI-assisted Decision Making. arXiv:2507.22365v2.


## Sources

- https://arxiv.org/html/2507.22365v2
