# threejs-auto-lod-generation-mobile

*Researched: 2026-04-05 12:52 CDT*

# Three.js Auto-LOD Generation for Mobile Anatomy Rendering

## Key Finding: SimplifyModifier for SOMA LOD Pipeline

Three.js provides `SimplifyModifier` (addon: `three/addons/modifiers/SimplifyModifier.js`) for automatic mesh decimation. Based on Stan Melax's 1998 Progressive Mesh Polygon Reduction algorithm.

### How It Works
```js
import { SimplifyModifier } from 'three/addons/modifiers/SimplifyModifier.js';
const modifier = new SimplifyModifier();
const simplified = modifier.modify(geometry, verticesToRemove);
// Returns NEW non-indexed BufferGeometry
```

### Critical Caveats for SOMA
1. **Output is always non-indexed** — loses index buffer optimization. For anatomy meshes with shared vertices, this can INCREASE memory despite fewer triangles.
2. **All LOD levels stay in GPU memory** — Three.js keeps every LOD mesh loaded, even non-visible ones. For 10+ anatomy models × 3 LOD levels, memory budget matters on mobile.
3. **Draw calls don't increase** — LOD swaps meshes, doesn't add renders. The cost is memory, not draw calls.
4. **Runtime generation is expensive** — SimplifyModifier is CPU-bound. For SOMA, generate LODs at build time, not on device.

### Recommended SOMA Approach
Instead of runtime SimplifyModifier, use **offline decimation** during the asset pipeline:
1. Export anatomy models at 3 detail levels from Blender (high/medium/low)
2. Use `THREE.LOD` to manage distance-based switching
3. Thresholds for mobile: near (<3m) = full, mid (<8m) = 50% triangles, far = 25% triangles
4. Consider replacing distant anatomy with billboard sprites (impostors) for extreme optimization

### When LOD Actually Helps (Forum Consensus, Oct 2025)
- Vast open scenes with many objects (SOMA: yes, full body scan)
- High-poly static models (SOMA: yes, anatomical meshes 100k+ triangles)
- NOT for dynamically created/modified geometry (SOMA: models are static, good fit)

### Alternative: Parameter-Based LOD for Primitives
For cylindrical/box primitives in anatomy scaffolding:
- Reduce radial segments on cylinders (32 → 16 → 8)
- Fewer subdivisions on spheres
- This is faster than SimplifyModifier and preserves indexed geometry

### Integration Path
1. Create `LODManager.ts` in SOMA that wraps `THREE.LOD`
2. During model loading, generate or load pre-computed LOD levels
3. Wire into SOMA's `AnatomyViewer` scene graph
4. Add distance-based switching with configurable thresholds
5. Monitor GPU memory on iOS to tune thresholds

## Sources
- Three.js docs: SimplifyModifier
- Three.js forum discussion: "When is LOD beneficial?" (Oct 2025)
- Forum: "THREE.SimplifyModifier vs Progressive Mesh Streaming"


## Sources

- https://threejs.org/docs/pages/SimplifyModifier.html
- https://discourse.threejs.org/t/when-is-it-actually-beneficial-to-use-lod-in-three-js-for-performance/87697
- https://discourse.threejs.org/t/three-simplifymodifier-vs-progressive-mesh-streaming/4460
