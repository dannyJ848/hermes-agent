# webgpu-mesh-decimation-compute-shaders

*Researched: 2026-04-06 06:49 CDT*

# WebGPU Compute Shaders for Mesh Decimation & Large Model Handling

## Key Finding (April 2026)
Three.js r171+ (Sept 2025) introduced production-ready WebGPURenderer with zero-config import: `import { WebGPURenderer } from 'three/webgpu'`. This is directly relevant to SOMA's mobile 3D anatomy rendering.

## Performance Gains (Construction/LiDAR benchmarks)
- **100x performance** on LiDAR point clouds and millions of particles
- Compute shaders unlock: collision detection, real-time filtering, mesh decimation
- Reduced memory overhead with enhanced instancing for large models
- Three.js WebGPU practical for models <500MB; native WebGPU for >500MB

## Mesh Simplification Techniques (from literature)
Four main GPU-accelerated operations:
1. **Vertex clustering** — group nearby vertices, replace with single representative
2. **Triangle collapsing** — merge adjacent triangles based on error metrics
3. **Vertex decimation** — remove vertices that contribute least to surface quality
4. **Edge collapse** — most common; collapse edge to single vertex using quadric error metrics

## Detail-Preserving Approach (Nature 2026)
- Texture-aware simplification preserves UV mapping during decimation
- Critical for anatomy models where surface detail (vasculature, tissue texture) matters
- GPU-based simplification makes real-time LOD generation feasible

## SOMA Integration Path
- Three.js TSL (Three Shading Language) simplifies compute shader development
- Could generate LOD levels at load time using compute-based edge collapse
- Target: reduce 500K+ triangle anatomy meshes to 50K for mobile, 200K for desktop
- WebGPU fallback to WebGL ensures iOS Safari compatibility (WebGPU available Safari 18+)

## Sources
- Three.js r171 WebGPU: altersquare.io/three-js-vs-webgpu-2026
- GPU mesh simplification: dl.acm.org/doi/10.1145/1230100.1230128
- Detail-preserving decimation: nature.com/articles/s41598-026-43736-w
- WebGPU dev guide 2025: dev.to/amaresh_adak/webgpu-in-2025


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://dl.acm.org/doi/10.1145/1230100.1230128
- https://www.nature.com/articles/s41598-026-43736-w_reference.pdf
- https://dev.to/amaresh_adak/webgpu-in-2025-the-complete-developers-guide-3foh
