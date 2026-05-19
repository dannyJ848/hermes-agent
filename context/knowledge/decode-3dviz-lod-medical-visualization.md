# DECODE-3DViz LOD Medical Visualization

*Researched: 2026-04-05 12:46 CDT*

# DECODE-3DViz: LOD + Chunk Streaming for WebGL Medical Visualization

**Source:** AboArab et al., J Imaging Inform Med, 2025. DOI: 10.1007/s10278-025-01430-9

## Key Innovation
A WebGL-based pipeline for high-fidelity 3D visualization of large-scale medical imaging data (CT scans of peripheral arteries) using two core techniques:
1. **Level of Detail (LOD)** — Progressive mesh resolution based on camera distance
2. **Data Chunk Streaming** — Streaming volumetric data in chunks rather than loading entire datasets

## Relevance to SOMA
- **Mobile LOD Strategy**: SOMA should implement distance-based LOD for anatomy meshes. High-detail meshes (>500K triangles) should have 3-4 LOD levels:
  - LOD0: Full detail (< 2m camera distance)
  - LOD1: 50% reduction (2-5m)
  - LOD2: 25% reduction (5-10m)  
  - LOD3: Wireframe or bounding box (> 10m)
- **Chunk Streaming**: For SOMA's encyclopedia entries with embedded 3D models, stream mesh data progressively instead of blocking on full load.
- **WebGL Compatibility**: This approach works in WebGL2 (no WebGPU dependency), which is critical for iOS Safari.

## Technical Details
- Uses progressive mesh decimation for LOD generation
- Chunk-based loading reduces initial memory footprint
- Specifically validated on CT angiography datasets
- Real-time interactive frame rates achieved in browser

## Architecture Pattern for SOMA
```
LODManager (Three.js)
├── Auto-LOD: Use THREE.SimplifyModifier or Blender decimate at build time
├── Runtime: Switch LOD based on camera.frustum.containsPoint + distance
├── Memory budget: Cap total triangles at 2M for mobile, 5M for desktop
└── Preload: Load LOD3 (wireframe) first, then progressively load higher LODs
```

## Action Items for SOMA
1. Generate LOD variants at build time using `gltf-transform` or Blender
2. Implement `LODManager` component that uses Three.js `THREE.LOD` class
3. Set triangle budgets per device capability (detect via `renderer.capabilities`)
4. Test on iOS Safari with complex anatomy models


## Sources

- https://pmc.ncbi.nlm.nih.gov/articles/PMC12701164/
- https://discourse.threejs.org/t/a-3d-interactive-system-for-exploring-human-anatomy-by-anatomical-layers/88813
