# siggraph-2025-hybrid-realtime-sss

*Researched: 2026-04-06 00:52 CDT*

# SIGGRAPH 2025: Hybrid Real-Time Subsurface Scattering

**Source:** SIGGRAPH 2025 "Advances in Real-Time Rendering in Games" (celebrating 20th anniversary)

## Key Innovation
NVIDIA introduced a **hybrid real-time subsurface scattering (SSS) technique** that combines:
- **Volumetric path tracing** via ReSTIR (Reservoir-based Spatiotemporal Importance Resampling)
- **Physically-based diffusion approximation**

This hybrid approach approaches path-traced quality while maintaining real-time performance — a breakthrough for skin, wax, marble, and organic tissue rendering.

## Technical Approach
- Traditional real-time SSS relies on diffusion approximations (Gaussian sum models, screen-space blur)
- The new method uses ReSTIR to sample volumetric light paths for subsurface transport
- Combines stochastic path sampling with analytical diffusion for performance
- Claims significantly closer ground-truth matching vs. prior methods

## SOMA Relevance
- **Directly applicable** to SOMA's 3D anatomy viewer for realistic tissue rendering
- Current soma-sss-shaders skill uses screen-space Gaussian approximation
- This hybrid technique could be implemented in WebGPU compute shaders
- Skin and organ tissue are the primary use cases — exactly what anatomy visualization needs
- Mobile feasibility depends on ReSTIR compute cost (likely needs desktop-grade GPU)

## Implementation Path
1. Study the paper (PDF available at advances.realtimerendering.com)
2. Evaluate ReSTIR compute requirements for mobile WebGPU
3. If too heavy for mobile, use the improved diffusion model as a fallback
4. The technique could be offered as a quality tier: high (hybrid) vs. medium (improved diffusion)

## References
- Paper PDF: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- ACM DOI: https://dl.acm.org/doi/10.1145/3721241.3744991
- YouTube talk: https://www.youtube.com/watch?v=AtFBbMnUgoc
- GPU Gems 3 Ch.14 (foundational SSS): https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin

## Sources

- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://dl.acm.org/doi/10.1145/3721241.3744991
- https://www.youtube.com/watch?v=AtFBbMnUgoc
