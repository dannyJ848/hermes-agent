# threejs-to-webgpu-large-scale-3d-engine

*Researched: 2026-04-05 18:51 CDT*

# Three.js to WebGPU: Large-Scale 3D Engine Lessons

**Source:** Three.js forum post by VIKAS_KUMAR_SINGH (April 2026) — building infinite 3D engine (orionrealms.com)

## Key Performance Findings

### InstancedMesh at Scale
- Successfully rendered **1 million objects** via InstancedMesh
- Animated **100k objects** by supplying transferable arrays between web workers
- Two web workers running alongside main thread (sim worker + render worker)

### Origin Rebasing Architecture
- Cell-based origin rebasing is **essential** for walkable planet-scale scenes
- When shifting positions for objects in visible 3x3x3 grid, R3F tree shakes cause scene rebuilds → **1 FPS**
- **Vanilla Three.js outperforms R3F** for dynamic scene graphs with frequent position updates
- Fix: ditch React/R3F, use vanilla Three.js for dynamic scenes

### WebGPU Migration Path
- Three.js WebGPURenderer + TSL (Three Shading Language) used for commercial project
- WebGPU enables compute shaders for GPU-side computation
- Offscreen rendering + Data-Oriented Design (DOD) approach needed for large-scale scenes
- Transferable arrays between workers avoid serialization overhead

## SOMA Applicability
1. **Anatomy models with thousands of parts** → Use InstancedMesh for repeated structures (blood vessels, neurons)
2. **Dynamic LOD/rebasing** → Cell-based origin rebasing for zooming from body-level to cellular-level
3. **Vanilla Three.js over R3F** → SOMA already uses vanilla Three.js in WKWebView — confirmed correct choice
4. **Web Workers** → Offload mesh processing to workers, keep main thread for rendering only
5. **Transferable arrays** → Pass geometry data between workers without copying

### Warning Signs
- WebGPU renderer (r182) shows **significant performance drop and shadow quality regression** vs WebGL (r170)
- WebGPU not yet production-stable in Three.js — stay on WebGL renderer for now, plan migration path
- Shadow quality regression in r182 noted by multiple users


## Sources

- https://discourse.threejs.org/t/from-three-js-to-webgpu-my-insane-journey-building-an-infinite-3d-engine/90779
- https://discourse.threejs.org/t/webgpu-significant-performance-drop-and-shadow-quality-regression-in-r182-vs-webgl-r170/89322
