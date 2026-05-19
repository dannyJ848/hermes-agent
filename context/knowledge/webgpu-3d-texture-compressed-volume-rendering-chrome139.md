# webgpu-3d-texture-compressed-volume-rendering-chrome139

*Researched: 2026-04-05 13:49 CDT*

# WebGPU 3D Texture Compressed Volume Rendering (Chrome 139+)

**Date:** 2025-07-30 (Chrome 139 release)
**Source:** Chrome for Developers blog

## Key Features

### 3D Texture BC and ASTC Compressed Format Support
Two new WebGPU features for volumetric texture data:
- `texture-compression-bc-sliced-3d` — Block Compression for 3D textures
- `texture-compression-astc-sliced-3d` — ASTC compression for 3D textures

**Impact for SOMA:** These formats offer significant reductions in memory footprint and bandwidth for volumetric medical imaging data (CT/MRI scans) without substantial visual quality loss.

### Implementation Pattern
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

// Fallback chain: ASTC 3D → BC 3D → uncompressed 3D
if (device.features.has("texture-compression-astc-sliced-3d")) {
  // Create compressed 3D texture (best compression, mobile-friendly)
} else if (device.features.has("texture-compression-bc-sliced-3d")) {
  // Create BC compressed 3D texture (desktop-friendly)
} else {
  // Fallback: uncompressed 3D texture
}
```

### WebGPU Compatibility Mode (Origin Trial)
- Addresses 31% of Windows Chrome users without D3D 11.1+ and 15% of Android users without Vulkan 1.1
- `core-features-and-limits` feature distinguishes core vs compatibility mode
- Critical for SOMA's cross-platform mobile reach

### Official Volume Rendering Sample
Chrome 139 ships with an official **Volume Rendering - Texture 3D** WebGPU sample showing 3D brain scan rendering with ASTC compressed format.

## SOMA Integration Implications

1. **Memory optimization:** ASTC 3D compression can reduce CT/MRI volume memory by 4-8x vs uncompressed
2. **Mobile viability:** ASTC is the mobile compression standard — essential for SOMA's iOS/Android targets
3. **Progressive loading synergy:** Compressed 3D textures work with Cornerstone's progressive decimation pattern — load compressed low-res first, then higher mip levels
4. **WebGPU compute shader interpolation:** With compressed 3D textures, compute shaders can perform trilinear interpolation between mip levels for progressive refinement
5. **iOS Safari support:** Article confirms WebGPU is now supported in Apple's latest iOS Safari, validating SOMA's WebGPU-first approach

## Technical Notes
- `textureSampleLevel` available in WGSL for sampling specific mip levels from compute shaders
- Intel Mac has known issues with `textureSampleLevel` in compute shaders (gpuweb issue #4818) — need fallback
- Three.js TSL (Three.js Shading Language) provides cross-backend shader authoring (WebGPU + WebGL fallback)


## Sources

- https://developer.chrome.com/blog/new-in-webgpu-139
- https://blog.maximeheckel.com/posts/field-guide-to-tsl-and-webgpu/
- https://github.com/gpuweb/gpuweb/issues/4818
