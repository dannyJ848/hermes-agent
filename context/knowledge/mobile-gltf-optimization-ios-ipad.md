# mobile-gltf-optimization-ios-ipad

*Researched: 2026-04-05 15:32 CDT*

# Mobile GLTF/GLB Optimization for iOS (iPad/iPhone) in Three.js

## Key Finding (April 2026)

**The bottleneck on iOS is NOT vertex/face count — it's draw calls and texture memory.**

### Evidence
- Stack Overflow case study: A model with MORE vertices loaded fine on iPad, while a "lighter" model with fewer vertices crashed. The difference: the lighter model had more meshes and more draw calls.
- Draco compression is a false optimization for mobile rendering. It only reduces file transfer size — once decompressed, the mesh uses identical GPU memory.
- Texture sizes are the #1 memory killer on iOS. Single-color textures (roughness, metalness) at 2048x2048px can be reduced to 16x16px or even 1x1px without visual difference.

### Actionable Rules for SOMA
1. **Merge meshes aggressively** — Combine anatomical structures into fewer draw calls. Each mesh = 1 draw call. iOS Safari has a hard memory limit (~1.5-2GB for WebGL).
2. **Reduce texture sizes** — Solid-color PBR maps (roughness, metalness) can be 16x16px or even 1x1px. Diffuse/normal maps at 512x512px maximum for mobile.
3. **Draco is for loading speed, not rendering** — Use Draco for faster downloads but don't expect it to help with memory/rendering performance.
4. **Use GLTFPack** — Tool from the gltf-transform ecosystem. Can compress 100MB glTF files to ~2MB. Merges meshes, strips unused data, quantizes attributes.
5. **Monitor draw calls** — Target <100 draw calls for mobile. Each anatomical system (skeletal, muscular, etc.) should be one merged mesh, not hundreds of individual bones/muscles.

### SOMA-Specific Recommendations
- ZAnatomy/BodyParts3D models likely have hundreds of separate meshes per body system
- Implement a build pipeline: Source GLTF → GLTFPack (merge + quantize) → Draco compress → Final GLB
- Consider texture atlasing: combine many small textures into one atlas per body system
- For iOS WKWebView, the memory ceiling is even lower than Safari — be extra aggressive

### Tools
- `gltfpack` (from meshoptimizer): CLI tool for mesh merging, simplification, quantization
- `gltf-transform`: JS library for programmatic GLTF optimization (can be scripted)
- `DRACOLoader`: Three.js loader for Draco-compressed GLTF files
- `MeshoptDecoder`: Alternative to Draco, often better decompression speed on mobile

### Sources
- https://stackoverflow.com/questions/54588165/3d-gltf-model-rendering-optimization-threejs
- https://discourse.threejs.org/t/gltf-model-rendering-optimization/6049
- https://threejs.org/docs/pages/DRACOLoader.html


## Sources

- https://stackoverflow.com/questions/54588165/3d-gltf-model-rendering-optimization-threejs
- https://discourse.threejs.org/t/gltf-model-rendering-optimization/6049
- https://threejs.org/docs/pages/DRACOLoader.html
