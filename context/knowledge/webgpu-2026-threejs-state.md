# webgpu-2026-threejs-state

*Researched: 2026-04-05 23:40 CDT*

# WebGPU + Three.js State (March 2026)

## Key Finding
Three.js r171 (Sept 2025) introduced production-ready `WebGPURenderer` with zero-config import:
```js
import { WebGPURenderer } from 'three/webgpu'
```

Universal browser support since late 2025. By March 2026, Three.js hits 2.7M weekly NPM downloads.

## Performance Gains
- **100x improvement** on LiDAR point clouds and millions of particles
- Compute shaders for collision detection, real-time filtering
- Reduced memory overhead, enhanced instancing for large models
- Segments.ai migrated LiDAR tool from WebGL→WebGPU with massive gains

## SOMA Relevance
- Three.js WebGPU is production-ready for anatomy rendering
- Models under 500MB work great with Three.js WebGPU layer
- TSL (Three Shading Language) simplifies custom shader dev — directly applicable to SSS shaders for skin/organ rendering
- WebGPU compute shaders enable real-time tissue deformation calculations on GPU
- Native WebGPU available for >500MB anatomy models requiring max performance

## SIGGRAPH 2025 SSS Paper
- "Real-Time Subsurface Scattering" published at SIGGRAPH 2025 Advances
- Hybrid ReSTIR-Path Tracing + Diffusion approach for real-time SSS
- PDF: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- This is the state-of-art for real-time subsurface scattering — directly applicable to SOMA's organ rendering

## Action Items for SOMA
1. Evaluate WebGPURenderer migration from current WebGL renderer
2. Study SIGGRAPH 2025 SSS paper for implementable techniques
3. Test TSL for custom tissue shaders


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
