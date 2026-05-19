# webgpu-3d-texture-compression-volume-rendering

*Researched: 2026-04-06 18:37 CDT*

# WebGPU 3D Texture Compression for Volume Rendering (Chrome 139)

**Date:** 2026-04-06
**Source:** Chrome for Developers Blog — What's New in WebGPU (Chrome 139)

## Key Finding

Chrome 139 (July 2025) introduces two critical WebGPU features for medical volume rendering:

1. **`texture-compression-bc-sliced-3d`** — Block Compression (BC) for 3D textures
2. **`texture-compression-astc-sliced-3d`** — ASTC for 3D textures

## SOMA Relevance

These features enable **compressed 3D textures** directly in WebGPU — critical for:
- CT/MRI volume rendering in the browser
- Significant memory reduction (BC/ASTC compression ratios ~4:1 to 8:1)
- Reduced bandwidth for volumetric medical data
- Enables real-time 3D brain scan visualization in-browser

## Implementation Pattern

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

// Create compressed 3D texture for CT/MRI data
if (device.features.has("texture-compression-astc-sliced-3d")) {
  // ASTC 3D texture — best for mobile (ARM GPUs)
} else if (device.features.has("texture-compression-bc-sliced-3d")) {
  // BC 3D texture — best for desktop (NVIDIA/AMD)
} else {
  // Fallback: uncompressed 3D texture
}
```

## Chrome Official Sample

Chrome provides a **Volume Rendering - Texture 3D** WebGPU sample that renders 3D brain scans with ASTC compressed format. This is a direct reference implementation for SOMA's volume rendering pipeline.

## Also Notable: MDPI Paper

A 2025 paper "The Implementation of a WebGPU-Based Volume Rendering Framework for Interactive Visualization of Ocean Scalar Data" (Applied Sciences, 15(5), 2782) describes ray casting-based volume rendering in WebGPU. Techniques transferable to medical imaging.

## Action Items for SOMA

1. Check WebGPU support in iOS Safari/WKWebView for `texture-compression-astc-sliced-3d` (ASTC is native on Apple GPUs)
2. Build a proof-of-concept volume renderer using the Chrome sample as reference
3. Evaluate ASTC 3D compression for CT abdomen datasets (512³ voxels)
4. Consider progressive loading: compressed mip levels streamed on demand


## Sources

- https://developer.chrome.com/blog/new-in-webgpu-139
- https://www.mdpi.com/2076-3417/15/5/2782
