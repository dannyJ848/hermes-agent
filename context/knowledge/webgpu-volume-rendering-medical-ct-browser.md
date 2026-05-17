# webgpu-volume-rendering-medical-ct-browser

*Researched: 2026-04-05 12:25 CDT*

# WebGPU Volume Rendering for Medical CT — Browser-Based (2025)

## Chrome 139: Native 3D Texture Compression (July 2025)
- Chrome 139 adds `texture-compression-bc-sliced-3d` and `texture-compression-astc-sliced-3d` features
- Enables BC (Block Compression) and ASTC compressed 3D textures in WebGPU
- **SOMA Impact:** Massive memory savings for volumetric medical data. ASTC 3D compressed brain scans already demonstrated in Chrome's official sample.
- Feature detection: `adapter.features.has("texture-compression-astc-sliced-3d")`
- Official sample: "Volume Rendering - Texture 3D" WebGPU sample (Chrome website)

## Real-Time Path Tracing of Medical CT Volumes (Hacker News, ~Feb 2025)
- Author: MickGorobets, built on Diligent Engine (contributed to its WebGPU backend)
- Full GPU path tracer running in Chrome via WebGPU + WebAssembly (C++/Emscripten)
- **Key techniques:**
  - Delta tracking (Woodcock null-collision algorithm) for unbiased volume rendering
  - Cook-Torrance GGX BRDF + Henyey-Greenstein phase function
  - MacroGrid acceleration (DDA empty-space skipping + GPU tile culling)
  - Progressive frame accumulation (noisy → converges to ground truth)
  - HDR pipeline: bloom, auto-exposure, PBR Neutral / ACES tone mapping
  - Async mip-level streaming with gzip decompression
- Works on discrete and integrated GPUs, Chrome only
- Source: https://grenzwert.net (author's site)

## SOMA Integration Notes
1. **ASTC 3D compression** reduces memory footprint for anatomy volumes — critical for mobile/iOS
2. **Delta tracking** is the gold-standard for unbiased volume rendering — consider for DICOM viewer
3. **Progressive accumulation** pattern matches SOMA's need: fast preview → high-quality final render
4. **Async mip-level streaming** solves the problem of loading large volumes on constrained devices
5. **Diligent Engine** WebGPU backend is production-tested and open source — potential rendering backend for SOMA


## Sources

- https://developer.chrome.com/blog/new-in-webgpu-139
- https://news.ycombinator.com/item?id=46933474
- https://www.mdpi.com/2076-3417/15/5/2782
