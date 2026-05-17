# subsurface-scattering-webgpu-realtime-2025

*Researched: 2026-04-06 16:17 CDT*

# Real-Time Subsurface Scattering for Anatomy Rendering (2025 State)

## Key Discovery: SIGGRAPH 2025 Advances Course
NVIDIA presented a **hybrid real-time SSS technique** combining volumetric path tracing (ReSTIR) with physically-based diffusion at SIGGRAPH 2025 "Advances in Real-Time Rendering in Games" (20th anniversary course). The technique uses **ReSTIR-Path Tracing** combined with diffusion approximation for SSS.

**Source:** https://advances.realtimerendering.com/s2025/ (PDF not directly extractable - binary/compressed)

## Reference Architecture for SOMA's SSS Implementation

### Tier 1: Production-Ready Techniques (implementable now)
1. **Separable Subsurface Scattering** (Jimenez et al.) - The standard real-time approach
   - Paper: https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
   - 2-pass screen-space blur, works in WebGL/WebGPU
   - Profile textures for skin, fat, muscle, organ tissue

2. **Approximating Translucency** (Barre-Brisebois, GDC 2011) - Fast, cheap, convincing
   - Slides: https://www.slideshare.net/slideshow/colin-barrebrisebois-gdc-2011-approximating-translucency-for-a-fast-cheap-and-convincing-subsurfacescattering-look-7170855/7170855
   - Wrapping lighting + transmission, very GPU-efficient

3. **GPU Gems Ch.16 - Real-Time Approximations to SSS** (NVIDIA)
   - https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
   - Warp-factor depth correction, texture-space diffusion

### Tier 2: High-Quality Techniques (for detailed organ views)
4. **GPU Gems 3 Ch.14 - Advanced Skin Rendering** (d'Eon)
   - https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
   - Gaussian texture-space diffusion with 6 profiles
   - Best reference for multi-layer tissue rendering

5. **Disney BSDF with Integrated SSS** (Burley 2015)
   - https://blog.selfshadow.com/publications/s2015-shading-course/burley/s2015_pbs_disney_bsdf_slides.pdf
   - Normalized diffusion profile (replaces multi-Gaussian)

6. **Quantized Diffusion Model** (d'Eon & Irving 2011)
   - Most physically accurate real-time method
   - Uses quantized dipole for better near-field behavior

### Tier 3: Path-Traced / Future (WebGPU compute)
7. **BSSRDF Importance Sampling** (Sony Pictures)
   - PDF: https://pdfs.semanticscholar.org/90da/5211ce2a6f63d50b8616736c393aaf8bf4ca.pdf
   - For when WebGPU compute shaders allow ray tracing

8. **NVIDIA ReSTIR + Hybrid Diffusion (SIGGRAPH 2025)**
   - Combines path tracing with diffusion for real-time SSS
   - Future direction for WebGPU when ray query is widely supported

## Practical Implementation Path for SOMA

### Phase 1: Screen-Space SSS (WebGL compatible)
- Implement Separable SSS in fragment shader
- 2-pass Gaussian blur in screen space
- Profile textures per tissue type (skin=red shift, muscle=deep red, fat=yellow)

### Phase 2: Transmission + Wrapping (enhanced realism)
- Add approximated translucency for thin structures (ears, fingers, organ walls)
- Light wrapping factor per tissue type

### Phase 3: WebGPU Compute SSS (next gen)
- Texture-space diffusion via compute shaders
- Custom diffusion profiles per anatomical material
- Optional path-traced SSS for close-up organ views

## Code Reference
- Advanced Vulkan Demos SSS: https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- MJP's SSS Introduction: https://therealmjp.github.io/posts/sss-intro/
- Skin textures: https://github.com/Vulpinii/skin-texture/tree/master


## Sources

- https://advances.realtimerendering.com/s2025/
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
- https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- https://therealmjp.github.io/posts/sss-intro/
