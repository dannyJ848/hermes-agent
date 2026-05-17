# SIGGRAPH-2025-real-time-SSS

*Researched: 2026-04-06 05:34 CDT*

# SIGGRAPH 2025: Real-Time Subsurface Scattering via Hybrid ReSTIR Path Tracing & Diffusion

## Summary
NVIDIA unveiled a novel hybrid real-time subsurface scattering technique at SIGGRAPH 2025 that combines volumetric path tracing with a new physically-based diffusion approximation. This is the state-of-the-art for real-time SSS.

## Key Technical Details
- **Hybrid approach**: Combines ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) path tracing with diffusion profiles
- **Volumetric path tracing**: Handles direct light transport through translucent media
- **Diffusion approximation**: New physically-based diffusion model for multi-scattered light
- **Real-time capable**: Designed for game frame budgets (~16ms)
- **Applications**: Skin rendering, wax, marble, organic tissues

## Relevance to SOMA
SOMA's 3D anatomy viewer needs realistic tissue rendering. Current approach uses basic SSS shaders. This hybrid technique could:
1. Replace the naive SSS approximation with path-traced accuracy
2. Use WebGPU compute shaders to implement the ReSTIR sampling
3. Apply diffusion profiles per tissue type (skin vs muscle vs organ)
4. Achieve photorealistic translucency on mobile via adaptive quality

## Implementation Path
1. Start with the diffusion profile approach (simpler, already partially in SOMA)
2. Add ReSTIR sampling for specular transmission (requires WebGPU compute)
3. Profile on mobile — may need to fall back to diffusion-only on low-end devices

## Sources
- Paper PDF: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Talk: https://www.youtube.com/watch?v=AtFBbMnUgoc
- SIGGRAPH course: https://advances.realtimerendering.com/s2025/index.html


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://advances.realtimerendering.com/s2025/index.html
- https://www.youtube.com/watch?v=AtFBbMnUgoc
