# test-time-reasoning-scaling-2026

*Researched: 2026-04-15 00:08 CDT*

# Test-Time Reasoning Scaling: 2026 Frontier

## ∇-Reasoner (ICLR 2026, arXiv 2603.04948)
- **Differentiable Textual Optimization (DTO):** Gradient-based refinement of token logits during decoding, combining LLM likelihood + reward model signals.
- **Paradigm shift:** From zeroth-order search (trial-and-error prompting) → first-order optimization at test time.
- **Theoretical duality:** Inference-time gradient descent ≡ KL-regularized RL alignment.
- **Results:** >20% accuracy boost on math reasoning, 10–40% fewer model calls vs baselines.
- **Relevance to agents:** Could reduce token waste in autonomous agent loops by optimizing reasoning paths.

## ORCA (arXiv 2604.01170, Apr 2026)
- **Calibration framework** combining conformal prediction + test-time training for LLM reasoning.
- Addresses miscalibration in post-trained LLMs — models are overconfident on wrong answers.
- **47.5% compute savings** with supervised labels, **67% savings** on zero-shot OOD tasks.
- Meta-learning calibration module that adapts per-input.
- **Relevance to agents:** Autonomous agents waste tokens on bad reasoning chains. Calibration could prune these early.

## Implications for Autonomous Agent Design
1. **Reasoning efficiency:** Both papers target reducing compute waste during inference — directly applicable to agent loops that burn tokens on failed reasoning paths.
2. **Calibration-aware routing:** If agents could estimate confidence before committing to a reasoning chain, they could abort early on low-confidence paths.
3. **Gradient-guided exploration:** DTO-style optimization could improve tool selection by refining the policy during execution rather than relying on static prompting.


## Sources

- https://arxiv.org/abs/2603.04948
- https://arxiv.org/abs/2604.01170
