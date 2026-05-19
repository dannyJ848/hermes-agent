# LOD caveats for close-up anatomy models in Three.js

*Researched: 2026-04-05 15:37 CDT*

# LOD (Level of Detail) Caveats for Close-Up Anatomy Models in Three.js

## Date: 2026-04-05 | Domain: 3D Rendering / Medical Visualization

## Core Problem
Standard LOD assumes objects are viewed at varying distances. But **anatomy apps invert this**: the camera is ALWAYS close (examining organs, bones, vessels). Distance-based LOD switching is nearly useless when the model is perpetually "near."

## Key Caveats for SOMA

### 1. Distance-Based LOD Doesn't Apply
- Three.js `THREE.LOD` switches geometry based on camera distance
- Anatomy viewers keep camera 0.5–3 units from the model at all times
- All LOD levels would resolve to "high detail" — no savings gained
- **Verdict:** Skip standard LOD for SOMA's primary interaction mode

### 2. Where LOD CAN Help in Anatomy Apps
- **Whole-body overview mode** (zoomed out, all systems visible) → use LOD to reduce poly count
- **Background structures** — organs behind the selected system can be lower detail
- **Cross-section views** — clipped-away parts don't need full resolution
- **Layer culling** — hidden layers (e.g., skin when viewing skeleton) should be fully culled, not just LOD-reduced

### 3. Alternative: Selective Detail Strategies
Instead of distance-based LOD, use these approaches:
- **Per-system poly budgets:** Skeleton gets more polys than veins (vessels are thin tubes, less detail needed)
- **On-demand tessellation:** Subdivide only the organ the user clicks/interacts with
- **Displacement maps instead of geometry:** Use bump/displacement maps for surface detail (wrinkles, muscle fiber texture) rather than actual geometry — reduces vertex count dramatically
- **Texture baking:** Bake high-res sculpt detail into normal maps applied to low-poly meshes

### 4. Bump Mapping as a LOD Substitute
- Grayscale bump maps simulate surface detail without extra polygons
- Works well for: muscle striations, bone texture, skin pores
- Performance cost: negligible compared to equivalent polygon detail
- Limitation: silhouette remains low-poly (visible at edges)

### 5. Progressive Loading is Better Than LOD
For SOMA's use case:
1. Load skeleton first (lowest poly, establishes spatial reference)
2. Load muscles (medium poly, user can start exploring)
3. Load organs/vessels/nerves progressively as needed
4. Full-resolution textures stream in lazily

This gives perceived performance without wasting effort on distance LOD that never triggers.

## Implementation Recommendation for SOMA
```
LOD: NO (distance-based switching)
Progressive loading: YES (skeleton → muscles → organs → details)
Bump/normal maps: YES (replace geometry detail)
Per-system budgets: YES (different poly limits per anatomical system)
Culling hidden layers: YES (don't render invisible systems at all)
```

## Sources
- CG-Wire LOD article (2026): https://blog.cg-wire.com/lod-levels-of-detail/
- Three.js LOD docs: https://threejs.org/docs/pages/LOD.html
- Three.js anatomy system thread: https://discourse.threejs.org/t/a-3d-interactive-system-for-exploring-human-anatomy-by-anatomical-layers/88813


## Sources

- https://blog.cg-wire.com/lod-levels-of-detail/
- https://threejs.org/docs/pages/LOD.html
- https://discourse.threejs.org/t/a-3d-interactive-system-for-exploring-human-anatomy-by-anatomical-layers/88813
