# subsurface-scattering-references-collection

*Researched: 2026-04-05 18:55 CDT*

# Subsurface Scattering Reference Collection

**Source:** [Jaysmito101/AdvancedVulkanDemos](https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md)

Curated list of real-time SSS techniques applicable to medical anatomy rendering:

## Key Techniques for SOMA

1. **Separable Subsurface Scattering** (Jimenez et al.) — The industry standard for real-time skin. Uses a 2D Gaussian blur in screen space. Most practical for WebGL/WebGPU.
   - Paper: https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf

2. **Approximating Translucency** (Barre-Brisebois, GDC 2011) — Fast, cheap SSS approximation. Best for mobile/WebGL where full SSS is too expensive. Wraps light around objects using a modified wrap-lighting model.
   - Slides: https://www.slideshare.net/slideshow/colin-barrebrisebois-gdc-2011-approximating-translucency-for-a-fast-cheap-and-convincing-subsurfacescattering-look-7170855/7170855

3. **GPU Gems Ch.16** — Real-time approximations using depth maps and texture-space blur. Good baseline approach.
   - https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering

4. **GPU Gems 3 Ch.14** — Advanced skin rendering techniques. Uses texture-space diffusion with irradiance maps.
   - https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin

5. **Disney BSDF with Integrated SSS** (Burley 2015) — Extends Disney BRDF to include subsurface scattering. Physically grounded, good reference implementation.
   - https://blog.selfshadow.com/publications/s2015-shading-course/burley/s2015_pbs_disney_bsdf_slides.pdf

6. **MJP's SSS Introduction** — Practical tutorial on implementing SSS in a real-time renderer.
   - https://therealmjp.github.io/posts/sss-intro/

## SIGGRAPH 2025: Real-Time Subsurface Scattering
- Latest advances talk: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Covers hybrid ReSTIR path tracing + diffusion for real-time SSS

## SOMA Implementation Priority
For mobile WebGL (Three.js):
1. Start with **Approximating Translucency** (wrap lighting) — cheapest, good enough for organs
2. Upgrade to **Separable SSS** for skin close-ups — post-process blur approach
3. Consider WebGPU compute shaders for full diffusion simulation (future)

## Skin Textures
- Free skin texture data: https://github.com/Vulpinii/skin-texture/tree/master


## Sources

- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
