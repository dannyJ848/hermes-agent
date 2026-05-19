# three-js-webgpu-large-scale-rendering-2026

*Researched: 2026-04-06 19:25 CDT*

# Three.js → WebGPU: Large-Scale 3D Rendering Techniques (April 2026)

## Source: VIKAS_KUMAR_SINGH (three.js forum, Apr 2026)
Developer of Axion Engine (orionrealms.com), 500k+ views on Reddit.

## Key Architectural Patterns for Million-Object Scenes

### 1. Origin Rebasing (Cell-based)
- Essential for walkable planet-scale scenes
- Divide world into 3x3x3 grid cells, rebase origin as camera moves
- **CRITICAL PITFALL:** R3F (React Three Fiber) shakes the React tree during rebasing → drops to 1 FPS
- **FIX:** Use vanilla Three.js, NOT R3F, for origin-rebasing architectures
- Must run in web workers to avoid blocking main thread

### 2. Data-Oriented Design (DOD)
- Offscreen rendering with DOD approach enables walkable planet layers
- Transferable arrays between workers for zero-copy animation data
- Two web workers: simulation worker + render worker

### 3. InstancedMesh at Scale
- InstancedMesh renders 1M+ objects efficiently
- Animating 100k objects via transferable arrays (transferable ArrayBuffers between workers)
- Works with both WebGL and WebGPU renderers

### 4. WebGPU Migration Path
- Three.js WebGPURenderer now production-ready for large scenes
- Some shadow quality regressions in r182 vs WebGL r170 (as of early 2026)
- Compute shaders enable GPGPU particles and GPU-driven techniques
- Performance gains most notable at >100k object scale

## Relevance to SOMA
- **Origin rebasing** could solve anatomical zoom-from-body-to-cell navigation
- **InstancedMesh** for rendering thousands of similar structures (blood vessels, neurons)
- **Transferable arrays** for real-time animation of physiological processes
- **DOD pattern** aligns with medical data structures (DICOM slices, mesh vertices)
- **Avoid R3F** for performance-critical medical rendering — use vanilla Three.js

## Performance Benchmarks (from community)
- 100k animated objects: feasible with WebGPU + transferable arrays
- 1M static objects: feasible with InstancedMesh
- Shadow quality: WebGL r170 still slightly better than WebGPU r182 in some cases


## Sources

- https://discourse.threejs.org/t/from-three-js-to-webgpu-my-insane-journey-building-an-infinite-3d-engine/90779
- https://discourse.threejs.org/t/webgpu-significant-performance-drop-and-shadow-quality-regression-in-r182-vs-webgl-r170/89322
