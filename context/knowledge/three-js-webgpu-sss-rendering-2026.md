# three.js-webgpu-sss-rendering-2026

*Researched: 2026-04-05 19:16 CDT*

# Three.js WebGPU Subsurface Scattering (2026 Status)

## Key Findings

### Three.js r171+ WebGPURenderer
- Three.js now has a built-in WebGPU SSS material example (`webgpu_materials_sss.html`)
- WebGPURenderer provides automatic fallback to WebGL2 when WebGPU is unavailable
- Universal browser support achieved late 2025

### Performance Comparison (Three.js WebGPU vs Native WebGPU)
- **Three.js WebGPU**: Ideal for models under 500MB, rapid development, TSL (Three Shading Language) simplifies shader development
- **Native WebGPU**: Better for models >500MB, massive datasets, advanced simulations — requires deep expertise
- Key 2026 improvement: 100x performance gains on LiDAR point clouds and millions of particles

### SOMA Relevance
- Three.js SSS example can serve as reference implementation for SOMA's anatomical tissue rendering
- WebGPURenderer fallback to WebGL2 ensures iOS Safari compatibility (critical for SOMA mobile)
- Compute shaders now available in Three.js — could enable real-time medical image segmentation
- TSL shader language simplifies custom material development (vs raw WGSL)

### Architecture Decision
For SOMA's 3D anatomy viewer:
1. Use Three.js WebGPURenderer (not native WebGPU) for maintainability
2. Implement SSS via TSL for realistic tissue rendering
3. Leverage compute shaders for real-time cross-section computation
4. WebGL2 fallback handles iOS Safari until WebGPU ships there

### Sources
- Three.js SSS example: https://threejs.org/examples/webgpu_materials_sss.html
- Three.js vs WebGPU 2026 comparison: https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/


## Sources

- https://threejs.org/examples/webgpu_materials_sss.html
- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
