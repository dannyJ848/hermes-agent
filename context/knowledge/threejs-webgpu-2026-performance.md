# threejs-webgpu-2026-performance

*Researched: 2026-04-05 22:05 CDT*

# Three.js WebGPU Performance in 2026 — Key Findings for SOMA

## Source
Altersquare.io — Three.js vs WebGPU 2026 analysis (March 31, 2026)

## Key Findings

### Three.js r171+ WebGPU Renderer (Sept 2025)
- Production-ready `WebGPURenderer` with zero-config import: `import { WebGPURenderer } from 'three/webgpu'`
- TSL (Three Shader Language): write shaders once, deploy to WGSL and GLSL — critical for SOMA's cross-platform SSS shaders
- Compute shaders now available via Three.js — GPU-parallel processing for collision detection, real-time lighting, data filtering

### Performance Gains (Real-World)
- **100× performance boost** on LiDAR point clouds (Segments.ai case study, 2025-2026 migration)
- Particle systems: **1,000,000+ units** vs WebGL's ~50,000 limit
- Reduced memory overhead, enhanced instancing for large models
- Three.js downloads: 2.7M/week on NPM by March 2026 (270× nearest competitor)

### SOMA Implications
1. **SSS Shaders**: TSL allows writing anatomy SSS shaders once for both WGSL (WebGPU) and GLSL (WebGL fallback) — directly relevant to `soma-sss-shaders` skill
2. **Anatomy Model Scale**: 1M+ particle support means tissue-level detail is feasible in browser
3. **Compute Shaders for Medical**: Could use compute pipelines for real-time tissue deformation, cross-section computation
4. **Migration Path**: Three.js WebGPURenderer with WebGL fallback means SOMA can target WebGPU-first with graceful degradation on older browsers
5. **Universal Browser Support**: All major browsers support WebGPU since late 2025 — safe to target for mobile anatomy viewer

### When to Use Native WebGPU vs Three.js
- **Three.js WebGPU**: Models <500MB, rapid development, most use cases
- **Native WebGPU**: Models >500MB, specialized simulations requiring full GPU control
- **For SOMA**: Three.js WebGPU renderer is the right choice — anatomy models are <500MB, and TSL simplifies the shader pipeline

### SIGGRAPH 2025 SSS Paper (Unread)
- Real-time SSS via hybrid ReSTIR-path tracing & diffusion was presented at SIGGRAPH 2025 Advances
- PDF is available but binary — need a PDF parser or video summary for details
- YouTube presentation available: "RT Subsurface Scattering via Hybrid RESTIR-Path Tracing & Diffusion"


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
