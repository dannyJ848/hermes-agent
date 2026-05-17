# threejs-mobile-performance-optimization

*Researched: 2026-04-05 21:58 CDT*

# Three.js Mobile Performance Optimization for Anatomy Viewers

## Source: CoderLegion (2025) — Practical optimization guide

### Key Findings for SOMA

#### 1. Low-Polygon Models
- **Budget**: 1,000-5,000 triangles per object for mobile (vs 50K+ for desktop)
- Anatomy meshes should target 2,000-5,000 triangles per organ
- Memory: high-poly (50K tris) = 5-10 MB GPU memory; low-poly (2K tris) = <1 MB
- Critical for devices with 2-4 GB RAM (budget smartphones)

#### 2. Level of Detail (LOD)
- Implement LOD system: switch to lower-poly versions when objects are far from camera
- Essential for full-body anatomy views where distant organs need simplified geometry
- Three.js `LOD` class built-in: `new THREE.LOD()` with `addLevel(mesh, distance)`

#### 3. Simplified Shaders
- Replace PBR (physically based rendering) with Lambertian lighting on mobile
- Flat shading (`flatShading: true`) reduces fragment shader complexity
- For anatomy: simple diffuse + slight subsurface scattering approximation is enough
- Avoid real-time shadows on mobile — use baked ambient occlusion instead

#### 4. Instancing for Repeated Geometry
- Use `InstancedMesh` for repeated structures (blood vessels, vertebrae, teeth)
- Single draw call for all instances — massive GPU savings
- Example: `new THREE.InstancedMesh(geometry, material, count)`

#### 5. Performance Targets
- Mobile FPS target: 30 FPS minimum, 60 FPS ideal
- Budget device GPU examples: Adreno 610, Mali-G57, Mali-G52
- Resolution: 720p on budget devices, auto-detect capability via `renderer.capabilities`

#### 6. Specific to Medical/Anatomy Apps
- Mesh decimation tools (Blender, Maya) preserve essential anatomical shapes
- Consider separate mesh quality tiers: desktop (high), tablet (medium), phone (low)
- Baked ambient occlusion maps give depth perception without runtime shadow cost
- Texture atlas consolidation reduces draw calls (multiple organs → one texture atlas)

### Implementation Priority for SOMA
1. Add auto-detect for GPU capability → select mesh quality tier
2. Implement LOD for organ groups (close-up vs full-body view)
3. Create mobile-specific decimated meshes (2K-5K tris per organ)
4. Replace shadow maps with baked AO on mobile
5. Use InstancedMesh for repeated anatomical structures


## Sources

- https://coderlegion.com/4191/performance-of-three-mobile-devices-and-lower-end-hardware-for-games-and-creative-resumes
- https://medium.com/@coders.stop/optimizing-performance-in-three-js-rendering-smoothly-on-low-end-devices-e48d2cc516cc
