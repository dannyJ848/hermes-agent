# SIGGRAPH-2025-Real-Time-SSS-ReSTIR

*Researched: 2026-04-06 13:49 CDT*

# SIGGRAPH 2025: Real-Time Subsurface Scattering via Hybrid ReSTIR Path Tracing & Diffusion

**Source:** SIGGRAPH 2025 Advances in Real-Time Rendering in Games (Part II), presented by Tanki Zhang (NVIDIA)

**Date:** August 12, 2025

## Key Innovation
A hybrid approach combining **ReSTIR (Reservoir-based Spatiotemporal Importance Resampling)** path tracing with traditional **diffusion approximation** for real-time subsurface scattering.

## Problem it Solves
Traditional real-time SSS relies on diffusion approximations (screen-space blur, texture-space diffusion) which fail to capture accurate transmission and scattering through thin translucent materials. Full path-traced SSS is too expensive for real-time.

## Hybrid Method
- **ReSTIR for path sampling:** Uses resampled importance sampling to efficiently find light paths through translucent volumes
- **Diffusion for fast close scattering:** Falls back to diffusion approximation for short-range scattering where it's accurate and cheap
- **Sequential shifting strategies:** Improves denoising quality and overall rendering

## Relevance to SOMA
SOMA's 3D anatomy viewer uses WGSL subsurface scattering shaders for realistic skin, organ, and tissue rendering. Key takeaways:

1. **Hybrid is the answer** — pure diffusion OR pure path tracing isn't optimal; combine them
2. **ReSTIR pattern** — reservoir-based importance resampling can be adapted to WebGPU compute shaders
3. **Sequential shifting** — reusing samples across frames/spatial neighbors improves quality without extra cost
4. **Production-proven** — this is from NVIDIA, shipping in games (meaning it's performant enough for real-time)

## Implementation Path for SOMA
- Current SOMA SSS: screen-space Gaussian blur approximation in WGSL
- Next step: Add spatial sample reuse (simple ReSTIR-like pattern) in compute pass
- Future: Full hybrid with diffusion for short-range + resampled path tracing for transmission

## Related Talks at Same Session
- MegaLights (Epic Games) — stochastic direct lighting in UE5
- idTech8 GI (id Software) — global illumination
- Strand-based hair/fur (MachineGames) — relevant for SOMA hair rendering

## ACM Paper
"ReSTIR Subsurface Scattering for Real-Time Path Tracing" — ACM DOI: 10.1145/3675372


## Sources

- https://advances.realtimerendering.com/s2025/
- https://dl.acm.org/doi/abs/10.1145/3675372
- https://www.youtube.com/watch?v=AtFBbMnUgoc
