# webgpu-compute-rasterizer-medical-rendering

*Researched: 2026-04-05 19:49 CDT*

# WebGPU Compute Rasterizer for Medical Volume Rendering

## Key Finding (Apr 2026)

WebGPU compute shaders enable rendering techniques impossible with traditional graphics pipelines, directly applicable to medical 3D anatomy visualization.

### Performance Advantage
- **10x faster** for large point clouds (>100M points) compared to point primitives (Markus Schütz's research)
- Unreal Engine 5 uses compute rasterizers for very small triangles — significantly faster
- Key: custom work group sizing and vertex buffer ordering minimizes blocking operations

### Techniques Enabled by Compute Rasterizers
1. **Pixel-level color averaging** — average colors of all geometry hitting same pixel. Creates natural "x-ray" / transparency effects without alpha blending
2. **Free-form read-write** to output buffer — can read current pixel AND write new value simultaneously
3. **Custom blending** — control how pixels combine beyond standard alpha/depth operations

### Architecture for SOMA
- Use compute shaders for anatomy mesh rendering (bones, organs, tissues have many small triangles)
- Storage buffers for vertex data → compute shader processes triangles → atomic operations write to texture
- Potential for "x-ray mode" where tissue layers blend naturally via pixel averaging
- Work group tuning: match thread count to anatomy complexity for optimal mobile performance

### Resources
- OmarShehata/webgpu-compute-rasterizer (GitHub, 264 stars) — step-by-step tutorial
- Markus Schütz point cloud rendering talk — performance benchmarks
- MDPI Applied Sciences 15(5):2782 — WebGPU volume rendering framework for ocean scalar data (applicable to medical volumes)

### SOMA Integration Path
1. Implement basic compute rasterizer in Three.js WebGPU renderer
2. Test with simplified anatomy meshes (skull, femur)
3. Add pixel-averaging for transparent tissue layers
4. Benchmark against traditional pipeline on iOS WKWebView


## Sources

- https://github.com/OmarShehata/webgpu-compute-rasterizer
- https://www.mdpi.com/2076-3417/15/5/2782
