# threejs-lod-vs-instancing-mobile-performance

*Researched: 2026-04-06 14:52 CDT*

# Three.js LOD vs Instancing for Mobile Performance

**Source:** Three.js Discourse + Utsubo 100 Tips (Oct 2025)

## Key Findings

### LOD is LAST resort optimization
- THREE.LOD keeps ALL levels in GPU memory simultaneously — low and high poly versions
- For dynamically-created geometry (like SOMA's anatomy parts), LOD may HURT performance since every mesh needs 2-3 copies
- LOD works best for **static, pre-created models** (buildings, large assets in open worlds)
- Draw calls should NOT increase with LOD — if they do, both meshes are being rendered (bug)

### Better optimization hierarchy for SOMA:
1. **Instancing** — Use 1 material for entire scene, vary appearance via shaders/textures per instance
2. **Geometry batching** — Merge static geometries into single draw calls
3. **Line impostors for distant objects** — Cylinders far from camera can't be distinguished from lines; render as `LineSegments` instead (10x cheaper)
4. **Radial segment reduction** — For cylinders/pipes, reduce `radialSegments` from 32→8 for distant objects
5. **Impostors (billboards)** — Last resort for far-away complex geometry
6. **LOD** — Only after all above are exhausted

### SOMA-specific application:
- Anatomy meshes are loaded from GLB (static per model) — LOD IS appropriate here
- But for dynamically-spawned label lines, wireframes, cross-section indicators — use instancing
- Mobile: keep triangle budget under 500K total, target 30fps on iPhone 12
- LOD can improve frame rates 30-40% in large scenes (Utsubo tip)

### Memory tradeoff:
- LOD levels in GPU memory: acceptable for pre-built GLB anatomy models (finite set)
- NOT acceptable for user-generated/dynamic content (infinite set, GPU bloat)


## Sources

- https://discourse.threejs.org/t/when-is-it-actually-beneficial-to-use-lod-in-three-js-for-performance/87697
- https://www.utsubo.com/blog/threejs-best-practices-100-tips
