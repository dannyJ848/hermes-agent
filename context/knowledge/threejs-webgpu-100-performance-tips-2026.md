# threejs-webgpu-100-performance-tips-2026

*Researched: 2026-04-06 05:48 CDT*

# Three.js + WebGPU: 100 Performance Tips (2026)

**Source:** Utsubo blog, Mar 2026 — comprehensive guide for production Three.js apps

## Key Takeaways for SOMA
- **WebGPU production-ready since Three.js r171** — zero-config imports with automatic WebGL2 fallback
- **Draw calls target: under 100/frame** — instancing and batching can reduce by 90%+
- **TSL (Three Shader Language)** is the future — write once, run on WebGPU or WebGL
- **Bake everything possible** — lightmaps, shadows, AO

## Most Relevant Tips for Medical 3D Anatomy Viewer

### WebGPU Renderer (Tips 1-20)
- `import WebGPURenderer` with async init, auto WebGL2 fallback
- Move particle systems to compute shaders (tip 4)
- Use `instancedArray` for GPU-persistent buffers (tip 5)
- Use compute shaders for physics simulation (tip 17)
- Generate geometry/terrain with compute shaders (tip 18-19)
- Use indirect draws for GPU-driven rendering (tip 20)
- Use storage textures for read-write compute (tip 13)
- Chrome WebGPU DevTools available for debugging (tip 15)

### Asset Optimization (Tips 21-29)
- **Draco compression** for geometry (tip 21)
- **KTX2** for texture compression — UASTC for quality, ETC1S for size (tips 22-23)
- **gltf-transform CLI** for asset pipeline optimization (tip 24)
- **Implement LOD** (tip 26) — critical for anatomy models
- **Meshopt as Draco alternative** (tip 29) — may be better for anatomy meshes
- Atlas textures to reduce binds (tip 27)

### Draw Call Optimization (Tips 30-36)
- Target under 100 draw calls per frame (tip 30)
- `InstancedMesh` for repeated anatomy structures (tip 31)
- `BatchedMesh` for varied geometries (tip 32)
- Merge static geometry with `BufferGeometryUtils` (tip 34)

### Memory Management (Tips 37-42)
- **Dispose ALL GPU resources** when done — geometries, materials, textures (tip 37)
- Object pooling for spawned entities (tip 39)
- Cache and reuse textures (tip 40)
- Clean up on component unmount in React (tip 42)

### Mobile-Specific (Tips 43-44)
- Use `mediump` precision on mobile (tip 43) — critical for iOS Safari
- Minimize varying variables (tip 44)

### Loading (Tips 83-90)
- Lazy load 3D content below fold (tip 83)
- Implement progressive loading (tip 86)
- Offload heavy work to Web Workers (tip 87)
- Stream large scenes (tip 88)
- Use placeholder geometry during load (tip 89)

### LOD Specifically (tip 26, 68)
- Use Drei's `<Detailed>` component for LOD in R3F
- Implement multiple detail levels per anatomy structure

## Action Items for SOMA
1. Migrate to WebGPU renderer with WebGL2 fallback
2. Apply Draco/Meshopt compression to anatomy GLTF models
3. Implement LOD for complex anatomy structures (skeleton, muscular system)
4. Target <100 draw calls per frame
5. Use compute shaders for any real-time mesh processing
6. Implement progressive loading with placeholder geometry
7. Use `mediump` precision for mobile Safari compatibility


## Sources

- https://www.utsubo.com/blog/threejs-best-practices-100-tips
