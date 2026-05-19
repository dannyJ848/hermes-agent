# real-time-subsurface-scattering-siggraph-2025

*Researched: 2026-04-06 13:05 CDT*

# Real-Time Subsurface Scattering — SIGGRAPH 2025 Advances & Techniques

## Key Discovery (April 2026)
SIGGRAPH 2025 "Advances in Real-Time Rendering" course includes a **dedicated SSS session** with novel hybrid ReSTIR-Path Tracing + Diffusion approach for real-time subsurface scattering.

## Hybrid ReSTIR-Path Tracing + Diffusion (SIGGRAPH 2025)
- Novel hybrid solution combining ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) with path tracing and diffusion approximation
- Enables real-time SSS without precomputation of diffusion profiles
- Relevant to SOMA: could replace our current screen-space SSS approximation with higher-quality real-time tissue rendering
- Video: https://www.youtube.com/watch?v=AtFBbMnUgoc
- Course materials: https://advances.realtimerendering.com/s2025/

## SOMA Applicability
For 3D anatomy rendering (WebGPU/Three.js), the key SSS techniques ranked by mobile feasibility:

### Tier 1 — Mobile-friendly (implement now)
1. **Screen-space SSS (Separable)** — 2-pass Gaussian blur in screen space. Cheap, looks decent.
   - Paper: https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
2. **Wrap lighting + thickness approximation** — Fake translucency with wrapped diffuse + thickness map.
   - GDC 2011: https://www.slideshare.net/slideshow/colin-barrebrisebois-gdc-2011-approximating-translucency-for-a-fast-cheap-and-convincing-subsurfacescattering-look-7170855/7170855

### Tier 2 — WebGPU compute shaders (future)
3. **BSSRDF diffusion profile** — Preintegrated diffusion per skin tone. Needs compute.
   - Disney BSDF extension: https://blog.selfshadow.com/publications/s2015-shading-course/burley/s2015_pbs_disney_bsdf_slides.pdf
4. **Quantized diffusion** — More accurate than Gaussian, less expensive than full BSSRDF.
   - Paper: "A Quantized-Diffusion Model for Rendering Translucent Materials"

### Tier 3 — Desktop/ray-tracing only
5. **ReSTIR-PT + Diffusion hybrid** (SIGGRAPH 2025) — Needs RT cores. Not mobile-viable yet.

## Key Reference Compendium (from Jaysmito101/AdvancedVulkanDemos)
- GPU Gems Ch.16: Real-Time Approximations to SSS — https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- GPU Gems3 Ch.14: Advanced Skin Rendering — https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- MJP SSS Introduction — https://therealmjp.github.io/posts/sss-intro/
- PBRT BSSRDF chapter — https://pbr-book.org/3ed-2018/Volume_Scattering/The_BSSRDF
- Wikipedia overview — https://en.wikipedia.org/wiki/Subsurface_scattering

## Action Items for SOMA
1. Implement Tier 1 wrap lighting as a WGSL shader (cheapest SSS look)
2. Add thickness maps to anatomy models for translucency
3. Profile screen-space SSS on iOS Safari WebGPU
4. Track ReSTIR-PT hybrid for future WebGPU ray-tracing support


## Sources

- https://advances.realtimerendering.com/s2025/
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://www.youtube.com/watch?v=AtFBbMnUgoc
- https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
