# ohif-viewer-webgl-medical-imaging

*Researched: 2026-04-19 19:39 CDT*

# OHIF Viewer: Clinical-Grade Medical Imaging in WebGL

**Source:** https://www.webgpu.com/showcase/ohif-viewer-medical-imaging-webgl-browser/
**GitHub:** https://github.com/OHIF/Viewers
**Org:** Open Health Imaging Foundation (Mass General Hospital program)
**Demo:** https://viewer.ohif.org
**Rendering Engine:** Cornerstone3D (https://github.com/cornerstonejs/cornerstone3D)

## Architecture
- Zero-footprint browser-based DICOM viewer
- Single shared WebGL context via Cornerstone3D offscreen rendering
- WebAssembly for JPEG 2000 and JPEG-LS decompression via web workers
- SVG overlay annotations (resolution-independent)
- React-based with mode/extension architecture for swappable clinical workflows
- Kitware's VTK.js for 3D visualization
- Progressive loading: metadata first, image frames on demand

## Key Techniques for SOMA
- **Single shared WebGL context** — avoids browser context limits in multi-viewport layouts
- **Offscreen rendering + compositing** — drives multiple viewports efficiently
- **WASM decompression** — parallel JPEG2000/JPEG-LS via web workers
- **Extension architecture** — modular clinical workflows without touching core rendering
- **Progressive streaming** — fetches metadata first, image frames on demand

## SOMA Integration Potential
- Single-context approach could solve SOMA's multi-panel anatomy view rendering
- Extension architecture pattern for swappable anatomy modules (muscular, skeletal, etc.)
- Cornerstone3D's streaming could inform SOMA's model loading strategy
- SVG annotation overlay pattern for medical labels and cross-sections

## Sources

- https://www.webgpu.com/showcase/ohif-viewer-medical-imaging-webgl-browser/
- https://github.com/OHIF/Viewers
- https://github.com/cornerstonejs/cornerstone3D
