# webgpu-compute-shaders-threejs-2026

*Researched: 2026-04-05 16:07 CDT*

# WebGPU Compute Shaders for Three.js — State of Art (April 2026)

## Key Findings

### 1. Three.js r171+ Production WebGPU
- Released September 2025, production-ready WebGPU renderer
- Zero-config import: `import { WebGPURenderer } from 'three/webgpu'`
- Three.js downloaded 2.7M times/week on NPM by March 2026
- **For SOMA:** Use WebGPURenderer for anatomy models; WebGL fallback for older devices

### 2. Compute Shader Optimization — Atomic Contention Fix
- **Problem:** `atomicMax` in high-concurrency loops serializes workgroup execution (warp stalling)
- **Solution:** Parallel Reduction Tournament — logarithmic sweep using `workgroupBarrier()` and bitwise shifts (`i >>= 1u`)
- **Result:** 256 sequential updates → 8 parallel rounds (O(N) → O(log N))
- **Directly applicable to SOMA:** MRI/CT volume gradient calculations, mesh processing
- Source: Oserebameh, Three.js Forum (March 2026)

### 3. Performance Benchmarks
- Segments.ai: LiDAR point cloud tool went from WebGL → WebGPU, saw 100x performance gains
- Compute shaders enable collision detection, real-time filtering on GPU
- Reduced memory overhead, enhanced instancing for large models
- **SOMA takeaway:** Complex anatomy meshes (>500MB) benefit from native WebGPU; models under 500MB fine with Three.js WebGPU abstraction

### 4. Architecture Decision for SOMA
- **Phase 1:** Use Three.js WebGPURenderer (simpler, WebGL fallback)
- **Phase 2:** Custom compute shaders for volume rendering, SSS, mesh decimation
- **Phase 3:** Native WebGPU for massive datasets (full-body scans, histology volumes)
- TSL (Three Shading Language) simplifies shader development within Three.js ecosystem

## Sources
- Three.js Forum: discourse.threejs.org/t/how-to-optimize-compute-shaders-in-webgpu-for-speed/90109
- AlterSquare: altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/


## Sources

- https://discourse.threejs.org/t/how-to-optimize-compute-shaders-in-webgpu-for-speed/90109
- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://medium.com/@osebeckley/gpu-optimization-in-webgpu-solving-atomic-contention-with-parallel-reduction-037819e5f7ed
