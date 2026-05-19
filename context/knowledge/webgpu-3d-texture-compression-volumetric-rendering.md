# webgpu-3d-texture-compression-volumetric-rendering

*Researched: 2026-04-05 20:16 CDT*

# WebGPU 3D Texture Compression for Volumetric Medical Rendering

**Date:** 2025-07-30 (Chrome 139 release)
**Source:** Chrome for Developers Blog

## Key Finding
Chrome 139 introduced native support for **3D textures using BC (Block Compression) and ASTC (Adaptive Scalable Texture Compression) compressed formats** via two new WebGPU features:
- `texture-compression-bc-sliced-3d`
- `texture-compression-astc-sliced-3d`

## Why This Matters for SOMA
1. **Memory reduction**: Compressed 3D textures dramatically reduce memory footprint for volumetric medical data (CT/MRI scans)
2. **Bandwidth savings**: Less data transferred to GPU = faster ray casting
3. **Mobile viability**: ASTC is the standard for mobile GPUs (Mali, Adreno) — critical for SOMA's iOS target
4. **No visual quality loss**: Compression is designed to be visually lossless for the intended use case

## Technical Implementation
```javascript
// Check adapter support
const adapter = await navigator.gpu.requestAdapter();
const requiredFeatures = [];

if (adapter?.features.has("texture-compression-bc-sliced-3d")) {
  requiredFeatures.push("texture-compression-bc", "texture-compression-bc-sliced-3d");
}
if (adapter?.features.has("texture-compression-astc-sliced-3d")) {
  requiredFeatures.push("texture-compression-astc", "texture-compression-astc-sliced-3d");
}

const device = await adapter?.requestDevice({ requiredFeatures });

// Create compressed 3D texture
if (device.features.has("texture-compression-astc-sliced-3d")) {
  // ASTC path (preferred for mobile/iOS)
} else if (device.features.has("texture-compression-bc-sliced-3d")) {
  // BC path (desktop GPUs)
}
```

## Chrome Sample
Google provides a reference implementation: **Volume Rendering - Texture 3D** WebGPU sample demonstrating 3D brain scan rendering with ASTC compressed textures.

## SOMA Integration Path
1. When targeting WebGPU (vs Three.js WebGL fallback), use these features for DICOM volume data
2. Pre-compress CT/MRI volumes to ASTC 3D textures during the asset pipeline
3. Feature-detect at runtime — fallback to uncompressed for older browsers
4. ASTC 3D is especially valuable for mobile (iOS Safari when WebGPU ships)

## Related
- MDPI paper: WebGPU-based volume rendering framework for interactive visualization of scalar data (ray casting approach)
- PMC paper: Multi-volume rendering using depth buffers for surgical planning
- HN: Real-time path tracing of medical CT volumes in browser via WebGPU + WASM (C++/Emscripten)


## Sources

- https://developer.chrome.com/blog/new-in-webgpu-139
- https://www.mdpi.com/2076-3417/15/5/2782
- https://pmc.ncbi.nlm.nih.gov/articles/PMC12575470/
