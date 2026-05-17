# AI Metacognitive Sensitivity in Human-AI Decision Making

*Researched: 2026-04-05 10:55 CDT*

# AI Metacognitive Sensitivity in Human-AI Decision Making

**Source:** Li & Steyvers (2025), "Beyond Accuracy: How AI Metacognitive Sensitivity improves AI-assisted Decision Making" — arXiv:2507.22365v2, UC Irvine.

## Key Findings

### Metacognitive Sensitivity vs Calibration
- **Metacognitive sensitivity** = AI's ability to assign confidence scores that accurately distinguish correct from incorrect predictions (high confidence when right, low when wrong).
- **Metacognitive calibration** = whether confidence scores match actual accuracy probabilities.
- Sensitivity matters MORE than calibration for human-AI complementarity.

### Signal Detection Framework
- The authors introduce a formal signal detection theory (SDT) framework for analyzing joint impact of AI accuracy + metacognitive sensitivity.
- They derive conditions where an AI with **lower accuracy but higher metacognitive sensitivity** outperforms a more accurate AI with poor sensitivity in hybrid decision-making.

### Behavioral Experiment Results
- Greater AI metacognitive sensitivity measurably improves human decision performance.
- Humans appropriately defer to high-confidence AI predictions and reject low-confidence ones when metacognitive sensitivity is high.
- This creates genuine complementarity — the human-AI team exceeds either alone.

### Practical Implications for Agent Design
1. **Don't just optimize accuracy** — optimize the correlation between confidence and correctness.
2. **Confidence scores are communication signals** — they tell the human when to trust the AI.
3. **Trading accuracy for sensitivity can be net positive** in human-AI collaboration settings.
4. For autonomous agents (like Evey): calibrating delegation confidence (when to trust vs verify subagent output) directly parallels this framework.

### Connection to SOMA/Agent Work
- Evey's metacognitive calibration tracker (59% baseline) measures a similar construct.
- The SDT framework could formalize Evey's self-assessment: track confidence-per-task-type, measure correlation with actual outcomes, optimize the confidence signal.
- Key insight: it's not enough to be accurate — the agent must **know when it's right vs wrong** and communicate that reliably.


## Sources

- https://arxiv.org/html/2507.22365v2
- https://www.pnas.org/doi/full/10.1093/pnasnexus/pgaf133
