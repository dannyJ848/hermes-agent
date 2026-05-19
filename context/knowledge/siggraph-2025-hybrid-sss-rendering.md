# siggraph-2025-hybrid-sss-rendering

*Researched: 2026-04-05 20:40 CDT*

# SIGGRAPH 2025: Hybrid Real-Time Subsurface Scattering

## Key Development
NVIDIA unveiled a **hybrid real-time SSS technique** (SIGGRAPH 2025 Advances in Real-Time Rendering, marking 20 years of the course) that combines:

1. **Volumetric path tracing** via ReSTIR (Reservoir-based Spatiotemporal Importance Resampling)
2. **Diffusion approximation** for performance fallback

### Technique: ReSTIR-Path Tracing + Diffusion
- Traditional real-time SSS uses diffusion approximations (Gaussian kernels in screen-space texture blur)
- The new hybrid approaches path-traced quality while maintaining real-time performance
- Published paper available at: `advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf`
- YouTube talk: "RT Subsurface Scattering via Hybrid RESTIR-Path Tracing & Diffusion"

### Relevance to SOMA
- SOMA uses Three.js/WebGL for anatomy rendering — currently lacks convincing subsurface scattering
- The SIGGRAPH paper's diffusion approximation component is implementable in WebGL shaders
- The full ReSTIR path tracing requires WebGPU (not WebGL) — future migration target
- **Actionable:** Screen-space Gaussian blur SSS (from GPU Gems 3 Ch.14) is implementable TODAY in SOMA's WebGL pipeline as a post-process effect

### Implementation Path for SOMA (WebGL)
1. Render anatomy model to G-buffer (albedo, normal, depth)
2. Apply screen-space Gaussian diffusion approximation using 6-tap separable blur
3. Use skin-layer absorption profiles (epidermis/dermis/subcutaneous RGB values)
4. Combine with Kelemen/Szirmay-Kalos specular model for oily skin layer

### Implementation Path for SOMA (WebGPU future)
1. Migrate renderer to WebGPU compute shaders
2. Implement ReSTIR-based volumetric path tracing for SSS
3. Hybrid with diffusion fallback for distant/small geometry

### Key References
- GPU Gems 3, Ch.14 (d'Eon & Luebke): Gaussian texture blur SSS
- SIGGRAPH 2025 paper: Hybrid ReSTIR-Path Tracing + Diffusion for SSS
- Donner & Jensen 2006: Multilayer skin model (epidermis → dermis → subcutaneous)

## Sources

- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- https://dl.acm.org/doi/10.1145/3721241.3744991
