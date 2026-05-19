# sigmoid-ignition-gwt-architecture

*Researched: 2026-04-04 21:56 CDT*

# Sigmoid Ignition: GWT Phase Transition for Agent Task Switching

## Core Mathematics
```
S(x) = 1 / (1 + e^(-k(x - θ)))
```
- x = aggregated evidence from competing specialist modules
- k = steepness of phase transition (higher = more all-or-nothing)
- θ = ignition threshold (access consciousness gateway)
- S(x) = ignition level in [0,1] — near 0 = unconscious, near 1 = conscious broadcast

## Key Insight: NOT Soft Attention
Sigmoid ignition creates a **nonlinear gate** — an effective "all-or-nothing" broadcast when evidence crosses θ. This is fundamentally different from transformer attention (which is a soft weighted sum). Ignition creates bistable dynamics:
- Below threshold → low-activity state (subconscious)
- Above threshold → avalanche to saturation (conscious broadcast)

## Temporal Dynamics (from Consciousness AI Project)
```python
τ(dx/dt) = -λx + Σ inputs(t) + σ_noise · ξ(t)
ignite(t) = 1 / (1 + exp(-k(x(t) - θ)))
```
- τ = integration time constant
- λ = decay (forgetting)
- σ_noise · ξ(t) = stochastic noise (neural variability)

## Architecture: 7-Layer GWT Agent
1. Specialist Modules (Vision, Memory, Planning, Language, Emotion, Motor) compete for workspace
2. Coalition Formation: compatible modules boost each other's bids
3. Evidence Accumulation: temporal integration with decay and noise
4. Sigmoid Ignition: phase transition gate
5. Global Broadcast: winner's content distributed to ALL modules
6. Adaptive Threshold: homeostatic adjustment (dθ/dt = α(observed_rate - target_rate))
7. Post-ignition Refraction: prevents rapid re-ignition

## Implementation for SOMA Agent
- Use SpecialistModule class with compute_bid() returning activation
- GlobalWorkspace with accumulate_evidence() + evaluate_ignition()
- AdaptiveWorkspace extends with homeostatic threshold adaptation
- GWTAgent orchestrates full cycle: stimuli → bids → coalitions → ignition → broadcast → task switch

## Full Python implementation saved in subconscious/gwt_agent.py (to be created)
## Reference: theconsciousness.ai v1.1.0, Nakanishi et al. Frontiers in Robotics & AI 2025

## Sources

- theconsciousness.ai
- Frontiers in Robotics & AI DOI:10.3389/frobt.2025.1607190
- Feinberg & Mallatt MIT Press 2016
