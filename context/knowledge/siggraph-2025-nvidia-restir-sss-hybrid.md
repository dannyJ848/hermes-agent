# siggraph-2025-nvidia-restir-sss-hybrid

*Researched: 2026-04-05 23:10 CDT*

# SIGGRAPH 2025: NVIDIA Real-Time Subsurface Scattering via Hybrid ReSTIR Path-Tracing & Diffusion

**Source:** SIGGRAPH 2025 Advances in Real-Time Rendering in Games (20th anniversary year)
**Presenter:** Tanki Zhang (NVIDIA)
**Date:** August 12, 2025, Vancouver

## Key Innovation
A novel **hybrid approach** combining:
1. **ReSTIR (Reservoir-based Spatiotemporal Importance Resampling)** — for path-traced SSS sampling
2. **Diffusion profiles** — traditional screen-space SSS approximation for real-time performance

The approach claims to approach **path-traced quality** at real-time frame rates.

## Technical Context
- Traditional real-time SSS uses **screen-space diffusion profiles** — fast but inaccurate for complex geometry
- ReSTIR enables efficient reuse of light samples across pixels and frames (spatiotemporal resampling)
- Hybrid approach: use diffusion profiles where they work well (flat surfaces), switch to ReSTIR path tracing for complex geometry (ears, fingers, noses)
- Monte Carlo simulation measures outgoing light vs distance from entry point, producing diffuse reflectance profile R(r) for given materials

## SOMA Relevance
- **Tissue-specific profiles**: Different tissue types (skin, muscle, organ) have different scattering parameters — this technique could provide per-organ SSS profiles
- **WebGPU compatibility**: ReSTIR is GPU-friendly and could be adapted for WebGPU compute shaders
- **Mobile considerations**: Need to evaluate performance on mobile GPUs — ReSTIR may be too expensive; fallback to diffusion profiles only
- **Integration path**: Three.js r171+ WebGPU renderer + TSL shaders + custom ReSTIR compute pass

## Related Work at Same Session
- **MegaLights** (Epic Games) — stochastic direct lighting in UE5, relevant for multi-light anatomy scenes
- **idTech8 GI** (id Software) — global illumination approaches
- **Adaptive Voxel-Based OIT** (Activision) — order-independent transparency for layered tissue

## ACM Paper Reference
"ReSTIR Subsurface Scattering for Real-Time Path Tracing" — DOI: 10.1145/3675372

## Next Steps for SOMA
1. Study the ReSTIR SSS paper implementation details when available
2. Evaluate if a simplified version works on mobile WebGPU
3. Create tissue-specific diffusion profiles for: skin, muscle, fat, organ tissue, bone
4. Prototype hybrid approach: diffusion for skin surfaces, path-traced SSS for thin tissue (ears, nose, membranes)


## Sources

- https://advances.realtimerendering.com/s2025/
- https://www.youtube.com/watch?v=AtFBbMnUgoc
- https://dl.acm.org/doi/abs/10.1145/3675372
