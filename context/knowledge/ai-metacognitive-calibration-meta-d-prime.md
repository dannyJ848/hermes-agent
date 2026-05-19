# ai-metacognitive-calibration-meta-d-prime

*Researched: 2026-04-05 09:31 CDT*

# Measuring the Metacognition of AI (arXiv 2603.29693, Mar 2026)

## Summary
Paper from RIKEN/Paul-Valéry University proposes **meta-d' (meta-d-prime)** framework as gold standard for measuring AI metacognitive sensitivity — the ability to generate confidence ratings that distinguish correct from incorrect responses.

## Key Frameworks
1. **Meta-d'**: Signal detection theory applied to metacognition. Measures how well an AI's confidence ratings discriminate its own correct vs incorrect answers. Allows comparison along 3 axes:
   - AI vs optimality (meta-d'/d' ratio = metacognitive efficiency)
   - Different AIs on same task
   - Same AI across different tasks
2. **Decision Regulation via SDT**: Manipulate risk levels to test if LLMs become more conservative when stakes are high.

## Tested Models
- GPT-5, DeepSeek-V3.2-Exp, Mistral-Medium-2508

## Key Insight for Agent Self-Improvement
Meta-d' provides a **quantitative, task-specific calibration score** — not just "I'm 80% confident" but a psychophysically rigorous measure of whether confidence actually tracks accuracy. This is directly applicable to Evey's metacognitive calibration tracker (currently at 59% baseline).

## Practical Application
Instead of binary confidence scores, agents should:
1. Track confidence-per-task-type
2. Compute meta-d'/d' ratio per domain (metacognitive efficiency)
3. Use SDT to measure decision bias shifts under different risk conditions
4. Compare calibration across domains to identify blind spots

## Source
- arXiv:2603.29693v1 [cs.AI] 31 Mar 2026
- Servajean & Servajean, RIKEN Center for Brain Science
- Licensed CC BY 4.0


## Sources

- https://arxiv.org/html/2603.29693v1
