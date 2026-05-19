# WebGPU 3D Texture Compressed Volume Rendering (Chrome 139)

*Researched: 2026-04-05 13:19 CDT*

# WebGPU 3D Texture Compressed Volume Rendering — Chrome 139

**Date:** 2025-07-30
**Source:** Chrome for Developers Blog

## Key Finding
Chrome 139 introduces native support for **3D textures with BC (Block Compression) and ASTC (Adaptive Scalable Texture Compression) compressed formats** in WebGPU.

### New Features
- `texture-compression-bc-sliced-3d` — BC compressed 3D textures
- `texture-compression-astc-sliced-3d` — ASTC compressed 3D textures

### Why This Matters for SOMA
1. **Memory reduction:** Compressed 3D textures significantly reduce GPU memory footprint for volumetric medical data (CT/MRI scans)
2. **Bandwidth savings:** Less data transfer = faster ray-casting through volume data
3. **Mobile viable:** ASTC is the mobile-standard compression format — critical for iOS Safari WebGPU adoption
4. **Brain scan demo:** Chrome ships a Volume Rendering - Texture 3D WebGPU sample rendering actual 3D brain scans

### Technical Details
- Check adapter features: `adapter.features.has("texture-compression-astc-sliced-3d")`
- Request device with features: `requestDevice({ requiredFeatures: ["texture-compression-astc", "texture-compression-astc-sliced-3d"] })`
- Fallback: uncompressed 3D textures if compression not supported

### Integration Path for SOMA
1. Use ASTC 3D compression for mobile (iOS) medical scan visualization
2. Use BC 3D compression for desktop browsers
3. Existing WebGPU volume rendering pipeline can be upgraded with compression wrappers
4. The Chrome sample code provides a reference implementation for brain scan rendering

### Also in Chrome 139
- New `core-features-and-limits` feature for upcoming WebGPU compatibility mode


## Sources

- https://developer.chrome.com/blog/new-in-webgpu-139
- https://github.com/fraserlove/ossium
