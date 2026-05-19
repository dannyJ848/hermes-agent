# threejs-webgpu-performance-100-tips-2026

*Researched: 2026-04-05 22:37 CDT*

# 100 Three.js Performance Tips (2026) — Utsubo

**Source:** Utsubo blog, March 2026 — Comprehensive guide for Three.js WebGPU optimization.

## Key Takeaways for SOMA
- **WebGPU production-ready since r171** — zero-config imports with automatic WebGL2 fallback
- **TSL (Three Shader Language)** is the future — write once, run on WebGPU or WebGL
- **Draw calls are the silent killer** — aim for under 100 per frame
- **Instancing and batching can reduce draw calls by 90%+**
- Dispose everything: geometries, materials, textures, render targets

## Most Relevant Tips for Medical 3D Viewer

### WebGPU Renderer (Tips 1-20)
- Use `instancedArray` for GPU-persistent buffers
- Move particle systems to compute shaders
- Use `renderAsync` for compute-heavy scenes
- Use storage textures for read-write compute
- Minimize buffer updates per frame
- Use indirect draws for GPU-driven rendering

### Asset Optimization (Tips 21-29)
- Compress geometry with **Draco** or **Meshopt**
- Use **KTX2** texture compression (UASTC for quality, ETC1S for size)
- Master `gltf-transform` CLI
- Implement **LOD** (Level of Detail)
- Atlas textures to reduce binds

### Draw Call Optimization (Tips 30-36)
- Target under 100 draw calls/frame
- Use `InstancedMesh` for repeated objects (anatomical symmetry!)
- Use `BatchedMesh` for varied geometries
- Share materials between meshes
- Merge static geometry with `BufferGeometryUtils`

### Memory Management (Tips 37-42)
- Dispose ALL GPU resources when done
- Use object pooling for spawned entities
- Dispose render targets

### Mobile-Specific (Tips 43-47)
- Use **mediump precision** on mobile
- Minimize varying variables
- Replace conditionals with `mix()` and `step()`
- Pack data into RGBA channels
- Avoid dynamic loops

### Shaders (Tips 48-52)
- Prefer **TSL** over raw GLSL/WGSL
- Build custom effects with node materials
- Write reusable TSL functions with `Fn`
- Use TSL's built-in noise functions

### Lighting (Tips 53-62)
- Limit active lights to 3 or fewer
- Bake lightmaps for static scenes (anatomy is static!)
- Use Cascaded Shadow Maps for large scenes
- Disable shadow auto-update for static scenes

### Loading (Tips 83-90)
- Lazy load 3D content below the fold
- Code-split Three.js modules
- Implement progressive loading
- Offload heavy work to Web Workers
- Stream large scenes
- Use placeholder geometry during load

## Action Items for SOMA
1. Migrate to WebGPU renderer with WebGL2 fallback
2. Replace GLSL shaders with TSL for forward compatibility
3. Implement LOD for anatomy models (close = full detail, far = simplified)
4. Use Draco compression on all GLTF/GLB anatomy assets
5. Bake lightmaps since anatomy is static geometry
6. Use InstancedMesh for bilateral symmetric structures
7. Target <100 draw calls per frame on mobile
8. Use mediump precision on mobile for subsurface scattering


## Sources

- https://www.utsubo.com/blog/threejs-best-practices-100-tips
