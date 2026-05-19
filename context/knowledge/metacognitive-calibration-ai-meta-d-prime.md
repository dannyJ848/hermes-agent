# metacognitive-calibration-ai-meta-d-prime

*Researched: 2026-04-05 11:46 CDT*

# Metacognitive Calibration in AI: The meta-d' Framework (2026)

## Paper: "Measuring the Metacognition of AI" (arXiv 2603.29693, Mar 2026)
**Authors:** Servajean & Servajean (RIKEN Center for Brain Science / Paul-Valéry University)

### Key Contribution
Proposes **meta-d'** (from signal detection theory) as the gold standard for measuring AI metacognitive sensitivity — the ability to generate confidence ratings that distinguish correct from incorrect responses.

### Core Framework
1. **meta-d'**: Measures how well an AI's confidence ratings discriminate between correct and incorrect answers. A meta-d' equal to d' means perfect metacognitive sensitivity (ideal calibration).
2. **Model-free alternatives**: For cases where meta-d' computation is impractical.
3. **Risk-based regulation**: Uses SDT to assess whether LLMs become more conservative when decision risks are high.

### Three Axes of Comparison
- **AI vs. optimality** — How close is the model to ideal metacognitive performance?
- **Model vs. model** — Comparing GPT-5, DeepSeek-V3.2-Exp, Mistral-Medium-2508
- **Task vs. task** — Same model across different domains

### Relevance to Hermes Agent
This framework provides a rigorous way to measure our own metacognitive calibration. Currently we track a 59% baseline accuracy in predictions. Applying meta-d' would let us:
1. Formally score whether our confidence ratings match actual performance
2. Compare calibration across task types (research, coding, delegation)
3. Detect overconfidence/underconfidence per domain

### Practical Integration
- Track confidence (1-10) with every tool call outcome
- Compute meta-d' = how well confidence separates success from failure
- Target: meta-d' / d' ratio approaching 1.0 (ideal calibration)
- Currently: 59% accuracy suggests significant calibration gap — meta-d' would quantify exactly how much

### Sources
- arXiv:2603.29693 (March 2026)
- Tested on GPT-5, DeepSeek-V3.2-Exp, Mistral-Medium-2508


## Sources

- https://arxiv.org/html/2603.29693v1
