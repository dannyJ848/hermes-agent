# metacognitive-calibration-learning-2026

*Researched: 2026-04-05 23:58 CDT*

# Metacognitive Calibration & Self-Aware Learning: SOTA 2025-2026

## Uncertainty Estimation
- **Semantic Entropy** (Farquhar, Nature 2024): cluster semantically equivalent generations, measure entropy over meaning clusters. Far more reliable than token-level entropy.
- **Conformal Prediction**: distribution-free coverage guarantees. Works for any black-box LLM.
- **Self-Consistency**: N diverse paths → agreement = high confidence
- Architecture: LLM output → Semantic Entropy + Conformal Predictor → Uncertainty Aggregator → Knowledge Gap Router (RAG/Tool/Defer/Direct)

## Active Inference & Epistemic Foraging
- Friston: maximize pragmatic_value + epistemic_value - cost
- Epistemic value = expected information gain = H[B_t] - E[H[B_{t+1}]]
- **Curiosity-driven retrieval**: intrinsic motivation via prediction error
- **Bounded foraging**: meta-controller decides if further info gathering is worth the cost
- Key papers: Tschantz (NeurIPS 2024), Jain (ICML 2025), Wang (ACL 2025)

## Calibration Techniques
1. **Temperature scaling** — still effective, single parameter T
2. **Conformal prediction** — prediction sets with coverage guarantees
3. **Self-consistency calibration** — agreement among N samples
4. **Verbalized confidence** — poorly calibrated raw, needs fine-tuning
5. **Reward model calibration** — score agent outputs, calibrate the scorer itself

## Meta-Learning for Rapid Adaptation
- **LoRA-based MAML** — sparse gradient updates for billion-param models
- **In-context learning as meta-learning** — ICL implicitly implements gradient descent
- **Compositional priors** — adaptation = composing known primitives in novel ways

## Actionable for Evey's learning Domain (cal=0.32, weakest)
1. Build uncertainty estimator: semantic entropy over multiple generations
2. Wire epistemic foraging into task selection: pick domains where EIG is highest
3. Add conformal prediction to confidence scores in domain_calibration table
4. Track prediction accuracy per domain — when accuracy < 60%, increase exploration
5. Meta-learning: store successful reasoning patterns as composable "skills"


## Sources

- Farquhar et al. Nature 2024
- Friston MIT Press 2022
- Jain ICML 2025
