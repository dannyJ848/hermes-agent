# webgpu-3d-texture-compression-medical-imaging

*Researched: 2026-04-06 19:03 CDT*

# WebGPU 3D Texture Compression for Medical Volume Rendering

**Date:** 2026-04-06
**Source:** Chrome 139 WebGPU update (July 30, 2025)

## Key Finding

Chrome 139 introduces two critical WebGPU features for 3D medical volume rendering:

### `texture-compression-bc-sliced-3d`
Block Compression (BC) format support for 3D textures. Reduces VRAM usage for volumetric data.

### `texture-compression-astc-sliced-3d`
Adaptive Scalable Texture Compression (ASTC) format support for 3D textures. Particularly useful for mobile GPUs (Apple Silicon, ARM Mali).

## Impact on SOMA

1. **Memory reduction:** Compressed 3D textures dramatically reduce VRAM for CT/MRI volumetric data — critical on mobile devices with 4-6GB shared memory.

2. **Official brain scan demo:** Chrome ships a "Volume Rendering - Texture 3D" WebGPU sample showing 3D brain scans with ASTC compression. This is a reference implementation SOMA can study.

3. **Mobile viability:** ASTC is the standard mobile GPU compression format. iOS devices (A-series/M-series) have hardware ASTC decoders, making this the ideal format for SOMA's mobile rendering pipeline.

## Code Pattern

```javascript
const adapter = await navigator.gpu.requestAdapter();
const requiredFeatures = [];

if (adapter?.features.has("texture-compression-bc-sliced-3d")) {
  requiredFeatures.push("texture-compression-bc", "texture-compression-bc-sliced-3d");
}
if (adapter?.features.has("texture-compression-astc-sliced-3d")) {
  requiredFeatures.push("texture-compression-astc", "texture-compression-astc-sliced-3d");
}

const device = await adapter?.requestDevice({ requiredFeatures });

// For mobile (SOMA iOS): prefer ASTC sliced-3d
// For desktop: prefer BC sliced-3d
```

## Action Items for SOMA
- Study the Chrome Volume Rendering - Texture 3D sample as reference architecture
- Plan migration from raw 3D textures to ASTC-compressed volumetric data
- Feature-detect at runtime: mobile → ASTC, desktop → BC, fallback → uncompressed
- This enables CT/MRI volume rendering directly in WebGPU without server-side decompression


## Sources

- https://developer.chrome.com/blog/new-in-webgpu-139
