# threejs-webgpu-2026-anatomy-rendering

*Researched: 2026-04-06 01:31 CDT*

# Three.js WebGPU 2026: Implications for SOMA Anatomy Viewer

## Key Findings

### Three.js r171+ WebGPURenderer (Sep 2025)
- Production-ready WebGPU renderer with zero-config: `import { WebGPURenderer } from 'three/webgpu'`
- Automatic WebGL fallback for older browsers
- TSL (Three Shading Language) simplifies custom shader development
- Three.js downloaded 2.7M times/week on NPM by March 2026 — 270x nearest competitor

### Performance Benchmarks (WebGPU vs WebGL)
- 100x performance gains for LiDAR point clouds and millions of particles
- Compute shaders for collision detection and real-time filtering
- Reduced memory overhead and enhanced instancing
- Segments.ai achieved massive speedup migrating LiDAR tool to WebGPU

### SOMA Architecture Decision
- **Three.js WebGPU is the right choice** for SOMA (anatomy models well under 500MB)
- Native WebGPU only needed for >500MB models or specialized simulations
- TSL makes custom SSS/transparency shaders much easier to write than raw WGSL
- Three.js ecosystem (OrbitControls, GLTFLoader, post-processing) all WebGPU-compatible

### Anatomy Model Pipeline (confirmed by community)
- Z-Anatomy (free) → Blender → export GLB → Three.js GLTFLoader
- Layer-based anatomy: separate meshes per system (skin, muscles, skeleton, veins, organs, nervous)
- Dynamic transparency per layer via material.opacity
- Interactive selection via raycasting + metadata mapping

### Competitive Landscape
- ZygotBody.com exists but is proprietary
- Several Three.js anatomy projects on discourse (student projects)
- No open-source mobile-first bilingual anatomy viewer exists — SOMA's niche

## Action Items for SOMA
1. Verify Three.js version in SOMA project ≥ r171
2. Test WebGPURenderer import path `three/webgpu`
3. Write SSS shader in TSL instead of raw GLSL/WGSL
4. Benchmark anatomy GLB with WebGPURenderer vs WebGLRenderer
5. Implement layer-toggle system per anatomical system

## Sources
- Three.js forum anatomy thread: discourse.threejs.org/t/a-3d-interactive-system-for-exploring-human-anatomy-by-anatomical-layers/88813
- Three.js vs WebGPU 2026 comparison: altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- Z-Anatomy free models: referenced as primary free anatomy source


## Sources

- https://discourse.threejs.org/t/a-3d-interactive-system-for-exploring-human-anatomy-by-anatomical-layers/88813
- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
