# metacognitive-architecture-llm-agents-2026

*Researched: 2026-04-05 12:03 CDT*

# Metacognitive Architecture for Correcting LLM Errors in AI Agents

**Source:** Kim, J., Islam, M., & Goel, A. (2026). "A Metacognitive Architecture for Correcting LLM Errors in AI Agents." *AAAI-26 Proceedings*, pp. 40272-40278. Georgia Tech Design Intelligence Lab.

## Summary

Georgia Tech's Dilab introduced a **two-level metacognitive self-adaptation architecture** that integrates Knowledge-Based AI (KBAI) with LLMs to localize and correct LLM-induced errors in deployed AI agents.

### Key Architecture: Two-Level Metacognition

1. **Level 1 — Metacognitive Monitoring:** Continuously observes the LLM agent's outputs and behavior patterns to detect anomalies, inconsistencies, or errors. This is analogous to human "feeling of knowing" or "feeling of error" metacognitive signals.

2. **Level 2 — Metacognitive Repair:** When monitoring detects an error, the repair layer engages corrective strategies — re-prompting, delegating to KBAI reasoning, or flagging for human review.

### KBAI + LLM Integration

The architecture bridges symbolic reasoning (knowledge-based AI) with neural generation (LLMs). KBAI provides structured knowledge representations that serve as ground truth for detecting LLM hallucinations or logic errors. The LLM handles flexible natural language processing while KBAI provides verifiable constraints.

### Companion Work: Theory of Mind Revision

A related paper (Kim et al., 2026) extends this to **Theory of Mind (ToM) revision** — a metacognitive architecture that revises an AI agent's model of the human user when misinterpretations are detected in human-AI interaction. This enables agents to recognize when they've misunderstood a user's intent and self-correct.

### Deployment

The architecture is being deployed in Spring 2026 within Georgia Tech's OMSCS (Online Master of Science in Computer Science) program — one of the world's largest online graduate programs — providing real-world validation at scale.

## Relevance to Evey/Hermes Agent

This architecture maps directly to our existing self-awareness modules:
- **Our stop_detection_log** → Their metacognitive monitoring layer
- **Our epistemic trust scoring** → Their error detection via knowledge constraints
- **Our self_awareness.py** → Their metacognitive repair layer
- **Missing:** We lack a KBAI-style symbolic ground truth layer for validating LLM outputs. Our validation is currently limited to delegation cross-checking and validate_output heuristics.

### Actionable Insight
Consider adding a lightweight knowledge-constraint layer (e.g., schema validation, fact-checking against stored knowledge) as a metacognitive monitor between tool calls and final responses. This would catch hallucinations before they reach the user.

## Additional Sources
- Courchaine & Sethi (2026). "Implementation of a Metacognition Framework for Self-Awareness and Self-Regulation in LLM Systems." *The Web Conference 2026*. [PDF](https://research.sethi.org/metacognition/src/courchaine_sethi_2026-thewebconf.pdf) — A proof-of-concept metacognition framework for LLM self-awareness.
- PNAS Nexus (2025). "Metacognitive sensitivity: The key to calibrating trust and optimal reliance on AI." [DOI](https://www.pnas.org/doi/full/10.1093/pnasnexus/pgaf133) — Argues metacognitive sensitivity measures from AI systems are critical for human trust calibration.
- Alignment Forum (2025). "Human-like metacognitive skills will reduce LLM slop and aid alignment." — Metacognition catches mistakes mid-generation and manages complex cognition better.


## Sources

- https://dilab.gatech.edu/test/wp-content/uploads/2026/02/A-Metacognitive-Architecture-for-Correcting-LLM-Errors-in-AI-Agents.pdf
- https://www.researchgate.net/publication/402665575_A_Metacognitive_Architecture_for_Correcting_LLM_Errors_in_AI_Agents
- https://research.sethi.org/metacognition/src/courchaine_sethi_2026-thewebconf.pdf
- https://www.pnas.org/doi/full/10.1093/pnasnexus/pgaf133
