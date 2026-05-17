# threejs-lod-anatomy-performance

*Researched: 2026-04-05 21:46 CDT*

# Three.js LOD & Large Model Performance for Anatomy Viewers

## Key Finding (Oct 2025, Three.js Discourse)
**THREE.LOD may NOT improve performance** for dynamic/complex scenes — in tests it slightly worsened it.

### Why LOD Fails for Dynamic Scenes
- Three.js keeps ALL LOD mesh levels in GPU memory, even non-visible ones
- For dynamically created/modified geometry, maintaining consistent LOD meshes is impractical
- LOD is designed for static, predefined models (buildings, open-world terrain)
- Per-mesh overhead of LOD objects adds up with thousands of objects

### Better Optimization Strategy for SOMA (Ordered by Impact)
1. **Instancing** — Use 1 material for entire scene, adjust via shaders/textures per element
2. **Batching** — Merge geometries that share materials to reduce draw calls
3. **Line rendering at distance** — Cylindrical elements (vessels, bones) become indistinguishable from Lines far away; Lines are WAY cheaper
4. **Geometry simplification at source** — Reduce polygon count in Blender/glTF export, not at runtime
5. **Impostors** (last resort) — Replace distant 3D with billboard sprites; overkill for non-open-world

### SOMA-Specific Recommendations
- Anatomy models are typically static once loaded → LOD IS viable for organ meshes
- But organs are viewed close-up → LOD levels rarely activate
- Better approach: **multiple resolution glTF exports** (high/medium/low) chosen at load time based on device capability
- Use `SimplifyModifier` only for preprocessing, never at runtime on mobile
- For vascular/tubular structures: use `LineSegments` or `TubeGeometry` with minimal segments when zoomed out

### Draw Call Monitoring
- Check draw calls with/without LOD — they should stay the same
- If draw calls increase with LOD, both meshes are rendering simultaneously (misconfiguration)
- Monitor with `renderer.info.render.calls` in Three.js debug mode

## Sources
- Three.js Discourse: "When is LOD beneficial?" (Oct 2025)
- Reddit r/threejs: "Handling huge GLTF/GLB models 1-10M polygons" (referenced IFC optimizations)


## Sources

- https://discourse.threejs.org/t/when-is-it-actually-beneficial-to-use-lod-in-three-js-for-performance/87697
- https://www.reddit.com/r/threejs/comments/1pnnlm4/handling_huge_gltfglb_models_in_threejs_110m/
