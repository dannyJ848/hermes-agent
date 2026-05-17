# webgpu-subsurface-scattering-realtime-2025

*Researched: 2026-04-05 22:25 CDT*

# WebGPU Subsurface Scattering for Real-Time Anatomy Rendering

## Key Discovery: SIGGRAPH 2025 SSS Course
SIGGRAPH 2025 "Advances in Real-Time Rendering" course has a dedicated session on real-time subsurface scattering with a published PDF. Key technique: **hybrid ReSTIR-Path Tracing + Diffusion** for RT-based subsurface scattering.

## Implementation Approaches (Ordered by Performance Cost)

### Tier 1: Approximation (Fastest — suitable for mobile WebGPU)
- **Wrap lighting / translucency fake**: Colin Barré-Brisebois GDC 2011 technique — cheap wrap diffuse + view-dependent translucency term
- **Source**: https://www.slideshare.net/slideshow/colin-barrebrisebois-gdc-2011-approximating-translucency-for-a-fast-cheap-and-convincing-subsurfacescattering-look-7170855/7170855

### Tier 2: Separable SSS (Medium — desktop WebGPU)
- **Separable Subsurface Scattering** (Jimenez et al.): 2-pass Gaussian blur in screen space
- **Source**: https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
- Applied in many game engines; can be adapted to WebGPU compute shaders

### Tier 3: BSSRDF-Based (Accurate — research quality)
- **Disney BSDF with Integrated SSS** (Burley 2015): Extends Disney BRDF with diffusion term
- **Source**: https://blog.selfshadow.com/publications/s2015-shading-course/burley/s2015_pbs_disney_bsdf_slides.pdf
- **Quantized-Diffusion Model** (d'Eon & Irving): More accurate than dipole
- **PBRT BSSRDF chapter**: https://pbr-book.org/3ed-2018/Volume_Scattering/The_BSSRDF

### Tier 4: Path-Traced SSS (Ground truth — not real-time on mobile)
- **Hybrid ReSTIR + Diffusion** (SIGGRAPH 2025): Novel real-time path-traced SSS
- **Source**: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf

## SOMA Integration Recommendation
For SOMA's mobile anatomy viewer (Three.js/WebGPU via WKWebView):
1. Start with **Tier 1** (wrap lighting translucency fake) — immediate visual improvement for skin/muscle/organ layers
2. Migrate to **Tier 2** (separable SSS) when WebGPU compute shaders are available in mobile Safari
3. Use **Tier 3** for desktop/VR mode as optional quality level
4. The Jaysmito101 AdvancedVulkanDemos repo has a reference MD with all key papers linked: https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md

## Key Papers Referenced
- Jimenez et al., "Separable Subsurface Scattering" (the industry standard)
- Burley, "Extending the Disney BRDF to a BSDF with Integrated SSS" (Disney 2015)
- d'Eon & Irving, "A Quantized-Diffusion Model for Rendering Translucent Materials"
- NVIDIA GPU Gems Ch.14 & Ch.16 (skin rendering and SSS approximation)

## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
