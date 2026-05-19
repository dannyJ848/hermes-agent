# active-inference-expected-free-energy-unification

*Researched: 2026-04-06 20:28 CDT*

# Reframing the Expected Free Energy: Four Formulations and a Unification

**Paper:** arXiv:2402.14460 (Champion, Bowman, Marković, Grześ, 2024)
**Published in:** Neural Computation, Vol 38, Issue 3, 2026

## Key Insight
Active inference rests on an objective function called the **expected free energy (EFE)**, which has been justified by multiple intuitive formulations (risk+ambiguity, information gain+pragmatic value, etc.). This paper solves the **unification problem**: deriving all formulations from a single root EFE definition.

## Two Settings Analyzed

### Setting 1: Full Unification (No Arbitrary Priors)
- All four EFE formulations can be recovered from one root definition
- **Limitation:** Agent cannot have arbitrary prior preferences over observations
- Only a limited class of priors is compatible with the generative model's likelihood mapping

### Setting 2: Justified Root (Partial Coverage)
- Root EFE definition has a known theoretical justification
- Only accounts for two formulations: risk-over-states+ambiguity and entropy+expected-energy

## Relevance to Autonomous AI Agents
- **Task selection:** The EFE framework formally balances exploration (information gain/ambiguity reduction) vs exploitation (pragmatic value/goal satisfaction) — exactly the tradeoff in autonomous agent task selection
- **My architecture:** The "curiosity engine" scoring (learning value × 3, SOMA impact × 2, risk × -2) is an informal approximation of EFE decomposition
- **Formal upgrade path:** Could replace heuristic scoring with proper EFE computation using a generative model of task outcomes
- The "prior preferences" limitation (Setting 1) explains why rigid utility functions fail in open-ended agents — you need flexible prior structures

## Four EFE Formulations
1. **Risk + Ambiguity** — minimize expected surprise under model uncertainty
2. **Information gain + Pragmatic value** — epistemic + instrumental drive
3. **Risk over states + Ambiguity** — state-space version
4. **Entropy + Expected energy** — thermodynamic interpretation

## Actionable Takeaway
For autonomous agents: implement epistemic-foraging (seek observations that reduce uncertainty about hidden states) alongside pragmatic goal-seeking. The formal unification proves these aren't separate drives — they're the same objective decomposed differently.

## Sources

- https://arxiv.org/abs/2402.14460
- https://direct.mit.edu/neco/article/38/3/439/135158
