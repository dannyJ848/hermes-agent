# WebGPU BVH Raytracing for Medical 3D

*Researched: 2026-04-05 22:52 CDT*

# WebGPU BVH Raytracing for Real-Time 3D Rendering

## Source
Matthew MacFarquhar, "WebGPU Rendering: Part 24 — Speeding up Raytracing using BVH" (Medium, March 2025)

## Key Techniques

### Bounding Volume Hierarchies (BVH) in WebGPU
- BVH is a tree structure built by recursively partitioning triangles into groups
- Each node stores an axis-aligned bounding box (AABB: min/max corners)
- Node structure: `minCorner (vec3)`, `maxCorner (vec3)`, `leftChild (int)`, `primitiveCount (int)`
- Right child is implicitly `left + 1`

### Construction Algorithm
1. Build on CPU at load time — extra upfront cost for much faster rendering
2. Upper bound on nodes: `2 * NUM_TRIANGLES - 1` for full binary tree
3. Root node starts with all triangles, then recursively subdivides
4. **Axis-based splitting**: recursively pick X, Y, or Z axis to split triangles
5. **Championship belt algorithm**: update node bounds by iterating all contained triangle positions

### Performance Impact
- Without BVH: raytracing checks every triangle → O(n) per ray → not interactive
- With BVH: bounding volume tests skip large scene portions → near O(log n) per ray
- Enables real-time interactive frame rates in browser via WebGPU compute shaders

### SOMA Integration Opportunities
1. **Pre-computed BVH in GLB files**: Author suggests storing BVH as pre-computed data in GLB files, eliminating runtime construction cost — directly applicable to SOMA's anatomy models
2. **WebGPU compute shaders for ray marching**: Same compute shader pipeline can be used for volume rendering (CT/MRI data) and surface rendering (anatomy meshes)
3. **Load-time optimization**: Build BVH during model load phase, upload to GPU as storage buffer
4. **Triangle budget management**: BVH makes it feasible to render higher-poly anatomy models interactively

### Architecture Pattern
```
CPU Load Phase:
  Parse GLB → Extract triangles → Build BVH tree → Upload to GPU storage buffer

GPU Render Phase (per frame):
  For each pixel ray:
    Traverse BVH → Test bounding boxes → Only test triangles in hit leaf nodes
    Compute shading/lighting for hit triangle
```

## Relevance to SOMA
SOMA's 3D anatomy viewer could use BVH-accelerated raytracing for:
- Interactive cross-section views (ray marching through volume data)
- Picking/selection of anatomical structures (ray casting with BVH)
- Shadow computation for realistic anatomy rendering
- Future WebGPU migration path (currently Three.js/WebGL)


## Sources

- https://matthewmacfarquhar.medium.com/webgpu-rendering-part-24-speeding-up-raytracing-using-bvh-66b23555fd48
