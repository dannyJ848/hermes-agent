# nvidia-restir-subsurface-scattering-2025

*Researched: 2026-04-06 12:41 CDT*

# NVIDIA ReSTIR Subsurface Scattering — SIGGRAPH 2025

## Summary
NVIDIA presented a novel hybrid real-time subsurface scattering technique at SIGGRAPH 2025 (Advances in Real-Time Rendering course). The approach combines **volumetric path tracing via ReSTIR** with **physically-based diffusion approximation** for real-time SSS rendering.

## Key Technical Details

### Hybrid Approach
- **Path tracing component:** Uses ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) to sample volumetric light paths inside translucent materials
- **Diffusion component:** Fast analytical diffusion approximation for multi-scattered light
- **Key insight:** Tracing limited bounces is much cheaper than unknown bounce counts, while diffusion evaluation remains very fast. Hybrid = best of both worlds

### Why This Matters for SOMA
1. **Skin rendering:** Human anatomy requires realistic skin SSS — blood vessels, fat layers, cartilage all scatter light differently. This technique could enable photorealistic tissue rendering.
2. **WebGPU feasibility:** ReSTIR is a sampling strategy, not hardware-specific. The diffusion component is essentially a shader computation. Both could be implemented in WebGPU compute shaders.
3. **Performance:** The "limited bounces + diffusion" split means we can control quality vs. performance by adjusting the bounce budget — critical for mobile where GPU budget is tight.

### SOMA Integration Path
1. **Phase 1:** Implement screen-space diffusion approximation (fast, approximate) in WGSL shader
2. **Phase 2:** Add ReSTIR-style importance sampling for key materials (skin, organ tissue)
3. **Phase 3:** Parameterize by tissue type — different scattering coefficients for skin, muscle, bone, organ tissue

### Comparison to Current SOMA SSS Skill
The existing `soma-sss-shaders` skill covers screen-space SSS. This NVIDIA technique adds:
- Physically accurate volumetric path tracing (not just screen-space blur)
- ReSTIR resampling for noise reduction (much better than naive MC)
- Hybrid approach maintains real-time performance

## Sources
- SIGGRAPH 2025 Advances in Real-Time Rendering course
- ACM DOI: 10.1145/3675372 (paywalled)
- Video: https://www.youtube.com/watch?v=AtFBbMnUgoc
- PDF slides: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf

## Date Discovered
2026-04-06


## Sources

- https://dl.acm.org/doi/abs/10.1145/3675372
- https://www.youtube.com/watch?v=AtFBbMnUgoc
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
