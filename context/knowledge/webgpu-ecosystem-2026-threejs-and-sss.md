# webgpu-ecosystem-2026-threejs-and-sss

*Researched: 2026-04-06 02:07 CDT*

# WebGPU Ecosystem State (March 2026) & SIGGRAPH 2025 SSS Advances

## Three.js WebGPU Status (r171+, March 2026)

### Production-Ready WebGPU Renderer
- **Three.js r171** (Sept 2025) introduced production-ready WebGPU renderer
- Zero-config import: `import { WebGPURenderer } from 'three/webgpu'`
- WebGL fallback automatically available
- **2.7M weekly NPM downloads** by March 2026 — 270x nearest competitor
- WebGPU has universal browser support since late 2025

### Performance Gains (Real-World)
- **100x performance gains** on LiDAR point clouds and millions of particles
- Compute shaders for collision detection, real-time filtering
- Reduced memory overhead, enhanced instancing for large models
- Segments.ai migrated LiDAR point cloud labeling tool from WebGL → WebGPU (2025-2026) with dramatic speedup

### When to Use What
| Feature | Three.js WebGPU | Native WebGPU |
|---------|----------------|---------------|
| Ease of Use | High | Low |
| Best For | Models <500MB, prototyping | Models >500MB, simulations |
| Shader Dev | TSL simplifies shaders | Full control, requires expertise |

## SIGGRAPH 2025: Real-Time Subsurface Scattering

### Key Paper (NVIDIA, SIGGRAPH 2025 Advances in Real-Time Rendering)
- **Title**: RT Subsurface Scattering via Hybrid ReSTIR-Path Tracing & Diffusion
- **Novel technique**: Hybrid approach combining volumetric path tracing with physically-based diffusion
- Uses **ReSTIR** (Reservoir-based Spatiotemporal Importance Resampling) for SSS specifically
- Claims significantly more detail with closer ground truth matching vs prior methods
- Designed for real-time game rendering (not offline)

### Relevance to SOMA
- NVIDIA's hybrid SSS could be adapted for WebGPU compute shaders in anatomy viewer
- Three.js TSL (Three Shading Language) now provides a simpler path to custom SSS shaders
- The ReSTIR approach is GPU-heavy — likely needs native WebGPU for full benefit
- For mobile: simpler screen-space SSS (from GPU Gems 3 Ch.14) still more practical
- Key insight: WebGPU's compute shader pipeline now makes real-time volumetric SSS feasible in-browser

## Actionable for SOMA
1. **Upgrade to Three.js r171+ WebGPU renderer** — zero-cost perf upgrade
2. **Monitor ReSTIR-SSS** for future native WebGPU integration when mobile WebGPU arrives
3. **Current approach** (screen-space SSS via TSL shaders) is correct for mobile-first
4. Consider WebGPU compute shaders for LOD calculations and mesh simplification at runtime


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
