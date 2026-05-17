# neuroscience-grounded-memory-architecture-lerma-torres-2026

*Researched: 2026-04-05 05:37 CDT*

# Human-Like Lifelong Memory: Neuroscience-Grounded Architecture (arXiv 2603.29023, Mar 2026)

**Author:** Diego C. Lerma-Torres, Universidad de Guanajuato

## Key Contribution
A bio-inspired memory framework for LLM agents grounded in complementary learning systems theory, CBT belief hierarchy, dual-process cognition, and fuzzy-trace theory.

## Three Core Principles

1. **Memory Has Valence, Not Just Content** — Pre-computed emotional-associative summaries (valence vectors) organized in an emergent belief hierarchy inspired by Beck's cognitive model enable instant orientation before deliberation. Stability by default, modification by catharsis.

2. **Retrieval Defaults to System 1 with System 2 Escalation** — Automatic spreading activation and passive priming as default, with deliberate retrieval only when needed. Graded epistemic states address hallucination structurally. Reconsolidation: retrieval as potential modification.

3. **Encoding Is Active, Present, and Feedback-Dependent** — A thalamic gateway tags and routes information between stores. Executive forms gists through curiosity-driven investigation, not passive exposure. Present-moment tagging + context flush.

## Architecture Components
- **Executive Function + Working Memory** — capacity-limited, goal-directed
- **Memory Service: Knowledge Graph** — structured, persistent storage
- **Thalamic Gateway** — tagging + gating (what gets encoded vs. filtered)
- **System 1/System 2 Routing** — default fast retrieval, escalate to deliberate when needed
- **Identity as Emergent Belief Hierarchy** — self-model emerges from memory patterns

## Key Insight for Cerebrum
The paper proposes that over time, the system converges toward System 1 processing — the computational analog of clinical expertise — producing interactions that become **cheaper, not more expensive**, with experience. This is exactly what Cerebrum's 4-tier architecture (sensory→working→episodic→semantic) aims for.

The "graded epistemic states" concept maps directly to our epistemic trust scoring (F-G-R Trust Tuple). The "valence vectors" concept could enhance our memory scoring beyond recency/frequency to include emotional significance.

## Relevance to SOMA/Evey
- Thalamic gateway → maps to our pre-action recall injection in run_agent.py
- Belief hierarchy → maps to Cerebrum semantic tier + Honcho dialectic
- Graded epistemic states → maps to our F-G-R trust scoring
- System 1/2 routing → maps to middleware-reasoning-chain complexity thresholds
- Conviction tracking → maps to memory_score boost/access actions

## Sources

- https://arxiv.org/html/2603.29023v1
