# WebGPU 3D Texture Compression for Medical Imaging (Chrome 139)

*Researched: 2026-04-06 20:40 CDT*

# WebGPU 3D Texture Compression for Medical Imaging (Chrome 139)

**Date:** 2025-07-30
**Source:** Chrome for Developers Blog

## Key Finding

Chrome 139 adds two critical WebGPU features for volumetric/medical rendering:

1. **`texture-compression-bc-sliced-3d`** — 3D textures with Block Compression (BC)
2. **`texture-compression-astc-sliced-3d`** — 3D textures with ASTC compression

## Relevance to SOMA

- **Directly applicable** to 3D anatomy rendering with volumetric data (CT/MRI textures)
- ASTC compression reduces memory footprint and bandwidth for 3D texture data
- Significant performance gains on mobile GPUs (iOS/Android) where bandwidth is limited
- Can compress DICOM-derived volumetric textures before upload to GPU

## Technical Details

```javascript
const adapter = await navigator.gpu.requestAdapter();
const requiredFeatures = [];
if (adapter?.features.has("texture-compression-bc-sliced-3d")) {
  requiredFeatures.push("texture-compression-bc", "texture-compression-bc-sliced-3d");
}
if (adapter?.features.has("texture-compression-astc-sliced-3d")) {
  requiredFeatures.push("texture-compression-astc", "texture-compression-astc-sliced-3d");
}
const device = await adapter.requestDevice({ requiredFeatures });
```

## Integration Path for SOMA

1. **DICOM → ASTC 3D texture pipeline**: Convert DICOM slices to compressed 3D textures
2. **Memory savings**: ASTC offers 4:1 to 8:1 compression ratios with minimal quality loss
3. **Mobile optimization**: Critical for iOS WebKit WebGPU where memory budgets are tight (~2GB)
4. **Cross-section rendering**: Use compressed 3D textures for real-time slice visualization

## Browser Support
- Chrome 139+ (stable July 2025)
- Safari/WebKit: WebGPU support growing, ASTC widely supported on Apple Silicon
- Firefox: WebGPU in development

## Priority
HIGH — This is a direct performance optimization for SOMA's 3D rendering pipeline.


## Sources

- https://developer.chrome.com/blog/new-in-webgpu-139
- https://productpower.substack.com/p/webgpu-your-browser-just-got-superpowers
- https://wishtreetech.com/blogs/digital-product-engineering/unlocking-the-power-of-webgl-and-webgpu-the-zero-install-enterprise/
