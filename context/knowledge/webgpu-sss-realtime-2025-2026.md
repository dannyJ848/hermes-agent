# webgpu-sss-realtime-2025-2026

*Researched: 2026-04-05 18:46 CDT*

# Real-Time Subsurface Scattering & WebGPU Advances (2025-2026)

## SIGGRAPH 2025: Hybrid SSS Technique
- NVIDIA presented a **hybrid real-time subsurface scattering** technique combining **volumetric path tracing with a new physically-based diffusion model** (ReSTIR-Path Tracing + Diffusion).
- Source: SIGGRAPH 2025 Advances in Real-Time Rendering course
- PDF: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Video: https://www.youtube.com/watch?v=AtFBbMnUgoc
- **Relevance to SOMA:** This hybrid approach could replace our screen-space SSS approximation with physically accurate skin rendering for anatomy models. The ReSTIR sampling strategy is particularly relevant for real-time performance on mobile.

## Three.js WebGPU Status (March 2026)
- Three.js r171 (Sept 2025) introduced production-ready `WebGPURenderer` with zero-config imports: `import { WebGPURenderer } from 'three/webgpu'`
- By March 2026: 2.7M weekly NPM downloads, 270x nearest competitor
- **WebGPURenderer performance gains over WebGL:**
  - 100x performance for LiDAR point clouds and millions of particles
  - Compute shaders for collision detection, real-time filtering
  - Reduced memory overhead, enhanced instancing
  - Segments.ai case study: migrated LiDAR tool from WebGL → WebGPU with dramatic improvements
- **Three.js TSL (Three Shading Language)** simplifies shader development
- **Best for models <500MB; native WebGPU better for >500MB**

## SOMA Integration Notes
- Three.js r171+ WebGPURenderer is production-ready — SOMA should migrate from WebGL renderer
- Compute shaders enable real-time tissue density filtering
- TSL could simplify our custom SSS shaders
- Mobile Safari WebGPU support landed in iOS 18 (late 2025) — now universal browser support


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
