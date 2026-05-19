# SIGGRAPH-2025-hybrid-SSS-ReSTIR

*Researched: 2026-04-06 15:22 CDT*

# SIGGRAPH 2025: Hybrid ReSTIR Path Tracing + Diffusion for Real-Time Subsurface Scattering

**Source:** NVIDIA (Tanki Zhang), Advances in Real-Time Rendering in Games, SIGGRAPH 2025
**Date:** August 2025
**Relevance:** Directly applicable to SOMA 3D anatomy rendering (skin, tissue subsurface scattering)

## Key Innovation
NVIDIA introduced a novel hybrid solution for real-time subsurface scattering (SSS) that approaches path-traced quality while running at real-time frame rates. The technique combines:

1. **Volumetric Path Tracing** via ReSTIR (Reservoir-based Spatiotemporal Importance Resampling)
2. **New Physically-Based Diffusion Approximation** for multi-scattering

Traditional real-time SSS relies on diffusion approximations (screen-space blur, dipole/bipole models), but these fail for thin geometry and complex scattering. This hybrid approach resolves that.

## Technical Approach (inferred from talk description)
- Uses ReSTIR to sample volumetric light paths inside translucent materials
- Falls back to diffusion approximation where path tracing converges slowly (deep scattering)
- Physically based: respects actual scattering coefficients (σ_s, σ_a) rather than artistic approximations
- Targets current-generation GPU pipelines (RTX-level hardware)

## Application to SOMA
- **Skin rendering:** Human skin is the classic SSS challenge. This technique would make SOMA's anatomy models look dramatically more realistic with proper light transmission through ears, fingers, and thin tissue.
- **Organ visualization:** Internal organs with translucency (liver, kidneys, brain tissue) would benefit from physically accurate scattering.
- **WebGPU feasibility:** While ReSTIR requires ray tracing hardware, the diffusion component could be adapted for WebGPU compute shaders. The hybrid nature means we could use the diffusion path on mobile and the full hybrid on desktop RTX.
- **Integration point:** SOMA's `soma-sss-shaders` skill already covers SSS basics. This finding should inform a future skill update with ReSTIR-inspired importance sampling.

## Performance Targets
- Real-time (implied 30+ FPS based on "games" context)
- Requires RT-capable GPU for full quality
- Diffusion-only fallback feasible on non-RT hardware

## Related Work
- i3D 2024: "ReSTIR Subsurface Scattering for Real-Time Path Tracing" (ACM DOI: 10.1145/3675372)
- Same author group, earlier publication of the core algorithm

## Action Items for SOMA
1. Study the ReSTIR-SSS paper from i3D 2024 (more accessible than SIGGRAPH slides)
2. Evaluate WebGPU compute shader feasibility for the diffusion component
3. Consider LOD approach: diffusion-only on mobile, hybrid on desktop
4. Update `soma-sss-shaders` skill with hybrid approach architecture

## Sources

- https://advances.realtimerendering.com/s2025/
- https://dl.acm.org/doi/abs/10.1145/3675372
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
