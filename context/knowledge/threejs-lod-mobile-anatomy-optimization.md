# threejs-lod-mobile-anatomy-optimization

*Researched: 2026-04-05 18:39 CDT*

# Three.js LOD & Mobile Anatomy Optimization Strategy

## Key Finding (Oct 2025, Three.js Forum)

**LOD (THREE.LOD) is the LAST optimization to consider**, not the first. For anatomy models on mobile:

### Why LOD Falls Short
- Three.js keeps ALL LOD meshes in GPU memory, even invisible ones
- For dynamically-generated geometry, LOD adds overhead (regenerating levels on modification)
- LOD only shines with static, pre-built assets at vastly different detail levels

### Better Optimization Hierarchy (in order)
1. **Instancing** — Use 1 material for the entire scene, use textures/shaders to differentiate
2. **Batching** — Merge geometries sharing the same material
3. **Line-based far rendering** — Cylindrical structures (bones, vessels) can render as lines when distant — indistinguishable from cylinders at distance, vastly cheaper
4. **Impostors** — Billboard sprites for distant objects (complex to implement)
5. **LOD** — Only as last resort, for predefined static models with pre-built detail levels

### Application to SOMA Anatomy Viewer
- **Bones/vessels**: Render as lines when zoomed out, switch to geometry on zoom
- **Shared materials**: Single PBR material for all bone tissue, single for muscle, etc.
- **Batch static anatomy**: Merge non-interactive anatomical structures into single draw calls
- **Dynamic LOD for glTF models**: Pre-build 3 detail levels (high/med/low poly) in Blender, load based on device capability
- **Mobile triangle budget**: Target 100K triangles on mobile, 500K on desktop

### Sources
- Three.js Forum discussion (Oct 2025): LOD practicality in industrial scenes
- Three.js LOD docs: https://threejs.org/docs/pages/LOD.html


## Sources

- https://discourse.threejs.org/t/when-is-it-actually-beneficial-to-use-lod-in-three-js-for-performance/87697
- https://threejs.org/docs/pages/LOD.html
