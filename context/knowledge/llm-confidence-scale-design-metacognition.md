# LLM confidence scale design metacognition

*Researched: 2026-04-05 11:09 CDT*

# LLM Confidence Scale Design Affects Metacognitive Quality

**Source:** "Rescaling Confidence: What Scale Design Reveals About LLM Metacognition" (arXiv:2603.09309v1, Mar 2026, Yuyang Dai, INSAIT)

## Key Findings

1. **Confidence discretization:** LLM verbalized confidence is heavily discretized — >78% of responses concentrate on just 3 round-number values (e.g., 50, 80, 100) when using standard 0-100 scales.

2. **Optimal scale: 0-20 beats 0-100.** A 0-20 scale consistently improves metacognitive efficiency (measured by meta-d') over the standard 0-100 format across 6 LLMs and 3 datasets.

3. **Boundary compression degrades performance.** Compressed or irregular ranges hurt calibration quality.

4. **Round-number bias persists** even under irregular/unnatural scale ranges, indicating deep-seated token-level preferences.

5. **Scale design is a first-class variable.** Confidence scale granularity, boundary placement, and range regularity all directly affect verbalized uncertainty quality.

## Implications for Agent Systems

- When designing self-assessment prompts for autonomous agents, use narrow scales (0-10 or 0-20) rather than 0-100 to get better-calibrated confidence scores.
- Agent metacognitive tracking (like Evey's calibration tracker at 59% baseline) should account for discretization bias — agents will anchor on round numbers.
- This supports using Likert-style scales (1-5 or 0-10) for agent self-evaluation rather than continuous percentages.


## Sources

- https://arxiv.org/html/2603.09309v1
