# webgpu-compute-shaders-mesh-lod

*Researched: 2026-04-05 21:34 CDT*

# WebGPU Compute Shaders for Mesh LOD/Simplification

## Key Findings (Oct 2025 article, relevant 2026)

### Browser Support (Production-Ready)
- WebGPU now universally supported since late 2025 including iOS Safari
- Near-native performance comparable to Vulkan/Metal
- Three.js TSL (Three Shading Language) provides umbrella abstraction over WebGPU + WebGL

### Compute Shader Capabilities
- **Particle systems**: GPU-driven particle updates via compute shaders (eliminate CPU bottleneck)
- **Instanced mesh transforms**: Batch transform computation on GPU
- **Post-processing**: Compute-based effects replacing fragment shader ping-pong
- **Memory management**: Direct control over bind groups, storage buffers

### Architecture: TSL Node System
- TSL is a functional JS-like shading language
- Compiles to both WGSL (WebGPU) and GLSL (WebGL) — single codebase targets both
- Replaces Three.js legacy GLSL shader chunks
- Node materials (`meshStandardNodeMaterial`) replace classic materials

### SOMA Application: Mesh LOD Pipeline
WebGPU compute shaders enable:
1. **GPU-side mesh decimation**: Simplify anatomy meshes without CPU roundtrip
2. **Dynamic LOD selection**: Compute shader evaluates camera distance → selects detail level
3. **Batched transforms**: Process all anatomy node transforms on GPU
4. **SSS shader optimization**: Compute-based subsurface scattering pre-pass

### Implementation Path
- Use Three.js TSL to write compute shaders that work on both WebGPU and WebGL fallback
- Start with particle system compute shader (simplest) → then mesh LOD
- `storageBuffer` + `computeNode` pattern from Maxime Heckel's guide

### Sources
- Maxime Heckel: "Field Guide to TSL and WebGPU" (Oct 2025)
- Utsubo: "100 Three.js Tips That Actually Improve Performance (2026)"
- Three.js now supports `WebGPURenderer` as first-class renderer


## Sources

- https://blog.maximeheckel.com/posts/field-guide-to-tsl-and-webgpu/
- https://www.utsubo.com/blog/threejs-best-practices-100-tips
- https://rendimension.com/blog/three-js-rendering/
