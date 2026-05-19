# real-time-subsurface-scattering-references

*Researched: 2026-04-06 20:25 CDT*

# Real-Time Subsurface Scattering (SSS) References for Anatomy Rendering

## Key Discovery: SIGGRAPH 2025 Hybrid Approach
SIGGRAPH 2025 Advances in Real-Time Rendering introduced a **hybrid ReSTIR-Path Tracing & Diffusion** approach for real-time SSS. This combines Monte Carlo path sampling with analytical diffusion profiles, potentially achieving photorealistic skin/organ translucency at interactive rates.

## WebGPU Applicability for SOMA
The most relevant techniques for WebGPU-based anatomy rendering:

### Tier 1: Screen-Space Methods (Fastest, Good Quality)
- **Separable SSS** (Jimenez et al.): 2-pass Gaussian blur in screen space. Best performance-to-quality ratio.
  - PDF: https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
- **Efficient Screen-Space SSS using Burley's Normalized Diffusion** (SIGGRAPH 2018): More physically accurate than separable, similar cost.
  - PDF: https://advances.realtimerendering.com/s2018/Efficient%20screen%20space%20subsurface%20scattering%20Siggraph%202018.pdf
- **12-Tap Blur Approximation** (Shader X7, p.30): Ultra-fast approximation, suitable for mobile.

### Tier 2: Pre-Integrated Methods (Best for Mobile)
- **Approximating Translucency** (GDC 2011, Barre-Brisebois): Cheap wrap lighting + thickness map. Ideal for iOS/WebGPU.
  - Slides: https://www.slideshare.net/slideshow/colin-barrebrisebois-gdc-2011-approximating-translucency-for-a-fast-cheap-and-convincing-subsurfacescattering-look-7170855/7170855
- **Real-Time Realistic Skin Translucency** (Iryoku): Uses transmittance maps.
  - PDF: https://www.iryoku.com/translucency/downloads/Real-Time-Realistic-Skin-Translucency.pdf

### Tier 3: Path Tracing (Future - WebGPU Compute)
- **ReSTIR-Path Tracing + Diffusion hybrid** (SIGGRAPH 2025): State of the art. Requires compute shaders — possible in WebGPU.
  - Video: https://www.youtube.com/watch?v=AtFBbMnUgoc
  - Course: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf

## SOMA Implementation Recommendation
For SOMA's WebGPU anatomy viewer, start with **Tier 2 (Approximating Translucency)**:
1. Add a thickness map per anatomical model
2. Use wrap diffuse lighting + back-light transmittance
3. Tune per-organ scattering radius (skin thin, organs medium, bone opaque)
4. Graduation path: Tier 1 screen-space SSS for desktop, Tier 2 for mobile

## Reference Collections
- Jaysmito101 SSS resource list: https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- MJP's SSS Introduction: https://therealmjp.github.io/posts/sss-intro/
- Disney BSDF with SSS: https://blog.selfshadow.com/publications/s2015-shading-course/burley/s2015_pbs_disney_bsdf_slides.pdf


## Sources

- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
