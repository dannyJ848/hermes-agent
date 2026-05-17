# threejs-performance-tips-soma-2026

*Researched: 2026-04-07 11:52 CDT*

# Three.js Performance Tips for SOMA (2026 Edition)

Source: "100 Three.js Tips That Actually Improve Performance (2026)" by Utsubo

## Most Relevant Tips for SOMA 3D Anatomy Viewer

### WebGPU Renderer (Future-proofing)
1. **Zero-config WebGPU import with async init** — Use `WebGPURenderer` with automatic WebGL2 fallback
2. **Compute shaders for particle systems** — Move to GPU for histology/cell visualizations
3. **InstancedArray for GPU-persistent buffers** — Anatomy instances can stay on GPU
4. **2-10x performance gains in specific scenarios** — Particularly draw-call heavy scenes
5. **TSL (Three Shader Language)** — Replaces raw GLSL/WGSL for custom anatomy shaders (SSS, translucency)

### Asset Optimization (Critical for SOMA)
- **Draco compression** for geometry — essential for large anatomy meshes
- **KTX2 texture compression** — UASTC for quality (organs), ETC1S for size (skin surfaces)
- **LOD (Level of Detail)** — Lower-poly models when zoomed out, full detail when close
- **gltf-transform CLI** — Batch optimize all anatomy GLB files
- **Meshopt as Draco alternative** — Better decompression speed on mobile

### Draw Call Optimization
- **Target under 100 draw calls per frame** — SOMA must batch anatomy parts
- **InstancedMesh** for repeated anatomical structures (vertebrae, ribs, teeth)
- **BatchedMesh** for varied geometries — group different organ meshes
- **Merge static geometry** with BufferGeometryUtils — combine non-interactive bones
- **Frustum culling** — only render visible anatomy

### Memory Management
- **Dispose all GPU resources** when switching body systems
- **Object pooling** for spawned medical annotations
- **Cache and reuse textures** — shared skin/muscle textures across models

### Shaders for Medical Rendering
- **mediump precision on mobile** — sufficient for anatomy, halves GPU cost
- **Pack data into RGBA channels** — encode tissue properties (density, opacity, color)
- **Replace conditionals with mix()/step()** — smoother tissue transitions
- **TSL noise functions** — organic tissue variation (vein patterns, skin texture)

### Lighting for Anatomy
- **Limit active lights to 3** — key, fill, rim for anatomical clarity
- **Bake lightmaps for static scenes** — pre-computed lighting on reference anatomy
- **Environment maps for ambient** — medical exam room lighting
- **Cascaded Shadow Maps** — accurate organ shadows at all zoom levels

### Mobile-Specific (SOMA iOS)
- **Lazy load 3D content** below the fold — load body systems on demand
- **Progressive loading** — show low-poly first, stream high-poly
- **Web Workers for heavy computation** — keep UI thread free on mobile
- **Code-split Three.js modules** — only load what the current view needs


## Sources

- https://www.utsubo.com/blog/threejs-best-practices-100-tips
