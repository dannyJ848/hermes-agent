# threejs-webgpu-2026-soma-impact

*Researched: 2026-04-06 06:34 CDT*

# Three.js WebGPU in 2026: Implications for SOMA 3D Anatomy Viewer

## Key Findings (March 2026)

### Three.js r171+ WebGPU Renderer (Production-Ready)
- Released September 2025 with `WebGPURenderer` via `import { WebGPURenderer } from 'three/webgpu'`
- Zero-configuration import system — no complex setup
- Automatic WebGL fallback for older browsers
- Three.js downloaded 2.7M times/week on NPM by March 2026 (270x nearest competitor)

### Performance Gains
- **100x improvement** in handling LiDAR point clouds and millions of particles
- Segments.ai (3D segmentation platform) migrated LiDAR point cloud tool from WebGL→WebGPU in 2025-2026 with massive perf gains
- Compute shaders now available for: collision detection, real-time filtering, custom particle systems
- Reduced memory overhead, enhanced instancing for large models
- Universal browser support since late 2025 (Chrome, Firefox, Safari, Edge)

### Shader Development
- **TSL (Three Shading Language)** simplifies shader creation — no raw WGSL needed
- Native WebGPU gives full WGSL control but requires deep expertise
- For SOMA: TSL is the sweet spot — medical shader effects (SSS, transparency) without low-level GPU programming

### SOMA Architecture Decision
- **Recommendation**: Use Three.js WebGPURenderer for SOMA's anatomy viewer
- Models under 500MB (anatomy atlases fit this): Three.js WebGPU ideal
- TSL enables custom SSS skin shaders without raw compute shader expertise
- WebGPU compute shaders could enable real-time tissue simulation on mobile
- Import path: `import { WebGPURenderer } from 'three/webgpu'` — trivial migration from WebGL

### SIGGRAPH 2025 SSS Advances
- NVIDIA presented hybrid real-time subsurface scattering combining volumetric path tracing with new physically-based diffusion
- ReSTIR-Path Tracing integration for real-time SSS
- Relevance: These techniques will eventually reach WebGPU — SOMA can adopt them via TSL

## Sources
- AlterSquare: Three.js vs WebGPU 2026 analysis
- SIGGRAPH 2025 Advances in Real-Time Rendering course
- NVIDIA GPU Gems 3 Ch.14 (skin rendering reference)


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
