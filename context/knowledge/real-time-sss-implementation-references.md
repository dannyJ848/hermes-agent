# real-time-sss-implementation-references

*Researched: 2026-04-06 03:53 CDT*

# Real-Time Subsurface Scattering: Implementation References for SOMA

## Key Resources (Curated 2026-04-06)

### SIGGRAPH 2025 — State of the Art
- **"Real-Time Subsurface Scattering"** (SIGGRAPH 2025 Advances course)
  - Source: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
  - Introduces **hybrid ReSTIR-Path Tracing + Diffusion** for real-time SSS
  - This is the cutting edge — combines Monte Carlo sampling with analytic diffusion approximation

### Practical Implementation References
1. **Separable SSS** (Jimenez et al.) — The gold standard for real-time
   - Paper: https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
   - 2-pass Gaussian blur approximation, runs at 60fps on modern GPUs
   - **Best starting point for SOMA** — well-documented, proven in production games

2. **Approximating Translucency** (GDC 2011, Colin Barre-Brisebois)
   - Slides: https://www.slideshare.net/slideshow/colin-barrebrisebois-gdc-2011-approximating-translucency-for-a-fast-cheap-and-convincing-subsurfacescattering-look-7170855/7170855
   - Cheap wrap-lighting + thickness-based translucency
   - **Lowest complexity** — good for mobile/WebGPU fallback

3. **GPU Gems Ch.16** — Real-Time Approximations to SSS
   - https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
   - Texture-based and lighting-based approximations
   - Well-suited for tissue rendering at varying LOD

4. **GPU Gems 3 Ch.14** — Advanced Realistic Skin Rendering
   - https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
   - Multi-layer skin model (epidermis + dermis + subcutaneous)
   - Directly applicable to SOMA's anatomy visualization

### Open Source Implementations
- **AdvancedVulkanDemos** — Vulkan SSS demo with skin textures
  - https://github.com/Jaysmito101/AdvancedVulkanDemos
  - Skin textures: https://github.com/Vulpinii/skin-texture

## SOMA Integration Strategy
1. **Tier 1 (mobile/low-end):** Wrap-lighting translucency approximation
2. **Tier 2 (desktop/WebGPU):** Separable SSS with 2-pass Gaussian
3. **Tier 3 (future):** Hybrid ReSTIR path-tracing from SIGGRAPH 2025

### Key Parameters for Anatomy Tissue
- **Skin/epidermis:** Low scattering radius (0.5-2mm), reddish tint
- **Muscle tissue:** Medium scattering (2-5mm), deep red
- **Organ tissue (liver, kidney):** High scattering (3-8mm), brownish-red
- **Fat/adipose:** High forward scattering, yellowish tint
- **Cartilage:** Moderate scattering, bluish-white


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
