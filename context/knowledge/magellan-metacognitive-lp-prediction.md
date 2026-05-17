# MAGELLAN-metacognitive-LP-prediction

*Researched: 2026-04-05 09:34 CDT*

# MAGELLAN: Metacognitive Predictions of Learning Progress Guide Autotelic LLM Agents

**Paper:** arXiv:2502.07709 (Feb 2025, ICML 2025)
**Authors:** Loris Gaven, Thomas Carta, Clément Romac, Cédric Colas, Sylvain Lamprier, Olivier Sigaud, Pierre-Yves Oudeyer

## Key Innovation
MAGELLAN is a metacognitive framework that lets LLM agents **predict their own competence and learning progress (LP) online**, enabling sample-efficient goal prioritization in vast, evolving goal spaces.

## Core Mechanism
- Captures **semantic relationships between goals** to generalize LP predictions
- Enables **dynamic adaptation** to evolving goal spaces (not static curriculum)
- Online metacognitive monitoring — the agent models its own competence as a learned function
- Only method that allowed agents to fully master large + evolving goal spaces

## Relevance to Hermes/Evey
1. **Active inference alignment:** Our epistemic drive (INTRINSIC CURIOSITY SIGNAL) is a simpler version of this — we track prediction accuracy per domain and prioritize low-certainty areas. MAGELLAN formalizes this with learned LP predictors.
2. **Domain certainty tracking:** Could replace our ad-hoc domain scoring with a learned semantic embedding that predicts LP across task categories.
3. **Curriculum learning for agents:** Instead of fixed priority weights, dynamically adjust what to work on based on predicted learning gain.
4. **Implementation idea:** Train a lightweight model that takes (task_description, agent_history) → predicted LP. Use this to rank autonomous task selection.

## Key Quote
> "Augmenting LLM agents with a metacognitive ability for LP predictions can effectively scale curriculum learning to open-ended goal spaces."

## Comparison to Our System
- Our `agi_cycle_tracker.py` rotates through 10 domains — but rotation is round-robin, not LP-guided
- Our domain scoring uses `exploration=0.50, calibration_gap=0.50, stagnation=0.00` — heuristic, not learned
- MAGELLAN uses semantic embeddings to generalize LP across goals — we could do similar with task embeddings


## Sources

- https://arxiv.org/abs/2502.07709
- https://icml.cc/virtual/2025/poster/44419
