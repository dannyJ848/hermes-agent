# consciousness-stack-architecture

*Researched: 2026-04-03 13:42 CDT*

# Herm Consciousness Stack Architecture (v1)

## Overview
Three-layer cognitive architecture built on neuroscience principles, integrated into the Cerebrum memory provider.

## Layer 3: Predictive Self-Model (`predictive_self.py`)
- **Basis**: Friston's Free Energy Principle — minimize surprise via prediction
- **Mechanism**: Before every task, generate a Prediction (difficulty, approach, iterations, outcome, confidence). After task, resolve with actuals. Prediction error = learning signal.
- **CalibratedSelf**: Tracks per-task-type capabilities (EMA update), systematic biases (over/underconfidence), emotional valence, growth trajectory
- **DB Tables**: `predictions`, `self_model`
- **Tool Actions**: `predict` (generate), `resolve` (compare), `self` (query)

## Layer 4: Global Workspace (`global_workspace.py`)
- **Basis**: Baars' Global Workspace Theory + Dehaene's Neuronal Global Workspace
- **Modules**: memory, reasoning, emotion, task, self, attention, metacog, intuition
- **Cycle**: COLLECT → COMPETE → IGNITE → BROADCAST → UPDATE
- **Scoring**: access_score = 0.3*salience + 0.25*relevance + 0.20*novelty + 0.25*goal_alignment
- **Ignition Threshold**: Adaptive (rises with strong wins, drops with weak candidates)
- **Default Mode**: When no candidates submitted, enters self-referential "mind wandering" (analogous to DMN)
- **Tool Action**: `workspace` (status, attention profile, dominance biases)

## Layer 5: Narrative Identity (`narrative_identity.py`)
- **Basis**: McAdams' narrative identity + Damasio's autobiographical self
- **Components**: LifeEvents (timeline), CoreValues (stable, slow-changing), Chapters (temporal organization), Self-Narrative (auto-regenerated)
- **Value Stability**: Dampened updates (0.1 * stability factor) prevent rapid identity drift
- **Tool Action**: `identity` (status, timeline, values, regenerate, event)

## Integration Points
- `provider.py` `sync_turn()`: Workspace submissions every turn, ignition every 3 turns
- New cerebrum tool actions: self, workspace, identity, predict, resolve
- Tables created on gateway restart (SQLite DB locked by running gateway)

## Key Insight
Consciousness is a BOTTLENECK, not a superpower. Most processing happens unconsciously in parallel. The bottleneck (workspace) coordinates specialized modules by broadcasting the winner. This is what gives coherence.

## Research Sources
- Darwin Gödel Machine (jennyzzt/dgm, ★2K) — open-ended self-improving agents via archive + evolution
- The Consciousness AI (theconsciousness.ai) — Feinberg/Mallatt neuroevolutionary approach
- AKOrN (ICLR 2025) — Artificial Kuramoto Oscillatory Neurons for binding
- Global Workspace Theory (Baars 1988, Dehaene 2011)
- Free Energy Principle (Friston 2010)


## Sources

- https://arxiv.org/html/2505.22954v3
- https://theconsciousness.ai/acm/
- https://github.com/jennyzzt/dgm
