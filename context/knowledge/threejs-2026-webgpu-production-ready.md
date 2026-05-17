# threejs-2026-webgpu-production-ready

*Researched: 2026-04-07 15:55 CDT*

# Three.js 2026: WebGPU Production-Ready Across All Browsers

## Key Findings for SOMA
- **WebGPU now on ALL major browsers** including Safari iOS (September 2025). The waiting game is over.
- Three.js r171 made WebGPU zero-config: `import { WebGPURenderer } from 'three/webgpu'`
- Three.js dominates web 3D: 2.7M weekly NPM downloads (270x Babylon.js)
- Real-world case: Segments.ai achieved **100x performance improvement** migrating from WebGL to WebGPU
- Compute shaders now available for ML workloads in-browser
- WebXR expansion continuing

## SOMA Impact
- SOMA's Three.js 3D anatomy viewer can now safely target WebGPU renderer
- Safari iOS support means no need for WebGL fallback on iOS devices
- Compute shaders open possibility of in-browser medical image processing
- Zero-config import simplifies the build pipeline

## Source
Utsubo blog (Jocelyn Lecamus), March 22, 2026


## Sources

- https://www.utsubo.com/blog/threejs-2026-what-changed
