# KTX2-Basis-texture-compression-SOMA-mobile

*Researched: 2026-04-05 12:58 CDT*

# KTX2 / Basis Universal Texture Compression for SOMA Mobile

## TL;DR
Use **KTX2 with Basis Universal transcoder** (not raw .basis) for SOMA anatomy models. Single .ktx2 file per texture, auto-transcodes to optimal GPU format per device (ASTC for iOS, BC7 for desktop, ETC2 for Android). 6-8x size reduction over PNG/JPEG, and stays compressed in VRAM.

## Key Findings

### Format Choice: KTX2 > .basis
- KTX2 is a Khronos standardized container that wraps Basis Universal data
- Three.js natively supports KTX2 via `KHR_texture_basisu` glTF extension
- `KTX2Loader` handles automatic transcoding to device-optimal format
- .basis is the legacy format — KTX2 is the recommended successor

### UASTC vs ETC1S (Two Basis Modes)
- **ETC1S**: Smallest file size, lower quality (~6-8x compression). Good for diffuse/albedo textures
- **UASTC**: Higher quality, larger files (~4-6x compression). Better for normal maps, detail textures
- **Recommendation for SOMA**: ETC1S for diffuse anatomy textures (tissue colors tolerate compression), UASTC for normal maps (precision matters for surface detail)

### VRAM Savings (Critical for Mobile)
- A 200KB PNG can decompress to 20MB+ in VRAM (full RGBA32)
- KTX2 stays compressed in GPU memory — same texture uses ~2-3MB VRAM
- On mobile Safari (iOS), ASTC is natively supported → zero transcoding overhead
- This is THE reason to use KTX2 over WebP/PNG for 3D anatomy models

### Pipeline for SOMA
1. **Build time**: Use `gltf-transform` CLI to convert textures:
   ```bash
   npx gltf-transform copy input.glb output.glb
   npx @gltf-transform/cli draco --compression level 7 output.glb output-draco.glb
   ```
2. **Texture conversion**: 
   ```bash
   npx @gltf-transform/cli ktxfix output-draco.glb
   # Or use basisu tool directly for manual control
   ```
3. **Runtime**: Three.js KTX2Loader with DRACOLoader
   ```js
   import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';
   const ktx2Loader = new KTX2Loader();
   ktx2Loader.setTranscoderPath('/basis/');
   ktx2Loader.detectSupport(renderer);
   ```

### Mobile Safari Specifics
- Safari supports ASTC natively via WebGL2 → KTX2 transcodes to ASTC automatically
- No WebGL2? Falls back to ETC1 (wide support)
- WebGPU (future): Native ASTC/BC7 support, zero transcoding needed
- **Performance**: Transcoding adds ~50-200ms per texture on first load, then cached

### Combined with Draco (SOMA LOD Pipeline)
From previous research cycle:
- Draco compresses geometry 90%+
- KTX2 compresses textures 6-8x in VRAM
- Combined: A 50MB anatomy GLB → ~3-5MB download, ~8-12MB VRAM (vs 200MB+ uncompressed)
- Perfect for SOMA's 3 LOD levels: high (full), medium (Draco+KTX2), low (Draco aggressive+ETC1S)

### gltf-transform is the One Tool
- Replaces need for separate basisu CLI
- Handles Draco + KTX2 + meshopt in single pipeline
- `npx @gltf-transform/cli validate model.glb` for sanity checks
- Shopify's gltf-compressor for visual comparison

### Meshopt as Draco Alternative (Tip #29 from Utsubo)
- Meshopt compression: better decompression speed, slightly larger files
- Consider for SOMA if Draco decode time is a bottleneck on older iOS devices
- Can use BOTH: Meshopt for geometry + KTX2 for textures

## Action Items for SOMA
1. Add KTX2Loader to AssetLoader.ts alongside DRACOLoader
2. Create texture conversion pipeline script (gltf-transform)
3. Define LOD texture strategies: LOD0=UASTC, LOD1=ETC1S, LOD2=ETC1S low-res
4. Benchmark texture memory on iOS Safari before/after KTX2
5. Update LODManager.ts design to include texture LOD

## Sources
- Utsubo: 100 Three.js Tips (2026) — Tips #22-29
- Kyady: BASIS vs KTX2 Web 3D Texture Compression Guide
- Three.js discourse: WebGPURenderer & KTX2/Basis


## Sources

- https://www.utsubo.com/blog/threejs-best-practices-100-tips
- https://mail.kyady.com/en/blog/basis-vs-ktx2-texture-compression-web-3d
- https://discourse.threejs.org/t/webgpurenderer-compressed-texture-ktx2-basis/69362
- https://threejs.org/examples/jsm/libs/basis/
