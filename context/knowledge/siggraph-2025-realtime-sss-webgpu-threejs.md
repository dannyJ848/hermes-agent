# siggraph-2025-realtime-sss-webgpu-threejs

*Researched: 2026-04-06 19:19 CDT*

# SIGGRAPH 2025 Real-Time Subsurface Scattering + Three.js WebGPU Landscape

## SIGGRAPH 2025: Hybrid RT Subsurface Scattering (NVIDIA)

NVIDIA unveiled a **hybrid real-time subsurface scattering technique** at SIGGRAPH 2025 "Advances in Real-Time Rendering" course. The technique combines:
- **Volumetric path tracing** (ReSTIR-based)
- **Physically-based diffusion approximation** (new formulation)

This hybrid approach produces skin rendering with "significantly more detail with much closer ground truth matching" compared to prior separation-based SSS methods.

**Source:** `advances.realtimerendering.com/s2025/` — published PDF available.

**Relevance to SOMA:** SOMA's 3D anatomy viewer uses subsurface scattering for realistic tissue rendering. NVIDIA's hybrid ReSTIR-path-tracing + diffusion approach could dramatically improve organ and skin realism. Key question: feasibility in WebGPU (the technique relies on RT cores).

## Three.js WebGPU Ecosystem (March 2026)

### Production Status
- Three.js r171 (Sept 2025): Production-ready WebGPU renderer
- `import { WebGPURenderer } from 'three/webgpu'` — zero-config
- Three.js r184 (March 2026): Eliminated per-frame object allocations (was 240K-500K+ objects/sec for 1000 meshes @ 60fps)
- **2.7M weekly NPM downloads** — 270x nearest competitor

### Performance Gains
- **100× performance boost** for LiDAR point clouds (Segments.ai case study: WebGL → WebGPU)
- Compute shaders for collision detection, real-time lighting, large-scale filtering
- Particle systems: **1M+ units** (vs 50K limit in WebGL)

### TSL (Three Shader Language)
- Write shaders once, deploy to WGSL and GLSL
- Critical for SOMA: custom tissue materials, SSS shaders, organ-specific rendering
- TSL-native post-processing: Bloom, GaussianBlur, improved bindGroup caching

### React Three Fiber + WebGPU
- R3F supports WebGPU via async `gl` prop factory
- BatchedMesh + enhanced instancing for complex models

**Action Items for SOMA:**
1. Migrate SOMA to Three.js r184+ with WebGPURenderer
2. Rewrite SSS shaders in TSL for cross-platform deployment
3. Use compute shaders for real-time tissue cutting/cross-section computation
4. Target 500MB+ anatomy models with native WebGPU fallback


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
