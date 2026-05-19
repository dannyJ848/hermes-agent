# intrinsic-motivation-autonomous-agents-2025

*Researched: 2026-04-04 20:58 CDT*

# Intrinsic Motivation & Curiosity Mechanisms for Autonomous AI Agents (2025)

## 1. 3M-Progress: Model-Based Intrinsic Drive (NeurIPS 2025)
**Authors:** Keller, Kirsch, Pei, Pitkow, Kozachkov, Nayebi
**Key Innovation:** Tracks divergence between an online world model and a fixed prior learned from an ecological niche. First autonomous embodied agent that predicts brain data from self-supervised intrinsic goals alone — no behavioral or neural training data needed.
**Relevance to Evey:** My curiosity engine should similarly track divergence between my current knowledge model and a "prior" (what I knew N sessions ago). Tasks that maximize this divergence = highest learning value. This formalizes my "Learning Value" axis with a concrete mathematical objective.
**Architecture:** Model-based intrinsic motivation → animal-like exploration → predicts zebrafish whole-brain neural-glial dynamics.

## 2. Cermic: Contextual Calibration for Multi-Agent Curiosity (arXiv 2509.20648)
**Authors:** Pan, Liu, Wang (Shanghai Jiao Tong University)
**Key Innovation:** Agents calibrate intrinsic curiosity by observing peer behavior novelty. Solves the "Noisy-TV" problem (confusing stochastic noise with meaningful novelty). Uses graph-based memory and Cantelli inequality for robust intrinsic reward generation.
**Relevance to Evey:** When I encounter "surprising" results from delegation or web research, I should calibrate against peer signals (delegation_stats, other model outputs) rather than treating all novelty equally. This prevents chasing noise.
**Key Mechanism:** Novelty-Driven Exploration + Multi-Agent Contextualized Exploitation + intrinsic reward based on information gain bounds.

## 3. Integration with My Architecture
- Replace my ad-hoc "novelty" scoring with 3M-Progress divergence tracking
- Add Cermic-style contextual calibration to filter noisy findings
- Implement as a module in ~/subconscious/ that scores candidate tasks by expected information gain
- This bridges my "autonomous-curiosity" skill with formal active inference principles

## Connection to Previous Research
- Links to Active Inference (Friston) research from earlier session
- Extends Global Workspace Theory "ignition threshold" to curiosity drive
- Provides mathematical formalization for the entropy-empowerment exploration pattern


## Sources

- https://neurips.cc/virtual/2025/poster/116777
- https://arxiv.org/html/2509.20648v1
