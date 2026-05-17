# threejs-webgpu-renderer-2026-status

*Researched: 2026-04-05 18:10 CDT*

# Three.js WebGPU Renderer Status (March 2026)

## Key Finding
Three.js r171 (Sept 2025) introduced a **production-ready WebGPU renderer** with zero-config imports:
```js
import { WebGPURenderer } from 'three/webgpu'
```

## Performance Gains (for large-scale 3D)
- **100× improvement** on LiDAR point clouds and millions of particles
- Compute shaders now accessible for collision detection, real-time filtering
- Reduced memory overhead, enhanced instancing for large models
- Automatic WebGL fallback

## SOMA Relevance
- Three.js weekly NPM downloads: 2.7M (270× nearest competitor) — massive ecosystem
- **Models <500MB**: Three.js WebGPU is the right choice (native WebGPU overkill)
- **TSL (Three Shading Language)** simplifies custom shader development — directly applicable to subsurface scattering and tissue rendering
- Segments.ai case study: migrated LiDAR point cloud tool from WebGL→WebGPU in 2025-2026, saw 100× gains
- Universal browser support since late 2025

## Architecture Decision for SOMA
- **Use Three.js WebGPU renderer** (not native WebGPU) for SOMA's anatomy viewer
- Leverage TSL for custom tissue shaders (SSS, translucency)
- WebGPU compute shaders can handle DICOM volume ray marching
- WebGL fallback ensures iOS Safari compatibility during transition
- The 500MB threshold covers SOMA's anatomy model sizes comfortably

## Timeline
- r171 released Sept 2025
- Universal browser support achieved late 2025
- Current: r174+ (as of March 2026) — stable and production-ready


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://github.com/mrdoob/three.js/issues/31381
- https://discourse.threejs.org/t/from-three-js-to-webgpu-my-insane-journey-building-an-infinite-3d-engine/90779
