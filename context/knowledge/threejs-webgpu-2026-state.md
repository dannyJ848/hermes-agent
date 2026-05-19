# threejs-webgpu-2026-state

*Researched: 2026-04-06 05:10 CDT*

# Three.js + WebGPU State (March 2026)

## Key Facts
- **Three.js r171** (Sept 2025) introduced production-ready WebGPU renderer
- Zero-config import: `import { WebGPURenderer } from 'three/webgpu'`
- WebGL fallback still available
- By March 2026: 2.7M weekly NPM downloads (270x nearest competitor)
- Universal browser support since late 2025

## Performance Gains
- **100x performance** improvement for LiDAR point clouds and millions of particles
- Compute shaders for collision detection and real-time filtering
- Reduced memory overhead and enhanced instancing for large models
- Segments.ai transitioned LiDAR tool from WebGL → WebGPU: massive perf improvement

## Decision Framework
| Feature | Three.js WebGPU | Native WebGPU |
|---------|----------------|---------------|
| Ease of Use | High | Low |
| Best For | Models <500MB | Models >500MB, simulations |
| Shader Dev | TSL simplifies | Full control, expertise needed |
| Performance | Moderate-large | High for massive datasets |

## Relevance to SOMA
- Three.js WebGPU renderer is the right choice for SOMA anatomy viewer
- Models under 500MB (anatomy models typically 50-200MB)
- TSL (Three Shading Language) simplifies custom SSS shader development
- WebGPU compute shaders could accelerate real-time tissue deformation
- Browser compatibility no longer a concern — universal support

## SIGGRAPH 2025 SSS Breakthrough
- NVIDIA unveiled hybrid real-time SSS combining volumetric path tracing + physically-based diffusion
- Uses ReSTIR-Path Tracing for real-time performance
- Paper available: advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Could inform SOMA's tissue rendering approach


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
