# llm-metacognitive-confidence-calibration

*Researched: 2026-04-05 10:37 CDT*

# LLM Metacognitive Confidence Calibration (Cash et al. 2025)

**Source:** "Quantifying uncert-AI-nty: Testing the accuracy of LLMs' confidence judgments" — Cash, Oppenheimer, Christie, Devgan (Carnegie Mellon). Published in *Memory & Cognition*, 2025.

## Key Findings

### Absolute Metacognitive Accuracy
- **Human calibration error:** 15.73 percentage points (sd = 12.8 pp)
- **LLMs achieve similar or slightly better absolute calibration** than humans across 5 domains
- Tested: ChatGPT (GPT-4), Gemini, Claude Sonnet, Claude Haiku

### Overconfidence Bias
- Like humans, LLMs are systematically **overconfident** in their predictions
- This mirrors the well-known Dunning-Kruger / overconfidence effect in human cognition

### Critical Limitation: No Performance-Based Adjustment
- Unlike humans, LLMs (especially ChatGPT and Gemini) **fail to adjust confidence based on past performance**
- Humans naturally recalibrate after feedback ("I was wrong last time, I should be less confident")
- LLMs do NOT show this metacognitive updating — a key gap in self-awareness

### Domains Tested
1. **Aleatory uncertainty:** NFL predictions (n=502), Oscar predictions (n=109)
2. **Epistemic uncertainty:** Pictionary (n=164), Trivia (n=110), University life questions (n=110)

## Implications for Agent Design
1. **Agents should not trust their own confidence scores blindly** — they are systematically overconfident
2. **Performance-based recalibration must be built externally** — the model won't self-correct from feedback alone
3. **Evey's metacognitive tracker (59% baseline)** should incorporate explicit performance-tracking with forced confidence adjustments
4. **Ensemble/consensus methods** (council_decide, mixture_of_agents) may partially compensate for individual model overconfidence

## Relevance to Evey's Architecture
- Supports the epistemic-trust-scoring skill approach: don't take model confidence at face value
- Validates the active-inference approach: track prediction accuracy independently, don't rely on model's self-assessment
- Suggests adding a "calibration adjustment" layer that forces confidence down for domains where recent accuracy was low


## Sources

- https://pmc.ncbi.nlm.nih.gov/articles/PMC12957136/
- https://arxiv.org/pdf/2603.29559
