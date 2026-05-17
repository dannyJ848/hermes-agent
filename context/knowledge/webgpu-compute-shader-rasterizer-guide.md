# webgpu-compute-shader-rasterizer-guide

*Researched: 2026-04-05 18:58 CDT*

# WebGPU Compute Shader Rasterizer Guide

**Source:** OmarShehata/webgpu-compute-rasterizer (GitHub, 264 stars)
**URL:** https://github.com/OmarShehata/webgpu-compute-rasterizer

## Key Findings

### Why Compute Rasterizers Matter
- Rendering large point clouds (>100M points) with compute shaders is **~10x faster** than point primitives (from Markus Schütz's point cloud rendering talk)
- Unreal Engine 5 switches to compute rasterizers for very small triangles for performance
- Compute shaders allow custom pixel blending — averaging colors of all points hitting same pixel, creating x-ray/volumetric effects

### SOMA Relevance
1. **Medical volume rendering**: Anatomy datasets have millions of vertices. Compute rasterizers can render them 10x faster than traditional pipeline.
2. **X-ray/translucency effects**: Custom blending in compute shaders enables the "see-through" visualization useful for layered anatomy (skin → muscle → bone).
3. **WebGPU storage buffers + atomic operations**: Core primitives for building a medical volume renderer in the browser.

### Technical Architecture
- Uses storage buffers (new in WebGPU vs WebGL)
- Compute shaders with atomic operations for pixel-level control
- Work group thread tuning for minimizing blocking operations
- Custom vertex buffer ordering for performance

### Key Techniques Applicable to SOMA
- **Point cloud rendering** for anatomy mesh vertices
- **Custom blending** for translucent tissue layers (complements SSS shader research from cycle 214)
- **Storage buffer** pattern for passing large anatomy datasets to GPU
- **Atomic operations** for depth buffer management in volume rendering

### Next Steps for SOMA
- Evaluate whether iOS WKWebView supports WebGPU (as of 2026, Safari has experimental WebGPU support)
- Prototype a compute shader for anatomy point cloud rendering
- Combine with SSS shader findings (cycle 214) for realistic tissue rendering


## Sources

- https://github.com/OmarShehata/webgpu-compute-rasterizer
- https://github.com/OmarShehata/webgpu-compute-rasterizer/blob/main/how-to-build-a-compute-rasterizer.md
