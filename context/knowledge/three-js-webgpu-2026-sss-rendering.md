# three-js-webgpu-2026-sss-rendering

*Researched: 2026-04-05 15:55 CDT*

# Three.js WebGPU Maturity & SSS Rendering (2026)

## Three.js WebGPU Status (March 2026)
- Three.js r171 (Sept 2025) introduced production-ready WebGPU renderer
- Zero-config import: `import { WebGPURenderer } from 'three/webgpu'`
- 2.7M weekly NPM downloads — 270x nearest competitor
- WebGPURenderer provides WebGL fallback automatically
- Segments.ai achieved 100x performance gains on LiDAR point clouds after WebGL→WebGPU migration
- Compute shaders now available for collision detection, real-time filtering
- Best for models under 500MB; native WebGPU better for larger datasets

## SIGGRAPH 2025: Real-Time Subsurface Scattering
- NVIDIA unveiled hybrid real-time SSS combining volumetric path tracing with physically-based diffusion
- ReSTIR-Path Tracing integration for real-time SSS
- Significantly better ground-truth matching for skin rendering
- Paper: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Video: https://www.youtube.com/watch?v=AtFBbMnUgoc

## SOMA Implications
- Three.js WebGPU is now production-ready — SOMA can target WebGPURenderer
- SSS shaders for anatomy should follow NVIDIA's hybrid approach (diffusion + path tracing)
- Compute shaders enable real-time tissue classification on GPU
- Mobile: WebGPU support landed in Safari 18+ (iOS 18), Chrome Android — covers SOMA's iOS target


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
