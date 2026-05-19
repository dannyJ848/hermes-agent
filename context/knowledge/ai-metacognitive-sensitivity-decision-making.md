# ai-metacognitive-sensitivity-decision-making

*Researched: 2026-04-05 11:19 CDT*

# AI Metacognitive Sensitivity in Human-AI Decision Making

**Source:** Li & Steyvers (2025), "Beyond Accuracy: How AI Metacognitive Sensitivity improves AI-assisted Decision Making", arXiv:2507.22365v2, UC Irvine.

## Key Findings

### Metacognitive Sensitivity vs Calibration
- **Metacognitive sensitivity** = AI's ability to assign confidence scores that accurately distinguish correct from incorrect predictions (type 2 signal detection)
- **Metacognitive calibration** = absolute accuracy of confidence scores relative to actual performance
- Sensitivity matters MORE than calibration for human-AI complementarity

### Counterintuitive Result
- An AI with **lower predictive accuracy but HIGHER metacognitive sensitivity** can improve overall human decision accuracy more than a more accurate but less metacognitively sensitive AI
- This is because humans can better learn when to trust vs override the AI's advice

### Signal Detection Framework
- Formalized using type 2 SDT: confidence distributions for correct vs incorrect predictions
- Switch point c* determines when humans should accept vs reject AI advice
- Human confidence adapts based on observed AI confidence signals

### Implications for Agent Design
1. **Agents should expose calibrated confidence**, not just answers
2. **Training for confidence discrimination** may matter more than raw accuracy gains
3. **Hybrid decision-making** benefits from AI that "knows what it doesn't know"
4. For Evey: tracking confidence calibration per domain (as in epistemic-trust-scoring) directly supports metacognitive sensitivity

### Human Calibration Data (from PMC study)
- Average human calibration error: 15.73 percentage points (sd=12.8pp)
- LLMs can exceed human metacognitive sensitivity in narrow domains
- XAI exposure reduces overconfidence in human experts (real estate agents study)


## Sources

- https://arxiv.org/html/2507.22365v2
- https://www.pnas.org/doi/full/10.1093/pnasnexus/pgaf133
- https://pmc.ncbi.nlm.nih.gov/articles/PMC12957136/
