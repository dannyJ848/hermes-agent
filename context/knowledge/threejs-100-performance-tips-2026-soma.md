# threejs-100-performance-tips-2026-soma

*Researched: 2026-04-07 13:01 CDT*

# 100 Three.js Performance Tips (Utsubo, March 2026) - SOMA-Relevant Selection

## Most Relevant for SOMA

### Draw Calls (Target: <100 per frame)
- #30 Target under 100 draw calls per frame
- #31 Use InstancedMesh for repeated objects (e.g., vertebrae, teeth)
- #32 Use BatchedMesh for varied geometries (different organs)
- #33 Share materials between meshes (tissue-type materials)
- #34 Merge static geometry with BufferGeometryUtils
- #35 Use array textures for modern browsers

### Mobile-Specific
- #43 Use mediump precision on mobile (saves GPU bandwidth)
- #66 Never create objects inside useFrame (GC pressure)
- #44 Minimize varying variables in shaders
- #45 Replace conditionals with mix() and step()

### Memory (iOS 350MB limit!)
- #37 Dispose all GPU resources when done
- #38 Handle ImageBitmap textures from GLTF specially
- #39 Use object pooling for spawned entities
- #41 Dispose render targets
- #42 Clean up on component unmount (React)

### R3F Specific
- #63 Mutate in useFrame, don't setState (critical perf tip)
- #64 Use frameloop="demand" for static scenes
- #69 Preload models with useGLTF.preload
- #70 Wrap expensive components in React.memo
- #71 Toggle visibility instead of remounting (SOMA layers!)

### Lighting
- #53 Limit active lights to 3 or fewer
- #55 Bake lightmaps for static scenes
- #59 Use environment maps for ambient light
- #61 Disable shadow auto-update for static scenes

### Asset Loading
- #83 Lazy load 3D content below the fold
- #85 Preload critical assets
- #86 Implement progressive loading
- #87 Offload heavy work to Web Workers

### WebGPU Notes
- #2 Trust the automatic WebGL 2 fallback
- #8 Use forceWebGL strategically (confirms our WebGL2 approach)
- #10 Use node materials for dynamic customization (TSL approach)

## Source
- URL: https://www.utsubo.com/blog/threejs-best-practices-100-tips
- Author: Jocelyn Lecamus, Utsubo
- Date: March 22, 2026


## Sources

- https://www.utsubo.com/blog/threejs-best-practices-100-tips
