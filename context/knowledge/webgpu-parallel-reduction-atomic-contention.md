# webgpu-parallel-reduction-atomic-contention

*Researched: 2026-04-07 18:22 CDT*

# WebGPU Compute Shader Optimization: Solving Atomic Contention

## Problem
In WebGPU compute pipelines, `atomicMax` and similar atomic operations serialize workgroup execution into a "single-file line" due to warp stalling. In high-occupancy shaders (e.g., MRI gradient calculations, 3D mesh processing), this bottleneck kills parallelism.

## Solution: Parallel Reduction Tournament
Replace atomic aggregation with a logarithmic sweep using `workgroupBarrier()` and bitwise shifts:

```wgsl
// Parallel reduction for workgroup maximum
for (var stride = workgroupSize / 2u; stride > 0u; stride >>= 1u) {
    if (gl_LocalInvocationID.x < stride) {
        shared_mem[gl_LocalInvocationID.x] = max(
            shared_mem[gl_LocalInvocationID.x],
            shared_mem[gl_LocalInvocationID.x + stride]
        );
    }
    workgroupBarrier();
}
```

## Results
- Slashes 256 sequential atomic updates down to exactly 8 parallel rounds
- O(N) → O(log N) for workgroup-scale aggregations
- Applicable to any WebGPU compute pipeline doing reductions (max, min, sum)

## Relevance to SOMA
- SOMA's 3D anatomy rendering uses WebGPU for volume rendering
- Mesh LOD calculations, bounding box computations, and subsurface scattering pre-computation all involve reduction operations
- This pattern can be applied to optimize mesh processing in the asset pipeline
- MRI gradient calculation is directly relevant to medical imaging features

## Source
- Three.js forum: https://discourse.threejs.org/t/how-to-optimize-compute-shaders-in-webgpu-for-speed/90109
- Deep dive article: https://medium.com/@osebeckley/gpu-optimization-in-webgpu-solving-atomic-contention-with-parallel-reduction-037819e5f7ed


## Sources

- https://discourse.threejs.org/t/how-to-optimize-compute-shaders-in-webgpu-for-speed/90109
- https://medium.com/@osebeckley/gpu-optimization-in-webgpu-solving-atomic-contention-with-parallel-reduction-037819e5f7ed
