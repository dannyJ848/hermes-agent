# siggraph-2025-hybrid-sss-realtimerendering

*Researched: 2026-04-06 00:13 CDT*

# SIGGRAPH 2025: Hybrid Real-Time Subsurface Scattering

**Source:** SIGGRAPH 2025 Advances in Real-Time Rendering course (20th anniversary)

## Key Discovery
NVIDIA unveiled a **hybrid real-time subsurface scattering technique** that combines:
1. **Volumetric path tracing** (ReSTIR-based)
2. **Physically-based diffusion approximation**

This is presented as a novel approach — previous SSS methods used either screen-space diffusion (fast but inaccurate) or full volumetric path tracing (accurate but slow). The hybrid approach gets quality close to offline rendering at real-time rates.

## Relevance to SOMA
- Directly applicable to our 3D anatomy viewer's skin/tissue rendering
- Current SOMA SSS implementation uses screen-space Gaussian approximation (fast but limited)
- This hybrid technique could provide realistic tissue translucency (ears, fingers, organs)
- ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) is the key enabling algorithm

## Technical Details
- Uses ReSTIR for path reuse across frames (massive variance reduction)
- Combines with diffusion theory for multi-scatter approximation
- Targets real-time performance on modern GPUs (RTX 4070+ class)
- Part of the "Advances in Real-Time Rendering in Games" course at SIGGRAPH 2025

## Action Items for SOMA
1. Study the ReSTIR algorithm for potential WebGPU compute shader adaptation
2. Evaluate if diffusion approximation alone (without path tracing) provides sufficient quality for mobile
3. Consider a tiered approach: simple diffusion on mobile, hybrid on desktop
4. The PDF slides are at: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
5. YouTube talk: https://www.youtube.com/watch?v=AtFBbMnUgoc

## Tags
#3d-rendering #subsurface-scattering #siggraph2025 #webgpu #soma #medical-rendering #nvidia

## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
- https://www.youtube.com/watch?v=AtFBbMnUgoc
