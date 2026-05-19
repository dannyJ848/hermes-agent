# realtime-sss-rendering-techniques-2025

*Researched: 2026-04-05 23:19 CDT*

# Real-Time Subsurface Scattering Techniques for 3D Anatomy Rendering

## SIGGRAPH 2025 Advances
- **New hybrid approach**: ReSTIR-Path Tracing + Diffusion for real-time SSS (SIGGRAPH 2025 Advances in Real-Time Rendering course)
- Key insight: SSS is volume scattering after surface transmission where light scatters multiple times internally
- PDF: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Video: https://www.youtube.com/watch?v=AtFBbMnUgoc

## Classic SSS Techniques (Still Relevant for WebGPU)
1. **Separable Subsurface Scattering** (Jimenez et al.) — 2-pass blur approach, most practical for real-time
   - Paper: https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
2. **Approximating Translucency** (Barre-Brisebois, GDC 2011) — Fast, cheap, convincing SSS look. Best for mobile/WebGPU where compute is limited
   - Slides: https://www.slideshare.net/slideshow/colin-barrebrisebois-gdc-2011-approximating-translucency-for-a-fast-cheap-and-convincing-subsurfacescattering-look-7170855/7170855
3. **GPU Gems Ch. 16** — Real-time approximations to SSS
   - https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
4. **GPU Gems 3 Ch. 14** — Advanced skin rendering techniques
   - https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin

## Open-Source Reference Implementations
- Jaysmito101/AdvancedVulkanDemos — Vulkan SSS demo with resource links
  - https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- Skin texture data: https://github.com/Vulpinii/skin-texture

## SOMA Application Strategy
For SOMA's anatomy viewer (Three.js/WebGPU):
- **Primary**: Separable SSS (2-pass Gaussian blur in screen space) — works on mobile, well-documented
- **Fallback**: Approximating Translucency (wrap lighting + thickness map) — cheapest option
- **Future**: WebGPU compute shaders could enable ReSTIR-style hybrid approach as browser support matures
- Key parameter: tissue thickness maps (different for skin vs organ tissue vs bone)


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.youtube.com/watch?v=AtFBbMnUgoc
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
