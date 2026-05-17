# real-time-sss-anatomy-rendering

*Researched: 2026-04-05 04:26 CDT*

# Real-Time Subsurface Scattering for Anatomy Rendering

## SIGGRAPH 2025: Hybrid ReSTIR Path Tracing + Diffusion

NVIDIA unveiled a **hybrid real-time SSS technique** combining:
1. **Volumetric path tracing** for accurate light transport inside tissue
2. **New physically-based diffusion approximation** for real-time performance
3. Uses **ReSTIR** (Reservoir-based Spatiotemporal Importance Resampling) for efficient path reuse

## Core SSS Concepts for Anatomy

### When SSS Matters
- Standard diffuse BRDF (Lambertian) assumes scattered light exits within the same pixel
- **Translucent materials** (skin, organs, tissue) scatter light beyond pixel footprint
- Must consider lighting from neighboring pixels — global diffusion problem

### Real-Time Approaches (Ranked by Quality/Cost)

1. **Screen-Space Diffusion** (fastest, game-quality)
   - Render lighting normally, then blur in screen space using Gaussian kernels
   - Separate blur passes for R, G, B channels with different widths (skin: R scatters most)
   - Typically 6 Gaussian passes (2 per channel) — Jimenez et al. 2015
   - Works well for skin but limited for deep tissue translucency

2. **Texture-Space Diffusion** (medium cost, film-quality)
   - Unwrap mesh UVs, render to texture, then blur in texture space
   - More accurate than screen-space but requires UV unwrap
   - Used in original GPU Gems 3 skin rendering

3. **Pre-Integrated Skin Shading** (fastest)
   - Penner & Borshukov 2011: Pre-compute scattering lookup textures
   - No blur passes needed — just texture lookups
   - Good for mobile/WebGPU where compute budget is tight
   - **Best option for SOMA mobile renderer**

4. **Hybrid Path Tracing** (highest quality, SIGGRAPH 2025)
   - ReSTIR + diffusion approximation
   - Requires RT cores — not available in WebGPU yet
   - Future option when WebGPU ray tracing lands

### SOMA Implementation Recommendation
For mobile 3D anatomy (Three.js/WebGPU):
- **Start with Pre-Integrated Skin Shading** — zero blur cost, texture lookups only
- Create lookup textures for different tissue types (skin, muscle, organ, bone)
- Tissue-specific scattering parameters (mean free path, absorption coefficients)
- Later upgrade to screen-space diffusion when compute budget allows

### Key Parameters by Tissue Type
| Tissue | Scattering Width | Red Absorption | Blue Absorption | Translucency |
|--------|-----------------|----------------|-----------------|-------------|
| Skin | Medium | Low (red passes through) | High | 0.3-0.5 |
| Muscle | High | Medium | High | 0.4-0.6 |
| Liver | High | High | Very High | 0.2-0.3 |
| Bone | Very Low | Low | Low | 0.05-0.1 |
| Cartilage | Medium | Medium | Medium | 0.3-0.4 |


## Sources

- https://therealmjp.github.io/posts/sss-intro/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
