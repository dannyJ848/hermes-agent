# real-time-subsurface-scattering-anatomy-2025

*Researched: 2026-04-05 22:10 CDT*

# Real-Time Subsurface Scattering for Anatomy Rendering (2025)

## SIGGRAPH 2025 Advances
- **Hybrid RESTIR-Path Tracing + Diffusion**: Novel real-time SSS approach combining ReSTIR path tracing with diffusion approximation. Presented at SIGGRAPH 2025 "Advances in Real-Time Rendering" course.
- Key insight: Separable SSS (Jimenez et al.) remains the practical baseline for real-time, but hybrid approaches are closing the quality gap with offline rendering.

## Practical SSS Pipeline for WebGPU/Three.js (Relevant to SOMA)

### Tier 1: Cheap & Convincing (Mobile-Friendly)
- **Approximating Translucency** (Barre-Brisebois, GDC 2011): Wrap lighting + thickness map. ~5 shader instructions. Ideal for mobile anatomy models.
- **Implementation**: `scatter = max(0, dot(N, -L) + wrap) / (1 + wrap)` where wrap ~0.5 for skin-like tissue.

### Tier 2: Screen-Space Separable SSS
- **Separable Subsurface Scattering** (Jimenez et al.): Gaussian kernel decomposed into 2 1D passes. GPU Gems 3 Chapter 14.
- Requires: depth buffer, albedo, normal map, thickness map.
- Profile kernels for skin, fat, muscle tissue — each has different scattering radii.
- **WebGPU compatibility**: Compute shaders make separable blur trivial. No need for ping-pong render targets.

### Tier 3: BSSRDF Path Tracing (Research/Offline)
- Disney BSDF extension with integrated SSS (Burley 2015).
- Quantized-diffusion model (d'Eon & Irving) — more accurate than dipole.
- PBRT 3 Chapter on BSSRDF — reference implementation.

## SOMA-Specific Recommendations
1. **Start with Tier 1** (wrap lighting + thickness) for all tissue types. Zero performance cost.
2. **Add Tier 2** for close-up organ views where subsurface scattering is visible (skin, liver, heart walls).
3. **Thickness maps**: Generate from mesh via AO bake or ray-marching during asset pipeline.
4. **Tissue-specific profiles**: Different scattering radius per tissue type (skin=thin, muscle=medium, fat=diffuse, bone=none).
5. **WebGPU migration**: When moving from WebGL → WebGPU, replace fragment-shater blur with compute-shader dispatch for SSS passes.

## Key References
- SIGGRAPH 2025 SSS Advances: `advances.realtimerendering.com/s2025/sss-siggraph-2025-advances-published.pdf`
- Separable SSS: `iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf`
- GPU Gems 3 Ch14: `developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin`
- MJP Introduction: `therealmjp.github.io/posts/sss-intro/`
- Disney BSDF: `blog.selfshadow.com/publications/s2015-shading-course/burley/s2015_pbs_disney_bsdf_slides.pdf`


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
