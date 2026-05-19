# webgpu-real-time-sss-medical-rendering-2025

*Researched: 2026-04-05 12:09 CDT*

# WebGPU Real-Time SSS & Medical Volume Rendering (2025)

## Grenzwert Medical Volume Viewer
**URL:** https://grenzwert.net
**Source:** Hacker News Show HN (Feb 2026), MickGorobets

A **GPU path tracer for volumetric medical data (CT/MRI)** running entirely in Chrome via WebGPU + WebAssembly (C++/Emscripten). Desktop-class rendering quality with zero-install.

### Key Techniques
- **Delta tracking** (Woodcock null-collision algorithm) for unbiased volume rendering
- **Cook-Torrance GGX BRDF** + **Henyey-Greenstein phase function** for scattering
- **MacroGrid acceleration**: DDA empty-space skipping + GPU tile culling
- **Progressive frame accumulation**: noisy initially, converges to ground truth
- **HDR pipeline**: bloom, auto-exposure, PBR Neutral / ACES tone mapping
- **Async mip-level streaming** with gzip decompression
- Built on **Diligent Engine** (cross-platform: D3D, Vulkan, Metal, WebGPU)

### Browser Requirements
- Chrome/Edge 142+ with full WebGPU + texture-formats-tier1 extension
- Firefox: missing texture-formats-tier1 (Bug 1982451)
- Safari: crashes during WebGPU init

### SOMA Relevance: **HIGH**
This proves real-time cinematic medical volume rendering is viable in-browser via WebGPU. SOMA could adopt:
1. The delta tracking approach for volumetric anatomy visualization
2. MacroGrid acceleration for large anatomy datasets
3. Progressive accumulation for quality refinement on mobile
4. Async mip-level streaming for fast initial load

---

## SIGGRAPH 2025: Hybrid ReSTIR-Path Tracing + Diffusion for SSS
**Source:** SIGGRAPH 2025 Advances in Real-Time Rendering course
**Paper:** "RT Subsurface Scattering via Hybrid ReSTIR-Path Tracing & Diffusion"
**Also:** "ReSTIR Subsurface Scattering for Real-Time Path Tracing" (ACM DOI: 10.1145/3675372)

### Key Innovation
Traditional real-time SSS uses **screen-space diffusion approximations** (separable SSS, Burley normalized diffusion). This new hybrid approach:
1. Uses **ReSTIR** (Reservoir-based Spatiotemporal Importance Resampling) for path-traced subsurface scattering
2. Combines path tracing importance sampling with diffusion approximation
3. Delivers high-quality SSS "fast enough for current generation pipelines"

### Impact for Anatomy Rendering
Skin, organs, and tissue all exhibit strong subsurface scattering. The ReSTIR approach could give SOMA photorealistic tissue rendering in real-time, far beyond screen-space approximations.

---

## SSS Reference Library (Jaysmito101/AdvancedVulkanDemos)
**URL:** https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md

Comprehensive list of SSS techniques ranked by implementation complexity:
1. **Cheap**: Approximating Translucency (GDC 2011, Colin Barre-Brisebois)
2. **Screen-Space**: Separable SSS (Jimenez et al.), Burley Normalized Diffusion (Siggraph 2018)
3. **Path-Traced**: BSSRDF Importance Sampling (Sony Pictures)
4. **Production**: Disney BSDF with Integrated SSS, Quantized Diffusion

### Recommended Implementation Path for SOMA
1. Start with **cheap translucency approximation** for mobile (1-2 extra shader passes)
2. Upgrade to **screen-space Burley normalized diffusion** for desktop
3. Explore **ReSTIR SSS** when WebGPU compute shaders mature across browsers


## Sources

- https://grenzwert.net
- https://news.ycombinator.com/item?id=46933474
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.youtube.com/watch?v=AtFBbMnUgoc
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
