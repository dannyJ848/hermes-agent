# threejs-100-performance-tips-2026

*Researched: 2026-04-06 06:37 CDT*

# 100 Three.js Performance Tips (2026) — Key Extracts for SOMA

**Source:** Utsubo blog, March 2026

## Most Relevant for SOMA 3D Anatomy Viewer

### WebGPU Renderer
- **Zero-config WebGPU import** with async init; automatic WebGL2 fallback
- **TSL (Three Shader Language)** replaces raw GLSL/WGSL — use for SSS shaders
- **Compute shaders** for particle systems and physics — offload from CPU
- **instancedArray** for GPU-persistent buffers (anatomy tissue layers)
- **forceWebGL** flag for debugging/compat testing
- **renderAsync** for compute-heavy scenes (anatomy models with many meshes)
- **Storage textures** for read-write compute (volume rendering)
- **Minimize buffer updates per frame** — batch geometry updates
- **2-10x performance gains** in specific scenarios vs WebGL

### Asset Optimization (Critical for SOMA)
- **Draco compression** for geometry — reduces GLB sizes significantly
- **KTX2 texture compression** — UASTC for quality, ETC1S for size
- **gltf-transform CLI** for batch optimization of anatomy models
- **LOD (Level of Detail)** — essential for anatomy with many systems
- **Atlas textures** to reduce texture binds per tissue type
- **Meshopt** as Draco alternative (better decompression speed)
- **Progressive loading** — load skeleton first, then muscles, then organs

### Draw Call Optimization
- **Target under 100 draw calls/frame** — SOMA must batch aggressively
- **InstancedMesh** for repeated objects (vertebrae, ribs, teeth)
- **BatchedMesh** for varied geometries (different organ shapes)
- **Share materials** between meshes (same tissue type = same material)
- **Merge static geometry** with BufferGeometryUtils for non-interactive parts

### Memory Management
- **Dispose all GPU resources** when switching anatomy systems
- **Object pooling** for spawned entities (probe tools, labels)
- **Cache and reuse textures** — anatomy atlases should be persistent

### Shaders & Materials (SSS Shaders)
- **mediump precision on mobile** — SOMA targets iOS
- **Minimize varying variables** — pack data into RGBA channels
- **Replace conditionals with mix()/step()** — GPU-friendly branching
- **TSL over raw GLSL** — future-proof for WebGPU migration

### Lighting & Shadows
- **Limit active lights to 3** — key for mobile performance
- **Bake lightmaps** for static anatomy regions
- **Cascaded Shadow Maps** for large scenes (full body view)
- **Environment maps** for ambient light — cheap and realistic

### Loading (SOMA UX)
- **Lazy load 3D content below fold** — progressive anatomy reveal
- **Web Workers** for heavy parsing of anatomy models
- **Placeholder geometry** during load (wireframe → solid)
- **Stream large scenes** — skeleton first, organs progressively

### React Three Fiber (if SOMA uses R3F)
- **frameloop="demand"** for static anatomy views (no continuous render)
- **invalidate()** for manual updates when user rotates
- **Drei's LOD** component
- **useGLTF.preload** for preloading anatomy models
- **Toggle visibility instead of remounting** when switching systems

## Action Items for SOMA
1. Implement LOD for anatomy models (full body → skeletal detail → organ detail)
2. Use Draco/Meshopt compression on all GLB anatomy files
3. Batch draw calls — merge non-interactive geometry
4. Add progressive loading: skeleton → muscles → organs → skin
5. Switch to TSL for SSS shaders (WebGPU future-proofing)
6. Limit to 3 lights for mobile performance
7. Use frameloop="demand" for static anatomy views


## Sources

- https://www.utsubo.com/blog/threejs-best-practices-100-tips
