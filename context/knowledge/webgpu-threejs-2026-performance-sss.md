# webgpu-threejs-2026-performance-sss

*Researched: 2026-04-06 15:06 CDT*

# WebGPU + Three.js 2026: Performance Advances for 3D Anatomy Rendering

## Three.js r171+ WebGPU Renderer (Sept 2025)
- Production-ready `WebGPURenderer` with zero-config import: `import { WebGPURenderer } from 'three/webgpu'`
- WebGL fallback automatic
- By March 2026: 2.7M weekly NPM downloads (270x nearest competitor)

## Key Performance Gains
- **100x performance** on LiDAR point clouds and millions of particles
- Compute shaders for collision detection, real-time filtering
- Reduced memory overhead, enhanced instancing for large models
- Segments.ai migrated from WebGL→WebGPU 2025-2026, saw dramatic perf gains

## Relevance to SOMA
- Three.js WebGPU path is ideal for anatomy models (typically <500MB)
- Compute shaders enable real-time tissue selection, cutting plane operations
- Enhanced instancing = better performance with layered anatomy (skin→muscle→bone)
- Universal browser support since late 2025 (Safari, Chrome, Firefox)

## SIGGRAPH 2025: Hybrid Real-Time SSS
- NVIDIA introduced hybrid real-time subsurface scattering combining volumetric path tracing with new physically-based diffusion
- Paper: `advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf`
- ReSTIR-Path Tracing + diffusion approach
- Could be adapted for WebGPU compute shaders in browser

## Decision Point
- SOMA should target Three.js WebGPURenderer for the anatomy viewer
- Native SSS shaders can be ported to TSL (Three Shading Language) 
- Models under 500MB work well with Three.js; native WebGPU only needed for >500MB


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
