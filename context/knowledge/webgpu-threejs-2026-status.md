# webgpu-threejs-2026-status

*Researched: 2026-04-06 19:55 CDT*

# WebGPU + Three.js Status (March 2026)

## Key Findings

### Three.js r171+ WebGPU Renderer (Production Ready)
- Released September 2025 with production-ready WebGPU renderer
- Zero-config import: `import { WebGPURenderer } from 'three/webgpu'`
- Automatic fallback to WebGL when WebGPU unavailable
- Three.js downloaded 2.7M times/week on NPM by March 2026 (270x nearest competitor)

### Performance Benchmarks
- **100x performance gains** for LiDAR point clouds and millions of particles
- Segments.ai migrated LiDAR point cloud labeling from WebGL→WebGPU (2025-2026): 100x+ improvement
- Compute shaders now available for collision detection, real-time filtering
- Reduced memory overhead, enhanced instancing for large models

### When to Use What
| Approach | Best For | Threshold |
|----------|----------|-----------|
| Three.js WebGPU | Models <500MB, rapid dev, prototyping | Default choice |
| Native WebGPU | Models >500MB, simulations, advanced compute | Expert teams |

### SOMA Implications
1. **Mobile WebGPU**: iOS Safari gained WebGPU support in 2025 - SOMA can use SSS shaders natively
2. **TSL (Three Shading Language)**: Simplifies custom shader development - could replace our GLSL SSS approach
3. **Compute shaders**: Could offload mesh processing (decimation, LOD generation) to GPU
4. **Instancing**: Critical for anatomical models with many repeated structures (blood vessels, nerves)
5. **Universal browser support since late 2025** - no more WebGL fallback needed for modern browsers

### SIGGRAPH 2025 SSS Breakthrough
- NVIDIA presented hybrid real-time SSS combining volumetric path tracing + physically-based diffusion
- Uses ReSTIR-Path Tracing for real-time subsurface scattering
- Paper: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Video: https://www.youtube.com/watch?v=AtFBbMnUgoc

### Action Items for SOMA
- [ ] Upgrade to Three.js r171+ with WebGPURenderer
- [ ] Evaluate TSL for SSS shader porting
- [ ] Benchmark anatomical model performance with WebGPU instancing
- [ ] Test mobile WebGPU on iOS Safari with existing SOMA models


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
