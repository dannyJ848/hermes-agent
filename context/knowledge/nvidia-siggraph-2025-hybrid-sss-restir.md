# nvidia-siggraph-2025-hybrid-sss-reSTIR

*Researched: 2026-04-05 22:14 CDT*

# NVIDIA SIGGRAPH 2025: Hybrid Real-Time Subsurface Scattering via ReSTIR-Path Tracing & Diffusion

**Source:** SIGGRAPH 2025 Advances in Real-Time Rendering in Games (20th anniversary session)
**Presented by:** NVIDIA
**Key paper:** "RT Subsurface Scattering via Hybrid ReSTIR-Path Tracing & Diffusion"
**ACM DOI:** 10.1145/3721241.3744991

## Core Innovation

NVIDIA introduced a **hybrid real-time SSS technique** that combines:

1. **Volumetric Path Tracing** — Uses ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) for stochastic light transport through translucent materials
2. **Physically-Based Diffusion Approximation** — Classical dipole/multipole diffusion profiles for broad subsurface scatter

The hybrid approach approaches **path-traced quality** while maintaining real-time frame rates.

## Why This Matters for SOMA

### Current SOMA SSS Approach
SOMA's `soma-sss-shaders` skill uses screen-space Gaussian approximations for subsurface scattering on anatomical tissue. This is fast but physically inaccurate — it doesn't account for light transport through varying tissue densities (fat, muscle, bone proximity).

### Potential Upgrade Path
- **WebGPU compatibility**: ReSTIR is a sampling strategy, not API-specific. The core algorithm can be implemented in WebGPU compute shaders.
- **Tissue-specific scattering**: Different anatomical tissue layers have different scattering coefficients (epidermis vs dermis vs subcutaneous fat). The hybrid approach could allow per-region parameterization.
- **Quality leap**: Current screen-space approximations miss light transmission through thin tissue (ears, fingers, nasal cartilage). Volumetric path tracing captures this naturally.

### Implementation Considerations
- **Performance**: ReSTIR requires reservoir-based temporal reuse — needs persistent GPU memory for sample history. On mobile, this means careful budget management.
- **Fallback path**: Must maintain screen-space Gaussian fallback for devices without adequate compute shader support.
- **Pre-integration**: For anatomy (non-deforming), could pre-compute scattering profiles per body region, reducing runtime cost.

## Technical Details (from search context)
- Traditional real-time SSS relies on **diffusion approximations** (dipole/multipole models from GPU Gems 3, Chapter 14)
- NVIDIA's new method captures "significantly more detail with much closer ground truth matching"
- Combines the broad diffusion profile (cheap, handles large scatter radius) with targeted path tracing (expensive, handles edge cases like thin geometry)
- Part of SIGGRAPH 2025 "Advances in Real-Time Rendering" which celebrated its 20th year

## Action Items for SOMA
1. Monitor for published source code / shader reference implementations
2. Evaluate WebGPU compute shader support for reservoir sampling on iOS Safari
3. Prototype: Implement a simplified 2-reservoir ReSTIR for single-scatter SSS
4. Benchmark: Compare current Gaussian SSS vs simplified ReSTIR on iPhone 15+ GPU

## Sources
- SIGGRAPH 2025 session: https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
- Paper PDF: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- ACM DOI: https://dl.acm.org/doi/10.1145/3721241.3744991
- Video: https://www.youtube.com/watch?v=AtFBbMnUgoc
- Classic reference: GPU Gems 3 Ch.14: https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin


## Sources

- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
- https://dl.acm.org/doi/10.1145/3721241.3744991
- https://www.youtube.com/watch?v=AtFBbMnUgoc
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
