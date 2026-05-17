# webgpu-volume-rendering-chrome139

*Researched: 2026-04-06 14:43 CDT*

# WebGPU Volume Rendering — Chrome 139 (July 2025)

## Key Development
Chrome 139 introduced native 3D texture compression support for WebGPU, enabling efficient volume rendering of medical imaging data (CT, MRI brain scans) directly in the browser.

## Technical Details
- **New features:** `texture-compression-bc-sliced-3d` and `texture-compression-astc-sliced-3d`
- **Impact:** Significant reductions in memory footprint and bandwidth for volumetric textures
- **Formats:** BC (Block Compression) and ASTC (Adaptive Scalable Texture Compression) for 3D textures
- **Official sample:** "Volume Rendering - Texture 3D" WebGPU sample demonstrates 3D brain scan visualization with ASTC compression

## SOMA Relevance
- Directly applicable to SOMA's 3D anatomy viewer for rendering volumetric medical data
- ASTC 3D compression could reduce DICOM/CT volume memory by 4-8x
- The Chrome sample code provides a reference implementation for brain scan rendering
- Feature detection pattern: check adapter.features, request device with capabilities, fallback to uncompressed

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

## Additional Research
- FusionRender (ACM 2024): WebGPU rendering performance improved 29-122% over WebGL baselines
- WebGPU-based volume rendering framework for ocean scalar data (MDPI Applied Sciences 2025) — transferable to medical volumes
- Privacy-preserving dermatological diagnostics using WebGPU client-side AI (2026)


## Sources

- https://developer.chrome.com/blog/new-in-webgpu-139
- https://www.mdpi.com/2076-3417/15/5/2782
- https://dl.acm.org/doi/abs/10.1145/3589334.3645395
