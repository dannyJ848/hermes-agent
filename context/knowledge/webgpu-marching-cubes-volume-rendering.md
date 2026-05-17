# webgpu-marching-cubes-volume-rendering

*Researched: 2026-04-05 15:42 CDT*

# WebGPU Marching Cubes for Medical Volume Rendering

## Key Finding
WebGPU compute shaders can run Marching Cubes at **near-native Vulkan performance** in the browser, enabling real-time medical volume rendering (CT/MRI isosurface extraction) entirely client-side.

## Technical Details

### Algorithm: Marching Cubes on GPU
- Nearly embarrassingly parallel — ideal for GPU compute
- Two global reduction steps needed for synchronization (vertex count + triangle offset)
- Each voxel independently classified via 8-bit case bitmask → lookup table
- Originally developed for medical imaging (Lorensen & Cline, 1987) for CT/MRI surface extraction

### WebGPU vs Vulkan Performance
- Will Usher (2024) benchmarked identical Marching Cubes in both WebGPU and native Vulkan
- WebGPU compute shaders + storage buffers are the key differentiator from WebGL
- Performance is competitive with native — the browser overhead is minimal for compute-bound workloads
- Chrome Canary recommended for best WebGPU support

### SOMA Integration Potential
- **DICOM → Isosurface extraction in browser**: Load DICOM volumes, extract bone/tissue surfaces via compute shaders
- **替代 Z-Anatomy static GLB**: Dynamic isosurface generation from volumetric data instead of pre-built meshes
- **Interactive threshold control**: User adjusts tissue density threshold → real-time mesh regeneration
- **Mobile consideration**: WebGPU support on iOS Safari is limited (as of 2025). Would need WebGL2 fallback or WKWebView with native Metal

### Key References
1. Will Usher, "GPU Compute in the Browser at the Speed of Native: WebGPU Marching Cubes" (2024) — willusher.io
2. MDPI Applied Sciences, "WebGPU-Based Volume Rendering Framework" (2025) — ocean scalar data visualization
3. Keijiro Takahashi, Unity WebGPU Volume Rendering of CT scan data using marching cubes — keijiro.tokyo
4. Lorensen & Cline (1987), original Marching Cubes paper

### Architecture for SOMA
```
DICOM Volume → 3D Texture → WebGPU Compute Pass
  → Marching Cubes (per-voxel classification) → Triangle Buffer
  → Render Pass (SSS shading, cross-section clipping)
  → Interactive threshold slider triggers re-extraction
```

### Risks
- WebGPU browser support still evolving (Chrome good, Safari limited, Firefox experimental)
- Large volumes (512³+) may exceed GPU memory on mobile
- Need fallback path for WebGL2-only devices


## Sources

- https://www.willusher.io/graphics/2024/04/22/webgpu-marching-cubes/
- https://www.mdpi.com/2076-3417/15/5/2782
- https://www.keijiro.tokyo/WebGPU-Test/MarchingCubesCThead/
