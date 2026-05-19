# webgpu-real-time-rendering-2025

*Researched: 2026-04-05 17:07 CDT*

# WebGPU Real-Time Rendering Advances (2025)

## Key Finding: WebGPU Compute Shaders Enable Real-Time Fluid/Particle Sim in Browser

**Source:** Hector Arellano (Hat), Codrops, Jan 2025 — "Particles, Progress, and Perseverance: A Journey into WebGPU Fluids"

### Core Technical Advances
- WebGPU provides compute shaders, storage buffers, 3D textures, atomics, indirect draw calls — none available in WebGL
- Smoothed Particle Hydrodynamics (SPH) for particle-based fluid simulation now runs in-browser
- Marching cubes on GPU for mesh generation from particle fields
- Histopyramids for GPU-side stream compaction
- 13-year journey from WebGL hacks to production WebGPU fluid sims

### SIGGRAPH 2025 Real-Time SSS
- SIGGRAPH 2025 Advances course published new real-time subsurface scattering techniques
- Hybrid ReSTIR-Path Tracing combined with diffusion profiles for realistic SSS in real time
- Paper: advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf

### SOMA Relevance
- **WebGPU SSS for anatomy rendering**: The SIGGRAPH 2025 SSS techniques could be adapted for realistic skin/organ rendering in SOMA's 3D viewer
- **Compute shaders for mesh processing**: Decimation, LOD generation, and mesh compression can run on GPU via WebGPU compute
- **SPH for soft tissue simulation**: Particle-based tissue deformation could enhance interactive anatomy
- **Browser compatibility**: WebGPU now in Chrome/Edge (Safari experimental) — iOS Safari support still limited
- **Migration path**: SOMA currently uses Three.js (WebGL). WebGPU adapter in Three.js (WebGPURenderer) is maturing — monitor for production readiness

### Web vs Pixel Streaming (2025 Analysis)
- ravespace.io analysis confirms: for complex 3D (medical), pixel streaming gives better quality but WebGL/WebGPU gives better accessibility and lower latency
- SOMA's mobile-first approach favors WebGPU over pixel streaming for offline-capable rendering

### Action Items
1. Monitor Three.js WebGPURenderer stability for production use
2. Evaluate iOS Safari WebGPU support timeline (critical for SOMA mobile)
3. Prototype WebGPU compute shader for mesh decimation in browser
4. Consider SSS diffusion profile shader for organ/skin rendering


## Sources

- https://tympanus.net/codrops/2025/01/29/particles-progress-and-perseverance-a-journey-into-webgpu-fluids/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://ravespace.io/blog/pixel-streaming-vs-webgl-three-js-2025-s-scientific-verdict-on-3d-web-technologies
