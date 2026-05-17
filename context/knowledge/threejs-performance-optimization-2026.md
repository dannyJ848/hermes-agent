# threejs-performance-optimization-2026

*Researched: 2026-04-06 00:19 CDT*

# Three.js Performance Optimization — 100 Tips (2026)

**Source:** Utsubo blog, Jocelyn Lecamus, Mar 2026

## Most Actionable for SOMA (Mobile 3D Anatomy)

### WebGPU Migration
- Use zero-config WebGPU import with async init; automatic WebGL2 fallback
- Move particle systems to **compute shaders** for 2-10x gains
- Use `instancedArray` for GPU-persistent buffers
- Use `forceWebGL` strategically for older iOS devices
- TSL (Three Shader Language) replaces raw GLSL/WGSL for custom materials
- Use `renderAsync` for compute-heavy scenes

### Draw Call Optimization
- Target **under 100 draw calls per frame**
- Use `InstancedMesh` for repeated objects (anatomical layers/structures)
- Use `BatchedMesh` for varied geometries
- Merge static geometry with `BufferGeometryUtils`
- Share materials between meshes

### Asset Optimization
- Compress geometry with **Draco**; use **Meshopt** as alternative
- Use **KTX2** for texture compression (UASTC for quality, ETC1S for size)
- Implement **LOD** (Level of Detail) — critical for complex anatomy models
- Atlas textures to reduce texture binds
- Master `gltf-transform` CLI for pipeline optimization

### Mobile-Specific
- Use `mediump` precision on mobile shaders
- Minimize varying variables
- Avoid dynamic loops in shaders
- Use object pooling for spawned entities
- Size shadow maps appropriately (don't oversample)

### Memory Management
- **Dispose all GPU resources** when done (textures, geometries, materials)
- Cache and reuse textures
- Clean up on component unmount (React)
- Dispose render targets explicitly

### Loading & Core Web Vitals
- Lazy load 3D content below the fold
- Code-split Three.js modules
- Implement progressive loading (critical for large anatomy datasets)
- Offload heavy work to **Web Workers**
- Stream large scenes
- Use placeholder geometry during load

### Lighting
- Limit active lights to **3 or fewer**
- Bake lightmaps for static scenes (anatomy is mostly static)
- Use environment maps for ambient light
- Disable shadow auto-update for static scenes

## Key Insight for SOMA
Anatomy models are mostly **static geometry** — perfect candidates for:
1. Geometry merging (BufferGeometryUtils)
2. Lightmap baking
3. LOD (high-res near camera, low-res far)
4. InstancedMesh for repeated structures (vertebrae, teeth, etc.)
5. KTX2 texture compression for mobile bandwidth savings


## Sources

- https://www.utsubo.com/blog/threejs-best-practices-100-tips
