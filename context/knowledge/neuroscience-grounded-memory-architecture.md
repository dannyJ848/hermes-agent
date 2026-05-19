# neuroscience-grounded-memory-architecture

*Researched: 2026-04-05 05:31 CDT*

# Human-Like Lifelong Memory: Neuroscience-Grounded Architecture

**Source:** arXiv:2603.29023v1 (Mar 2026) — Diego C. Lerma-Torres, Universidad de Guanajuato

## Key Contribution
A bio-inspired memory framework for LLMs grounded in complementary learning systems theory, CBT belief hierarchy, dual-process cognition, and fuzzy-trace theory.

## Three Core Principles

1. **Memory has valence, not just content** — Pre-computed emotional-associative summaries (valence vectors) organized in an emergent belief hierarchy (inspired by Beck's cognitive model) enable instant orientation before deliberation. This is what Cerebrum's episodic→semantic tier approximates.

2. **Retrieval defaults to System 1 with System 2 escalation** — Automatic spreading activation and passive priming as default, deliberate retrieval only when needed. Graded epistemic states address hallucination structurally. Maps to Cerebrum's pre-action recall (System 1) vs. deep Honcho search (System 2).

3. **Encoding is active, present, and feedback-dependent** — A thalamic gateway tags and routes information between stores. Executive forms gists through curiosity-driven investigation, not passive exposure. This validates Cerebrum's sensory→working→episodic→semantic pipeline.

## Relevant Architecture Components
- **Thalamic Gateway**: Tags + gates information flow between memory stores (Cerebrum's tier router)
- **Belief Hierarchy**: Emergent from CBT — core beliefs → intermediate → automatic thoughts (maps to Cerebrum semantic layer)
- **Graded Epistemic States**: Knowledge has confidence levels, not binary true/false (validates F-G-R trust scoring)
- **Reconsolidation**: Retrieval is potential modification — memories update when accessed (Cerebrum episodic reconsolidation)
- **Convergence to System 1**: Over time, expertise = cheaper processing (validates Cerebrum's cache patterns)

## Related Work to Explore
- HippoRAG / HippoRAG 2 — knowledge graphs with Personalized PageRank
- EM-LLM — surprise-boundary segmentation
- EcphoryRAG — cue-driven retrieval
- Titans — three integrated memory types

## Implications for Cerebrum
- Add **valence vectors** to semantic facts (emotional/associative weight)
- Implement **graded epistemic states** (not just confidence, but epistemic status: known/assumed/speculative/dreamed)
- **Thalamic gateway** pattern for routing sensory input to appropriate tier
- **Reconsolidation** on retrieval — update facts when accessed, not just on storage

## Key Stat
Context expansion alone degrades LLM reasoning by up to 85% (Du et al., 2025). This validates the need for structured memory beyond context windows.


## Sources

- https://arxiv.org/html/2603.29023v1
