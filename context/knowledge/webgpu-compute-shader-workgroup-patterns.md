# webgpu-compute-shader-workgroup-patterns

*Researched: 2026-04-06 05:46 CDT*

# WebGPU Compute Shader Workgroup Patterns for 3D Mesh Processing

## Source
Medium article by Oserebameh Beckley (Jan 2026) — mental model for WebGPU compute shaders.

## Key Patterns for SOMA

### Workgroup Sizing
- `@workgroup_size(8, 8, 4)` = 256 threads per workgroup (good default for volumetric data)
- For anatomy meshes: map voxels to threads, process 3D volumes in parallel
- Dispatch: `Math.ceil(dataSize / workgroupSize)` per axis

### Shared Memory (var<workgroup>)
- Threads within a workgroup share memory — cross-workgroup communication NOT possible
- Use for local reductions (finding max gradient, min distance, etc.)
- **Race condition fix:** `workgroupBarrier()` ensures all threads sync before reading shared data

### Global vs Local IDs
- `global_id` = absolute index in the full dataset (use for reading input buffers)
- `local_invocation_id` = index within the workgroup (use for shared memory indexing)

### Performance Anti-Pattern
- "Atomic Safety" — overusing atomics kills GPU parallelism
- **Fix:** Parallel Reduction via Tournament Trees — hierarchical reduction within workgroups, then combine results

### Application to SOMA LOD
1. Vertex decimation: dispatch N workgroups over vertex buffer, each workgroup processes a cluster
2. Use shared memory to find edge collapse candidates within cluster
3. Use workgroupBarrier() to sync before writing collapsed vertices
4. Multiple passes for progressive LOD levels

### Relevant for Anatomy Rendering
- MRI volume processing (256×256×128) maps naturally to 3D workgroups
- Mesh simplification can use same pattern — treat vertex neighborhoods as 3D clusters
- SIGGRAPH 2025 Advances course has continuous LOD via displacement maps using compute shaders


## Sources

- https://medium.com/@osebeckley/webgpu-compute-shaders-explained-a-mental-model-for-workgroups-threads-and-dispatch-eaefcd80266a
- https://advances.realtimerendering.com/s2025/
