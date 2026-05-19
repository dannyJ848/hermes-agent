# webgpu-3d-texture-compression-medical-volume-rendering

*Researched: 2026-04-06 18:46 CDT*

# WebGPU 3D Texture Compression for Medical Volume Rendering

**Date:** 2026-04-07 (researched)
**Source:** Chrome 139 WebGPU Update (July 2025)

## Key Finding

Chrome 139 introduced two critical WebGPU features for medical imaging:

1. **`texture-compression-bc-sliced-3d`** — Block Compression (BC) for 3D textures
2. **`texture-compression-astc-sliced-3d`** — ASTC compression for 3D textures

These enable volumetric texture data (CT/MRI scans) to be stored with significant memory/bandwidth reduction.

## Technical Details

- BC formats: Widely supported on desktop GPUs (NVIDIA/AMD)
- ASTC formats: Mobile-friendly (ARM GPUs, Apple Silicon)
- Both support 3D (sliced) variants — crucial for volume rendering
- Feature detection via `adapter.features.has("texture-compression-astc-sliced-3d")`

## Code Pattern (Feature Detection)

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
```

## SOMA Application

- **Brain scans**: Chrome team provides an official "Volume Rendering - Texture 3D" WebGPU sample with 3D brain scans using ASTC compression
- **Memory reduction**: Compressed 3D textures dramatically reduce memory footprint — critical for mobile (iOS Safari)
- **Mobile path**: ASTC sliced-3d is the mobile-friendly route for SOMA's iOS app
- **Desktop path**: BC sliced-3d for desktop browsers

## Also Noted

- MDPI paper: "WebGPU-Based Volume Rendering Framework for Interactive Visualization" (ocean scalar data, but techniques transfer to medical)
- WebGPU client-side AI for dermatological diagnostics (privacy-preserving, uses WebGPU compute)

## Action Items for SOMA

1. Test `texture-compression-astc-sliced-3d` feature availability on iOS Safari (WKWebView)
2. Evaluate WebGPU as a migration path from Three.js WebGL for volume rendering
3. Study the Chrome WebGPU volume rendering sample code for implementation patterns


## Sources

- https://developer.chrome.com/blog/new-in-webgpu-139
- https://www.mdpi.com/2076-3417/15/5/2782
