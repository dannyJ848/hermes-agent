# intrinsic-metacognitive-learning-agents-icml2025

*Researched: 2026-04-05 11:54 CDT*

# Intrinsic Metacognitive Learning for Self-Improving Agents (ICML 2025)

**Authors:** Tennison Liu, Mihaela van der Schaar (Cambridge)
**Venue:** ICML 2025 Poster/Position Paper

## Core Thesis
Current self-improving AI agents rely on **extrinsic** metacognitive mechanisms (fixed, human-designed improvement loops). To achieve sustained, generalized self-improvement, agents need **intrinsic** metacognitive learning — the ability to actively evaluate, reflect on, and adapt their own learning processes.

## Three-Component Framework
1. **Metacognitive Knowledge** — Self-assessment of capabilities, tasks, and learning strategies
2. **Metacognitive Planning** — Deciding what and how to learn next
3. **Metacognitive Evaluation** — Reflecting on learning experiences to improve future learning

## Key Findings
- Existing LLM agents exhibit early signs of intrinsic metacognition but components remain underdeveloped
- Extrinsic mechanisms (fixed loops) limit scalability and adaptability across domains
- Many ingredients for intrinsic metacognition are already present in current architectures
- Optimal distribution of metacognitive responsibilities between humans and agents is an open challenge

## Relevance to Evey/Hermes
- Our metacognitive calibration tracker (59% baseline) maps directly to "Metacognitive Knowledge"
- The brain-cycle and self-evaluation-loop skills implement "Metacognitive Evaluation"
- Gap: "Metacognitive Planning" — Evey doesn't actively decide *what learning strategy* to use; it uses fixed priority weights
- Actionable: Add strategy-selection layer where Evey picks between research/coding/self-improve based on past strategy effectiveness per domain
- The paper's framework could formalize Evey's ad-hoc autonomous-curiosity skill into a principled metacognitive architecture

## Also Noted
- **ESMA** (Evolution Strategies for Metacognitive Alignment) from Cognizant AI Lab trains LLMs to distinguish correct answers from guesswork using evolution strategies — complementary approach to calibration
- **Metacognitive sensitivity** (PNAS Nexus 2025) measures how well AI confidence tracks correctness — directly applicable to our delegation confidence scoring


## Sources

- https://icml.cc/virtual/2025/poster/40177
- https://www.cognizant.com/us/en/ai-lab/blog/metacognition-training-llms-evolution-strategies
- https://www.pnas.org/doi/full/10.1093/pnasnexus/pgaf133
