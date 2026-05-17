# siggraph-2025-real-time-subsurface-scattering

*Researched: 2026-04-06 13:31 CDT*

# SIGGRAPH 2025: Real-Time Subsurface Scattering Advances

## Key Discovery (SIGGRAPH 2025 Advances in Real-Time Rendering)

NVIDIA unveiled a **hybrid real-time subsurface scattering technique** combining:
1. **Volumetric path tracing** — physically accurate light transport through translucent media
2. **Diffusion-based SSS approximation** — fast screen-space diffusion for real-time performance
3. **ReSTIR-Path Tracing** — resampling-based path guiding for efficient light transport

### Technique: Hybrid ReSTIR-Path Tracing + Diffusion
- Uses ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) to guide path tracing through skin layers
- Combines with classic screen-space diffusion (separable Gaussian approximation) for real-time performance
- Achieves significantly closer ground truth matching than previous screen-space-only approaches
- Captures fine skin detail that diffusion-only methods miss

### Relevance to SOMA 3D Anatomy Viewer
1. **Current approach (soma-sss-shaders skill):** Uses separable Gaussian diffusion — the classic 2007 GPU Gems approach. Fast but lacks physical accuracy for thick tissue (ears, nose).
2. **Potential upgrade:** WebGPU compute shaders could implement a simplified ReSTIR-style approach. The key insight is that path tracing even 1-2 bounce subsurface paths adds dramatic realism for anatomy models.
3. **Practical implementation path:**
   - Phase 1: Keep current diffusion SSS for real-time
   - Phase 2: Add pre-computed subsurface lookup tables for specific tissue types (skin, muscle, organ tissue)
   - Phase 3: WebGPU compute shader for real-time volumetric sampling when browser supports it

### Three.js/WebGPU Status (2025-2026)
- WebGPU has universal browser support since late 2025 (Chrome, Firefox, Safari)
- Three.js r170+ has WebGPU renderer backend
- Construction/architecture platforms already migrated to WebGPU for large-scale viewers
- Anatomy viewers with <500K triangles are well within WebGPU performance budget

### Sources
- SIGGRAPH 2025: "Advances in Real-Time Rendering in Games" (20th anniversary session)
- NVIDIA GPU Gems 3, Chapter 14: "Advanced Techniques for Realistic Real-Time Skin Rendering" (foundational reference)
- Paper: "RT Subsurface Scattering via Hybrid ReSTIR-Path Tracing & Diffusion" (SIGGRAPH 2025)


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
