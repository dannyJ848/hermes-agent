# real-time-subsurface-scattering-webgpu-anatomy

*Researched: 2026-04-06 20:05 CDT*

# Real-Time Subsurface Scattering for 3D Anatomy Rendering

## Key Findings (April 2026 Research)

### SIGGRAPH 2025 Advances: RT Subsurface Scattering
- **Hybrid ReSTIR-Path Tracing + Diffusion** approach introduced at SIGGRAPH 2025
- Combines path tracing with diffusion approximation for real-time SSS
- Source: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf

### Implementation Resources for SOMA
1. **Separable Subsurface Scattering** (Jimenez et al.) — The gold standard for real-time SSS in games. Uses 2-pass Gaussian blur in screen space.
   - Paper: https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf

2. **Approximating Translucency** (GDC 2011, Barre-Brisebois) — Fast, cheap SSS look. Good for mobile targets.
   - Slides: https://www.slideshare.net/slideshow/colin-barrebrisebois-gdc-2011-approximating-translucency-for-a-fast-cheap-and-convincing-subsurfacescattering-look-7170855/7170855

3. **GPU Gems Chapter 16** — NVIDIA's real-time approximation using depth maps and wrap lighting.
   - URL: https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering

4. **Vulkan SSS Demo** — Working implementation with code by Jaysmito101
   - Repo: https://github.com/Jaysmito101/AdvancedVulkanDemos

### SOMA Application Strategy
- **Mobile (Three.js/WebGL):** Use the GDC 2011 translucency approximation — cheap wrap lighting + thickness map. No compute shaders needed.
- **Desktop (WebGPU):** Consider separable SSS with 2-pass blur. Requires compute shaders (WebGPU supports them).
- **Future path:** ReSTIR-based hybrid approach once WebGPU ray tracing APIs mature.

### Key Technical Insight
SSS for anatomy differs from skin rendering: organ tissue has different scattering coefficients (higher absorption, different mean free path). Need to tune SSS profiles per tissue type using measured BSSRDF data from medical literature.

## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
