# threejs-webgpu-2026-status

*Researched: 2026-04-05 21:31 CDT*

# Three.js WebGPU Status (March 2026)

## Key Milestone
- Three.js r171 (September 2025): Production-ready WebGPU renderer
- Zero-config import: `import { WebGPURenderer } from 'three/webgpu'`
- WebGPU has universal browser support since late 2025
- Three.js NPM downloads: 2.7M/week by March 2026 (270x nearest competitor)

## Performance Gains (WebGPU over WebGL)
- 100x performance gains on LiDAR point clouds and millions of particles
- Segments.ai case study: migrated LiDAR point cloud labeling tool → massive speedup
- Compute shaders enable: collision detection, real-time filtering, simulation
- Reduced memory overhead, enhanced instancing for large models

## Three.js WebGPU vs Native WebGPU
| Feature | Three.js WebGPU | Native WebGPU |
|---------|----------------|---------------|
| Ease of Use | High | Low |
| Best For | Models <500MB, prototyping | Models >500MB, simulations |
| Shader Dev | TSL simplifies shaders | Full control, requires expertise |
| Performance | Moderate for large datasets | High for massive datasets |

## SOMA Relevance
- Three.js WebGPU is ideal for SOMA's anatomy models (well under 500MB)
- WebGPURenderer with WebGL fallback gives us broad compatibility
- Compute shaders could enable real-time tissue simulation
- TSL (Three Shading Language) simplifies custom SSS shader development
- Enhanced instancing = better performance for multi-organ models


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
