# webgpu-marching-cubes-medical-volume-rendering

*Researched: 2026-04-05 20:58 CDT*

# WebGPU Marching Cubes for Medical Volume Rendering

## Key Findings

### Performance: WebGPU ≈ Native Vulkan Speed
Will Usher (April 2024) benchmarked Marching Cubes in WebGPU vs native Vulkan. Key result: **WebGPU compute shaders run at near-native Vulkan performance** for embarrassingly parallel algorithms like Marching Cubes. The two global reduction steps (synchronization) are the main bottleneck but WebGPU handles them efficiently.

### Relevance to SOMA
Marching Cubes was **originally invented for medical visualization** (Lorensen & Cline, 1987) — specifically for extracting bone/tissue surfaces from CT and MRI volumes. This is directly applicable to SOMA's anatomy viewer:

1. **Isosurface extraction**: Could generate mesh surfaces from DICOM volume data directly in the browser
2. **GPU compute pipeline**: WebGPU's storage buffers + compute shaders enable parallel voxel processing
3. **No server-side processing**: Everything runs client-side in the browser

### Implementation Notes
- Algorithm is "nearly embarrassingly parallel" — each voxel is independent
- Two global reduction steps needed for thread synchronization
- Case table lookup based on 8-bit bitmask (one bit per voxel vertex)
- Dual grid approach: shift from cell-centered to vertex-centered values
- WebGPU's compute pipeline handles the parallel dispatch naturally

### Mol* Molecular Graphics Engine
A 2026 paper in Protein Science describes Mol*, a web molecular graphics engine that uses WebGPU compute for:
- Gaussian-density accumulation
- Marching cubes isosurface extraction
- Volumetric smoothing

This proves the approach is production-ready for scientific visualization in browsers.

### Reference Implementation
- `conorpo/marching-cubes-webgpu` on GitHub: Noise field → MC triangle creation → rasterization
- Will Usher's blog has full WebGPU vs Vulkan benchmark code

## SOMA Integration Path
1. Load DICOM volume as 3D texture
2. Run WebGPU compute shader for MC isosurface extraction at configurable iso-value
3. Output triangle mesh to GPU buffer
4. Render with Three.js WebGPU renderer or custom pipeline
5. Allow user to adjust iso-value slider for different tissue densities (bone, soft tissue, skin)


## Sources

- https://www.willusher.io/graphics/2024/04/22/webgpu-marching-cubes/
- https://onlinelibrary.wiley.com/doi/10.1002/pro.70514
- https://github.com/conorpo/marching-cubes-webgpu
