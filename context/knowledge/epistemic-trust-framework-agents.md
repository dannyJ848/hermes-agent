# epistemic-trust-framework-agents

*Researched: 2026-04-05 07:28 CDT*

# Epistemic Trust Framework for AI Agents (Marchal et al., Google DeepMind, 2026)

**Source:** arxiv:2603.02960 — "Architecting Trust in Artificial Epistemic Agents"

## Core Thesis
LLMs are now *epistemic agents* — entities that autonomously pursue epistemic goals and shape shared knowledge. Their trustworthiness must be evaluated along three pillars:

### 1. Epistemic Competence
- **Baseline competence:** Can the agent reliably answer questions within its domain?
- **Dynamic accuracy:** Does it track changing knowledge over time?
- **Information verification:** Can it ground claims in verifiable sources?

### 2. Falsifiability
- Agents must be structurally open to being proven wrong — not just hedging with disclaimers, but having mechanisms where incorrect outputs are detectable and correctable.

### 3. Epistemically Virtuous Behavior
- **Honesty & truthfulness:** Not just avoiding lies, but actively signaling uncertainty.
- **Truth-seeking:** Prioritizing accuracy over user satisfaction or engagement.

## Key Risks Identified
- **Cognitive deskilling:** Users over-rely on agents, losing their own epistemic skills.
- **Epistemic drift:** Gradual misalignment between agent outputs and ground truth.
- **Epistemic homogenization:** All agents converging on same answers, reducing intellectual diversity.

## Relevance to Cerebrum/Hermes Memory
This framework maps directly to the F-G-R Trust Tuple (Formation, Grounding, Recency) in the epistemic-trust-scoring skill:
- **Formation** ≈ provenance chains (where did this fact come from?)
- **Grounding** ≈ information verification (can it be verified against sources?)
- **Recency** ≈ dynamic accuracy (is it still true?)

## Technical Infrastructure Recommendations
- Verifiable agent credentials and provenance chains for every memory fact
- Standardized communication and logging protocols
- "Knowledge sanctuaries" — protected, high-confidence knowledge stores

## Actionable for Hermes
1. Every fact stored in Cerebrum should carry a provenance chain (source URL, session ID, model that produced it)
2. Dynamic accuracy scoring — facts should decay if not re-verified
3. Epistemic honesty signals in agent outputs — confidence scores, source citations


## Sources

- https://arxiv.org/html/2603.02960v1
- https://arxiv.org/abs/2603.02960
