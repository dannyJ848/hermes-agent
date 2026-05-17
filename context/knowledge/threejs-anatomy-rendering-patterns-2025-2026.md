# threejs-anatomy-rendering-patterns-2025-2026

*Researched: 2026-04-05 21:44 CDT*

# Three.js Anatomy Rendering Patterns (2025-2026)

## Transparency & Layering
- **renderOrder** is the key technique for fixing overlapping transparent anatomy meshes in Three.js. Set custom `renderOrder` values per mesh to control draw order.
- Use `transparent: true` on materials + animated opacity for smooth fade transitions between anatomical layers.
- Toggle visibility (`visible` property) is faster than opacity transitions but lacks visual polish.
- Multiple overlapping transparent objects require careful renderOrder management.

## Model Pipeline
- **Z-Anatomy** (free) is the go-to source for anatomy models in Blender→Three.js workflows.
- Blender models export as `.glb` files, imported via Three.js GLTFLoader.
- For 1-10M polygon models, community recommends: LOD (Level of Detail), frustum culling, and offloading parts to web workers.
- IFC loading patterns from architecture (three.js IFC.js) apply to anatomy — similar polygon budgets and hierarchical structure.

## Active Community Projects (2025-2026)
- Grzesiek Rogala's anatomy viewer (CodePen demo, Nov 2025) — layer toggle + opacity fade + annotations.
- Layer-Based Interactive 3D Human Anatomy Visualization System (Dec 2025 thread).
- Multiple developers independently building anatomy viewers with Three.js — common pattern: Blender → glb → GLTFLoader → per-mesh visibility/opacity.

## SOMA Integration Notes
- Our ZAnatomyLoader → GLBAnatomyModel pipeline follows the community-validated pattern.
- Need to implement renderOrder for transparent organ overlays (heart through ribcage, etc.).
- LOD system needed for mobile — anatomy models easily hit 5M+ triangles across full body.


## Sources

- https://discourse.threejs.org/t/feedback-on-a-three-js-project-human-anatomy/88151
- https://discourse.threejs.org/t/a-3d-interactive-system-for-exploring-human-anatomy-by-anatomical-layers/88813/4
- https://www.reddit.com/r/threejs/comments/1pnnlm4/handling_huge_gltfglb_models_in_threejs_110m/
