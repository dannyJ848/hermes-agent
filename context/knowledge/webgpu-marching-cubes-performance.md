# webgpu-marching-cubes-performance

*Researched: 2026-04-05 21:40 CDT*

# WebGPU Marching Cubes: Near-Native Vulkan Performance

**Source:** Will Usher (willusher.io), April 2024

## Key Findings

1. **WebGPU compute shaders run Marching Cubes at near-native Vulkan speed** — the overhead of the browser abstraction is minimal for this embarrassingly-parallel algorithm.

2. **Marching Cubes origin:** First published 1987 by Lorensen and Cline. Original motivation was **medical visualization** — extracting bone/tissue surfaces from CT/MRI volumes. Directly relevant to SOMA's anatomy mesh generation.

3. **Algorithm structure for GPU:**
   - Classify each voxel into a case via bitmask (8 bits, one per vertex)
   - Look up triangle edges from a case table (256 entries)
   - Two global reduction steps needed for synchronization
   - Otherwise embarrassingly parallel — ideal for GPU compute

4. **WebGPU vs WebGL key advantage:** WebGPU supports **compute shaders and storage buffers**, which WebGL lacks entirely. This makes it possible to run the full Marching Cubes pipeline on GPU without CPU round-trips.

5. **Implementation approach:**
   - Uses dual grid (values at vertices, not cell centers)
   - Bitmask classification → case table lookup → edge interpolation → triangle output
   - Storage buffers for triangle output with atomic counters for vertex allocation

## Relevance to SOMA

- **DICOM → mesh pipeline:** Marching Cubes on WebGPU compute shaders can convert medical volume data (CT/MRI) to triangle meshes **entirely in the browser** at interactive rates.
- **No server needed:** Volume rendering and isosurface extraction can run client-side on mobile Safari/Chrome with WebGPU.
- **LOD strategy:** Multiple isosurface levels can be computed at different resolutions for adaptive detail.
- **Integration path:** SOMA's existing Three.js pipeline could use WebGPU compute for mesh generation, then render via standard pipeline.

## References
- Will Usher blog: https://www.willusher.io/graphics/2024/04/22/webgpu-marching-cubes/
- GitHub implementation: https://github.com/conorpo/marching-cubes-webgpu
- MDPI WebGPU volume rendering paper: https://www.mdpi.com/2076-3417/15/5/2782
- Mol* molecular graphics (uses WebGPU marching cubes): https://onlinelibrary.wiley.com/doi/10.1002/pro.70514


## Sources

- https://www.willusher.io/graphics/2024/04/22/webgpu-marching-cubes/
- https://github.com/conorpo/marching-cubes-webgpu
- https://www.mdpi.com/2076-3417/15/5/2782
- https://onlinelibrary.wiley.com/doi/10.1002/pro.70514
