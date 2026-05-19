# webgpu-3d-texture-volume-rendering-chrome139

*Researched: 2026-04-06 16:07 CDT*

# WebGPU 3D Texture Volume Rendering (Chrome 139, July 2025)

## Key Discovery: 3D Compressed Textures in WebGPU

Chrome 139 (July 2025) added **3D texture support for BC and ASTC compressed formats** via two new WebGPU features:
- `texture-compression-bc-sliced-3d`
- `texture-compression-astc-sliced-3d`

These enable volumetric texture data with efficient compression — **significant reductions in memory footprint and bandwidth** without substantial visual quality loss.

## Relevance to SOMA

SOMA's 3D anatomy viewer currently uses Three.js mesh-based rendering. This WebGPU feature opens the door to:
1. **Volume rendering of CT/MRI data** — Direct visualization of medical DICOM volumes in the browser
2. **Compressed 3D textures** — ASTC compression for volumetric medical data reduces memory by 4-8x
3. **Brain scan visualization** — Chrome's own sample demonstrates 3D brain scan rendering with ASTC

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
```

## Chrome Sample
Google provides a working sample: "Volume Rendering - Texture 3D" WebGPU sample with 3D brain scan visualization using ASTC compressed format.

## Next Steps for SOMA
1. Evaluate WebGPU browser support (Chrome 139+, Edge, Safari TP)
2. Prototype volume rendering pipeline alongside existing mesh renderer
3. Integrate with DICOM-to-volume pipeline from soma-asset-pipeline skill
4. Consider fallback to Three.js raymarching for non-WebGPU browsers


## Sources

- https://developer.chrome.com/blog/new-in-webgpu-139
- https://www.mdpi.com/2076-3417/15/5/2782
