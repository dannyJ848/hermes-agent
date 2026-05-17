# DR-FREE distributionally robust active inference 2025

*Researched: 2026-04-05 20:27 CDT*

# DR-FREE: Distributionally Robust Free Energy Principle

**Paper:** Shafiei et al., "Distributionally robust free energy principle for decision-making," Nature Communications, vol. 17, Article 707, Dec 2025. (Co-authored by Karl Friston)

**Core Innovation:** DR-FREE combines a robust extension of the free energy principle with a resolution engine to wire robustness into agent decision-making by design. It addresses the fundamental gap where RL-trained agents fail when training-environment conditions become inconsistent.

**Key Insight:** Natural agents survive in capricious environments with little/no training, while artificial agents — even with high-fidelity simulators — produce brittle policies that fail under minor environmental mismatches (illumination changes, hardware malfunctions, etc.).

**Technical Approach:**
- Formulates an optimization where policies emerge by minimizing the **maximum** free energy over all admissible distributions (min-max formulation)
- This distributionally robust approach guarantees worst-case performance bounds
- Combines robust optimization with active inference's variational Bayes framework
- Resolution engine handles the resulting optimization problem

**Results:** Across benchmarks, DR-FREE agents complete tasks even when state-of-the-art RL models fail due to train-test distribution shift.

**Relevance to SOMA/Hermes:**
1. **Agent robustness:** Could inform how Hermes handles API failures, model degradation, and unexpected tool outputs
2. **Active inference architecture:** Validates the active inference approach for autonomous agents — directly relevant to our curiosity/exploration scoring
3. **Worst-case reasoning:** The min-max free energy formulation could improve task selection under uncertainty (e.g., when multiple goals compete and budget is limited)
4. **Multi-agent potential:** Authors note this may inspire multi-agent deployments — relevant to squad-dev patterns

## Sources

- https://www.nature.com/articles/s41467-025-67348-6
