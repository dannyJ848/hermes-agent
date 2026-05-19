# webgpu-medical-volume-rendering-tools

*Researched: 2026-04-06 14:21 CDT*

# WebGPU Medical Volume Rendering Tools (2025-2026)

## Key Projects Discovered

### 1. Ossium (fraserlove/ossium)
- **URL:** https://github.com/fraserlove/ossium
- **Stack:** TypeScript + WebGPU + Webpack
- **Techniques:** Multi-Planar Reformatting (MPR) with Maximum Intensity Projection, Shaded Volume Rendering (SVR) with Blinn-Phong lighting
- **Input:** DICOM files → 3D volumes in browser
- **License:** MIT
- **Relevance to SOMA:** High — directly usable patterns for DICOM-to-3D pipeline. WebGPU shaders for volume rendering could be adapted for anatomy visualization.

### 2. Grenzwert
- **URL:** https://www.webgpu.com/showcase/grenzwert-volumetric-ct-rendering-webgpu/
- **Stack:** C++/WebAssembly + WebGPU
- **Technique:** Path-traced volumetric CT rendering (ground-truth quality)
- **Relevance:** Reference for photorealistic medical rendering in browser

### 3. Web MRI Volume Renderer (Armeet Jatyani)
- **URL:** https://armeet.ca/blog/2025/web-mri-volume-renderer-in-rust
- **Stack:** Rust → WASM + wgpu
- **Relevance:** Alternative approach using Rust/WASM for performance-critical rendering

### 4. OrthoRay
- **URL:** https://users.rust-lang.org/t/real-time-medical-imaging-with-rust-wgpu-is-this-an-underexplored-niche/138189
- **Stack:** Rust + Tauri + wgpu
- **Focus:** DICOM viewer with high rendering performance
- **Relevance:** Desktop approach, but wgpu patterns transfer to WebGPU

## SOMA Integration Opportunities
1. **Ossium's shader code** (shaders/ folder) could be adapted for SOMA's anatomy viewer — Blinn-Phong SVR for tissue surface rendering
2. **MIP technique** useful for displaying bone/dense tissue layers in cross-sections
3. **DICOM ingestion pipeline** pattern from Ossium relevant to SOMA's asset pipeline
4. **WebGPU compute shaders** for real-time volume classification (tissue type separation)

## Technical Notes
- WebGPU is now stable in Chrome 113+, Firefox Nightly, Safari preview
- Volume rendering in browser is viable at interactive framerates
- Path tracing (Grenzwert) achieves ground-truth quality but may be too slow for mobile
- MIP + SVR (Ossium) is the practical sweet spot for production medical visualization


## Sources

- https://github.com/fraserlove/ossium
- https://www.webgpu.com/showcase/grenzwert-volumetric-ct-rendering-webgpu/
- https://armeet.ca/blog/2025/web-mri-volume-renderer-in-rust
- https://users.rust-lang.org/t/real-time-medical-imaging-with-rust-wgpu-is-this-an-underexplored-niche/138189
