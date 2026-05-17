# reSTIR-subsurface-scattering-real-time-2025

*Researched: 2026-04-06 20:10 CDT*

# ReSTIR Subsurface Scattering for Real-Time Path Tracing (SIGGRAPH 2025)

**Date:** 2025 SIGGRAPH Advances in Real-Time Rendering
**Authors:** KIT (Karlsruhe Institute of Technology) + NVIDIA
**Sources:** dl.acm.org/doi/abs/10.1145/3675372, advances.realtimerendering.com/s2025

## Key Innovation
A hybrid approach combining **ReSTIR path tracing** with **diffusion profile approximation** for real-time subsurface scattering. Previous SSS methods relied on screen-space post-processing (blur-based diffusion profiles) or texture-space convolution — both with known limitations (screen boundaries, no back-scattering, no volumetric accuracy).

## Technique Summary
1. Uses path tracing with diffusion approximation to overcome screen-space SSS limitations
2. Applies ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) to improve sampling efficiency
3. ReSTIR reduces the noise floor significantly, making path-traced SSS viable at real-time rates
4. Hybrid method: combines volumetric path tracing light transport with physically-based diffusion profiles

## SIGGRAPH 2025 Update (NVIDIA)
NVIDIA presented a further evolution: hybrid real-time SSS that combines volumetric path tracing with a new physically-based diffusion profile technique. This was part of the "Two Decades of Progress in a Frame" session marking 20 years of the Advances course.

## Relevance to SOMA
- **Skin rendering**: Critical for anatomical visualization — skin, muscle tissue, and organs all exhibit strong SSS
- **WebGPU potential**: ReSTIR-style importance resampling could be adapted for WebGPU compute shaders
- **Mobile considerations**: The hybrid approach (part path tracing, part diffusion profile) offers a quality/performance dial — use more diffusion on mobile, more path tracing on desktop
- **Current SOMA SSS skill**: We have a `soma-sss-shaders` skill — this ReSTIR approach could significantly upgrade it

## Implementation Path for SOMA
1. Start with diffusion profile approximation (already in soma-sss-shaders skill)
2. Add ReSTIR resampling in a WebGPU compute pass
3. Use screen-space irradiance buffer as input
4. Blend path-traced samples with diffusion profile based on GPU budget
5. Adaptive quality: detect mobile vs desktop and adjust sample count

## References
- Paper: "ReSTIR Subsurface Scattering for Real-Time Path Tracing" (ACM 2024, doi:10.1145/3675372)
- SIGGRAPH 2025 course: https://advances.realtimerendering.com/s2025/
- KIT PDF: https://cg.ivd.kit.edu/publications/2024/restir-sss/restir-sss.pdf


## Sources

- https://dl.acm.org/doi/abs/10.1145/3675372
- https://advances.realtimerendering.com/s2025/
- https://cg.ivd.kit.edu/publications/2024/restir-sss/restir-sss.pdf
