# webgpu-volume-rendering-3d-textures-2025

*Researched: 2026-04-06 15:58 CDT*

# WebGPU Volume Rendering & 3D Textures (Chrome 139, July 2025)

## Key Finding
Chrome 139 introduced native 3D texture support with BC (Block Compression) and ASTC (Adaptive Scalable Texture Compression) sliced-3D formats in WebGPU. This is directly applicable to medical imaging volume rendering in the browser.

## Technical Details
- **Feature flags:** `texture-compression-bc-sliced-3d` and `texture-compression-astc-sliced-3d`
- **Benefit:** Significant reductions in memory footprint and bandwidth for volumetric texture data without substantial visual quality loss
- **Use case:** Scientific visualization, medical imaging, advanced rendering
- **Sample:** Chrome provides a "Volume Rendering - Texture 3D" WebGPU sample rendering 3D brain scans with ASTC compression

## Feature Detection Pattern
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

## SOMA Relevance
- SOMA's 3D anatomy viewer could use WebGPU 3D textures for volumetric medical data (CT/MRI scans)
- Compressed 3D textures reduce memory — critical for mobile Safari/WKWebView
- The official Chrome brain scan sample is a direct reference implementation
- Feature available from Chrome 139+ (July 2025)

## Related Work
- MDPI paper on WebGPU-based volume rendering framework for ocean scalar data (2025) — couldn't access (403)
- WebGPU client-side AI for dermatological diagnostics with local differential privacy (Patel, Feb 2026)
- WebGPU-based MRI reverse engineering pipeline for digital brain twins (LinkedIn, 2025)


## Sources

- https://developer.chrome.com/blog/new-in-webgpu-139
- https://www.mdpi.com/2076-3417/15/5/2782
- https://www.researchgate.net/publication/401110730_WebGPU_Accelerated_Client-Side_AI_for_Privacy_Preserving_Dermatological_Diagnostics
