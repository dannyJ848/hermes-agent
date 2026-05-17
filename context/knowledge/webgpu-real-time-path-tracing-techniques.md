# webgpu-real-time-path-tracing-techniques

*Researched: 2026-04-06 05:40 CDT*

# WebGPU Real-Time Path Tracing Techniques (2025)

## Source
James Randall's "Building a Real-Time Path Tracer in WebGPU" — a complete implementation using **WebGPU compute shaders only**, no hardware RT cores, no ML denoisers.

## Key Techniques
1. **Rendering Equation**: Full Monte Carlo integration — fire rays in random directions, average results. No closed-form solution exists for arbitrary scenes.
2. **BVH Acceleration**: Bounding Volume Hierarchy for fast ray-triangle intersection testing.
3. **Monte Carlo Importance Sampling**: Sample directions weighted by the BRDF to reduce variance.
4. **Temporal Accumulation**: Accumulate samples across frames to converge toward ground truth.
5. **Spatial Denoising**: Post-process to smooth noise from under-sampled pixels.
6. **Doom WAD Loader**: Parses original 1993 level geometry into triangle meshes for the path tracer.

## Performance
- 60fps on Mac at default settings
- Resolution scaling critical for performance
- No brute-force physics possible even on high-end GPUs

## Relevance to SOMA
- **SSS Alternative**: Path tracing naturally produces subsurface scattering effects without separate SSS passes — light scatters through translucent geometry automatically.
- **WebGPU Compute Shaders**: Same target as SOMA's rendering pipeline. This proves complex rendering is viable in browser.
- **BVH + Monte Carlo**: Could be applied to anatomical models for realistic tissue lighting without pre-baked SSS.
- **Temporal Accumulation**: Perfect for interactive anatomy viewer where camera is relatively still — accumulate quality over frames.

## SIGGRAPH 2025 Advances
- Real-time SSS via hybrid ReSTIR-Path Tracing & Diffusion (NVIDIA talk)
- Order-independent transparency improvements
- Less reliance on pre-computed diffusion profiles

## Actionable for SOMA
1. Consider WebGPU compute shader pipeline for tissue rendering (replacing separate SSS shader)
2. BVH acceleration for anatomy meshes with complex internal geometry
3. Temporal accumulation for quality improvement on still camera views
4. Monitor SIGGRAPH 2025 techniques for browser-feasible adaptations


## Sources

- https://www.jamesdrandall.com/posts/building-a-real-time-path-tracer-in-webgpu/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
