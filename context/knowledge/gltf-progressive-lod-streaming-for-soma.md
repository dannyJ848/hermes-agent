# gltf-progressive-lod-streaming-for-soma

*Researched: 2026-04-05 13:28 CDT*

# Progressive glTF LOD Streaming for SOMA

## Source
[@needle-tools/gltf-progressive](https://engine.needle.tools/docs/gltf-progressive/) — standalone npm module for any Three.js project.

## Key Findings

### What it does
- Creates a tiny initial file with embedded low-quality proxies PLUS higher-quality LOD files that stream on demand
- Mesh LODs loaded lazily based on **screen density** (not just distance)
- Texture LODs stream progressively from low-res to full quality
- Automatic mobile optimization and quality reduction

### Performance impact
- 56 MB asset → 300 KB initial download, with up to 8 MB progressive streaming
- Most users never need full 8 MB because 4K textures only load on zoom
- ~90% smaller initial download vs standard gltf-transform

### SOMA Relevance
1. **Mobile-first anatomy**: SOMA on iOS can load anatomy proxy meshes instantly, then stream detail as user navigates
2. **Bilingual labels**: Low-poly LOD proxies can include label geometry; full detail streams for focused study
3. **Memory budget**: Keeps mobile GPU memory low by only loading visible LODs
4. **Single-line integration**: Works with vanilla Three.js — no framework lock-in

### Comparison with Draco
| Feature | Draco | Meshopt | gltf-progressive |
|---------|-------|---------|------------------|
| Compression | ~95% geometry | ~70% geometry + GPU-friendly | N/A (uses Meshopt/Draco) |
| Runtime cost | Full decompress before GPU | Direct GPU upload | Progressive streaming |
| Initial load | Full file | Full file | 300KB proxy |
| LOD support | None | None (external tooling) | Built-in density LOD |

### Integration Path for SOMA
1. `npm i @needle-tools/gltf-progressive`
2. Replace `GLTFLoader.load()` with progressive loader
3. Generate LOD assets via Needle Cloud CLI during build
4. LODManager.ts can leverage built-in density selection instead of manual LOD switching

### Recommended Pipeline (updated from cycle 212)
```
glTF source → gltf-transform (dedup + simplify) → @needle-tools/gltf-progressive (generate LOD tiers) → CDN
Runtime: progressive loader streams proxy → medium LOD → full LOD based on camera density
```


## Sources

- https://engine.needle.tools/docs/gltf-progressive/
- https://www.utsubo.com/blog/threejs-best-practices-100-tips
