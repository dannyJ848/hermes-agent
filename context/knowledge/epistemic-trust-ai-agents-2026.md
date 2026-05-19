# epistemic-trust-ai-agents-2026

*Researched: 2026-04-05 08:58 CDT*

# Epistemic Trust & Trustworthy Agentic AI Systems (2025-2026)

## Paper 1: Architecting Trust in Artificial Epistemic Agents
- **Source:** Marchal et al. (arXiv:2603.02960, March 2026)
- **Key thesis:** LLMs are now "epistemic agents" — entities that autonomously pursue epistemic goals and shape shared knowledge environments.
- **Framework:** Three pillars for trustworthy epistemic AI:
  1. **Epistemic competence** — reliability, calibration, accuracy of knowledge
  2. **Robust falsifiability** — claims must be testable and retractable
  3. **Epistemically virtuous behaviors** — honesty about uncertainty, avoiding hallucination
- **Key concepts:**
  - "Knowledge sanctuaries" — protected human knowledge reserves to prevent epistemic drift
  - Technical provenance systems for tracing AI-generated claims
  - Danger of "cognitive deskilling" — humans losing expertise by over-relying on AI
  - Multi-agent interactions create new informational interdependencies requiring new governance
- **Relevance to Cerebrum:** The F-G-R Trust Tuple (Formation, Grounding, Recency) I implemented maps directly to their "epistemic competence" pillar. Our trust scoring is a concrete implementation of their theoretical framework.

## Paper 2: Trustworthy Agentic AI Systems (Cross-Layer Review)
- **Source:** Adabara et al. (F1000Research 14:905, Sep 2025)
- **Key thesis:** Agentic AI (with autonomous reasoning, memory augmentation, adaptive planning) introduces novel security risks beyond traditional LLM concerns.
- **Architecture components reviewed:**
  - Memory-augmented decision making
  - Persistent execution across dynamic environments
  - Threat taxonomies specific to autonomous agents
- **Key concepts:**
  - **Zero-trust principles** for multi-agent systems — every agent interaction must be verified
  - **Dynamic trust scoring** — trust is not binary, must be continuously recalculated
  - **Secure registries** — prevent agent impersonation and data poisoning
  - Cross-layer threat model spanning infrastructure, model, agent, and application layers
- **Relevance to Cerebrum:** Our memory trust scoring (F-G-R tuple) implements their "dynamic trust scoring" recommendation at the memory layer. The zero-trust principle validates our approach of scoring each memory fact independently rather than trusting all stored knowledge equally.

## Synthesis for Cerebrum Design
Both papers validate the Cerebrum approach:
1. Individual fact trust scoring (F-G-R) maps to "epistemic competence" and "dynamic trust scoring"
2. Memory decay/pruning maps to "falsifiability" — removing ungrounded claims
3. Provenance tracking (which source, when stored) maps to "technical provenance systems"
4. The papers suggest adding: explicit uncertainty markers per fact, retraction mechanisms for disproven claims, and cross-validation between multiple sources before high-trust scoring


## Sources

- https://arxiv.org/abs/2603.02960
- https://f1000research.com/articles/14-905
