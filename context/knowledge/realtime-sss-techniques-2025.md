# realtime-sss-techniques-2025

*Researched: 2026-04-06 12:53 CDT*

# Real-Time Subsurface Scattering Techniques for Anatomy Rendering

## SIGGRAPH 2025 Breakthrough
NVIDIA unveiled a **hybrid real-time SSS technique** combining ReSTIR path tracing with diffusion-based subsurface approximation. This is the state-of-the-art for real-time skin/organic tissue rendering.

**Key presentation:** "RT Subsurface Scattering via Hybrid ReSTIR-Path Tracing & Diffusion" at SIGGRAPH 2025 Advances in Real-Time Rendering course.

## Practical Implementation References (GPU-friendly)

### 1. Separable Subsurface Scattering (Jimenez et al.)
- **Paper:** https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
- 2D Gaussian blur pass decomposed into two 1D passes
- Very fast, good quality for real-time
- Used in many game engines for skin rendering
- **SOMA relevance:** Can implement in WebGPU compute shaders for tissue rendering

### 2. Approximating Translucency (Barre-Brisebois, GDC 2011)
- **Slides:** https://www.slideshare.net/slideshow/colin-barrebrisebois-gdc-2011-approximating-translucency-for-a-fast-cheap-and-convincing-subsurfacescattering-look-7170855/7170855
- Fast, cheap, convincing SSS look without full simulation
- Great for mobile/performance-constrained targets
- **SOMA relevance:** Best option for iOS WKWebView where compute budget is limited

### 3. GPU Gems Chapter 16 - Real-Time Approximations
- **URL:** https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- Classic reference: wraps lighting + texture-based approaches
- Works in fragment shaders (no compute needed)

### 4. BSSRDF (PBRT)
- Physically correct approach using Bidirectional Surface Scattering RDF
- Too expensive for real-time but ground truth for validation

## SOMA Implementation Priority
1. **Mobile (iOS):** Approximating Translucency approach — cheap, convincing, no compute shaders needed
2. **Desktop (WebGPU):** Separable SSS with 2-pass Gaussian — high quality, reasonable perf
3. **Future:** Hybrid ReSTIR approach when WebGPU ray tracing lands in browsers

## Skin Texture Resources
- Free skin textures: https://github.com/Vulpinii/skin-texture/tree/master


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://www.reddit.com/r/GraphicsProgramming/comments/1lfku5c/playing_around_with_realtime_subsurface/
