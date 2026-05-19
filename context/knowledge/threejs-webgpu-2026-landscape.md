# threejs-webgpu-2026-landscape

*Researched: 2026-04-06 01:37 CDT*

# Three.js WebGPU in 2026: Rendering Landscape Update

## Key Findings (March 2026)

### Three.js r171+ WebGPU Renderer (Sept 2025)
- Production-ready WebGPU renderer shipped in Three.js r171
- Zero-config import: `import { WebGPURenderer } from 'three/webgpu'`
- Automatic WebGL fallback for unsupported browsers
- Universal browser support since late 2025

### Performance Benchmarks
- **100× performance gains** in LiDAR point cloud handling
- Millions of particles rendered efficiently
- Segments.ai migrated LiDAR tool from WebGL→WebGPU (2025-2026), massive perf improvement
- Three.js downloaded **2.7M times/week** on NPM by March 2026

### Three.js WebGPU vs Native WebGPU
| Feature | Three.js WebGPU | Native WebGPU |
|---------|----------------|---------------|
| Ease of Use | High | Low |
| Performance | Moderate (<500MB models) | High (>500MB models) |
| Shader Dev | TSL simplifies shaders | Full control, requires expertise |
| Best For | Prototyping, anatomy viewers | Large simulations, massive datasets |

### Compute Shaders (New in WebGPU)
- Collision detection offloaded to GPU
- Real-time filtering of massive datasets
- Reduced memory overhead
- Enhanced instancing for large models

### SIGGRAPH 2025 SSS Breakthrough
NVIDIA introduced a **hybrid real-time subsurface scattering technique** combining:
- Volumetric path tracing
- New physically-based diffusion model
- ReSTIR-path tracing integration
- Significantly closer ground truth matching for skin rendering

### SOMA Architecture Implications
1. **Three.js WebGPU is now viable** for SOMA — r171+ with compute shaders enables mobile anatomy rendering
2. **SSS via compute shaders** could replace screen-space approximations for realistic tissue rendering
3. **Instancing improvements** support complex anatomical models with many repeated structures
4. **TSL (Three Shading Language)** simplifies custom shader development for medical visualization
5. Models under 500MB (typical anatomy atlas) are squarely in Three.js WebGPU sweet spot

## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
