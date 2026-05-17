# draco-gltf-compression-soma-asset-pipeline

*Researched: 2026-04-05 13:25 CDT*

# Draco Compression for SOMA Anatomy Models

**Date:** 2025-04-05
**Relevance:** Tier 1 — SOMA 3D asset pipeline optimization

## Summary
Google Draco compression can reduce glTF/GLB mesh geometry by **~95%** for models over 1MB. This is directly applicable to SOMA's anatomy models (Z-Anatomy, BodyParts3D exports), which are typically multi-MB meshes.

## Key Technical Findings

### Compression Ratios
- **Models >1MB geometry:** ~95% file size reduction typical
- **Models <1MB geometry:** WASM decoder (~150KB) may outweigh savings — NOT recommended for tiny meshes
- **Textures NOT compressed** by Draco — use `KHR_texture_basisu` (KTX2) for texture compression separately
- **Animations:** Draco handles mesh geometry only; animation data requires separate optimization

### Three.js Integration (DRACOLoader)
```javascript
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('/examples/jsm/libs/draco/');
// Auto-selects JS vs WASM based on browser capabilities

const gltfLoader = new GLTFLoader();
gltfLoader.setDRACOLoader(dracoLoader);
```
- Reuse ONE DRACOLoader instance to avoid loading multiple decoder copies
- `setWorkerLimit(n)` controls Web Worker count for parallel decoding
- WASM decoder preferred where supported (all modern browsers + WKWebView)

### Critical Architecture Insight: Transfer vs Runtime
**Draco is a TRANSFER optimization, NOT a runtime optimization.**
- Decompression happens **before** GPU upload
- Draco-compressed geometry uses the same GPU memory as uncompressed
- For runtime FPS improvement, geometry **simplification** (reducing vertex count) is required
- This complements the LOD work (previous cycles): **Draco for transfer + LOD levels for runtime**

### Tooling: gltf-transform CLI
```bash
# Install
npm install -g @gltf-transform/cli

# Apply Draco compression
gltf transform input.glb output.glb --draco

# With options
gltf transform input.glb output.glb --draco --quantize
```
`gltf-transform` is the modern successor to `gltf-pipeline`. Supports Draco, Meshopt, simplification, texture compression in one pass.

### Alternative: Meshopt (EXT_meshopt_compression)
- Also available via gltf-transform (`--meshopt`)
- GPU-friendly format — no full decompression needed before upload
- Lower compression ratio than Draco but faster decode
- Better for streaming/lazy-loading scenarios
- **Recommendation for SOMA:** Use Draco for initial download, Meshopt for streaming LOD levels

## SOMA Integration Path

### Asset Pipeline (build-time)
1. Source anatomy GLB from Z-Anatomy/BodyParts3D
2. `gltf-transform` pipeline: dedup → simplify (LOD levels) → draco → ktx2 textures → output
3. Generate 3 LOD levels per model (high/med/low vertex counts)
4. Each LOD level independently Draco-compressed

### Runtime Loading
1. DRACOLoader + GLTFLoader in SOMA's model loading system
2. Load LOD level based on device capability (detected via renderer caps)
3. Progressive: start with low LOD, upgrade to high LOD in background
4. Cache decoded geometry in IndexedDB for repeat visits

### Mobile Performance Notes
- WKWebView (iOS) supports WASM decoder — no issue
- Decoding on mobile adds ~100-500ms latency per model
- Trade-off: 5-10x faster download vs 100-500ms decode overhead
- Net positive for models >500KB

## Cross-References
- LOD Strategy: `~/.hermes/knowledge/decode-3dviz-lod-medical-visualization.md`
- Three.js LOD: `~/.hermes/knowledge/threejs-auto-lod-generation-mobile.md`
- FHIR Integration: `~/.hermes/knowledge/fhir-imagingselection-3d-regions-soma.md`

## Sources
- https://github.com/google/draco (Google Draco, Apache-2.0, 7.2k stars)
- https://gltf-transform.dev/modules/extensions/classes/KHRDracoMeshCompression
- https://threejs.org/docs/pages/DRACOLoader.html


## Sources

- https://github.com/google/draco
- https://gltf-transform.dev/modules/extensions/classes/KHRDracoMeshCompression
- https://threejs.org/docs/pages/DRACOLoader.html
- https://cesium.com/blog/2018/04/09/draco-compression/
