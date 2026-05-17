# threejs-lod-vs-instancing-mobile-optimization

*Researched: 2026-04-06 00:25 CDT*

# Three.js LOD vs Instancing for Dynamic 3D Scenes

**Date:** 2026-04-06
**Source:** Three.js Discourse + community consensus

## Key Finding
**THREE.LOD is the LAST optimization to consider for dynamic scenes.** For SOMA's anatomy viewer where meshes are loaded dynamically and the scene isn't open-world, LOD provides negligible benefit and may worsen performance.

## Why LOD Fails for Dynamic Scenes
- Three.js keeps ALL LOD meshes in GPU memory regardless of visibility
- For dynamically created/modified geometry, regenerating LOD levels is expensive and complex
- Overhead of managing LOD levels can exceed the rendering savings

## Recommended Optimization Priority (for SOMA)
1. **Instancing** — Use `InstancedMesh` for repeated anatomical structures (ribs, vertebrae, teeth). One material, one draw call for N instances.
2. **Batching** — Merge static geometries into single buffers where possible
3. **Distance-based simplification** — Render cylindrical/small elements as Lines when far from camera (indistinguishable visually, much cheaper)
4. **Impostors** — Only as last resort for open-world-scale scenes (overkill for medical viewers)

## SOMA Application
- Ribs (24 bones): Use InstancedMesh with transforms → 1 draw call instead of 24
- Vertebrae (33 bones): InstancedMesh → massive savings
- Teeth (32): InstancedMesh
- Blood vessels/tubes: Consider Line rendering at distance
- Organ models: Keep as-is (unique geometries, few instances)

## Bottom Line
For a medical anatomy viewer (closed scene, ~100-500 meshes, camera orbit around subject):
- LOD: Not worth the complexity
- Instancing of repeated structures: HIGH impact, LOW effort
- Triangle budget per mesh matters more than LOD levels


## Sources

- https://discourse.threejs.org/t/when-is-it-actually-beneficial-to-use-lod-in-three-js-for-performance/87697
