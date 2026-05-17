# ossium-webgpu-dicom-volume-renderer

*Researched: 2026-04-05 17:37 CDT*

# Ossium: WebGPU DICOM Volume Renderer (Browser-Based)

**Source:** https://github.com/fraserlove/ossium
**License:** MIT
**Stars:** 13 | **Language:** TypeScript + WebGPU shaders
**Relevance to SOMA:** HIGH — Direct reference implementation for browser-based medical volume rendering

## Key Features
- **DICOM-to-3D volume rendering** entirely in the browser via WebGPU
- Two rendering techniques implemented:
  1. **Multi-Planar Reformatting (MPR)** using Maximum Intensity Projection
  2. **Shaded Volume Rendering (SVR)** using Blinn-Phong lighting
- Built with TypeScript + Webpack
- Includes example human brain volume in assets/
- WebGPU-enabled browser required

## Architecture Notes
- `shaders/` — WebGPU shader code (WGSL)
- `src/` — TypeScript application logic
- Volume data loaded from DICOM files
- Uses 3D textures for volume representation

## SOMA Integration Potential
1. **Direct reference for DICOM loading pipeline** — Ossium already parses DICOM → 3D volume
2. **Shader techniques reusable** — Blinn-Phong volume shading could complement SOMA's SSS shaders
3. **MPR mode** — SOMA could add cross-sectional views using this approach
4. **WebGPU migration path** — When SOMA moves from Three.js/WebGL to WebGPU, this repo is the blueprint
5. **TypeScript native** — Fits SOMA's TS codebase perfectly

## Action Items
- Clone and study shader code for volume rendering techniques
- Evaluate MPR implementation for SOMA cross-section feature
- Consider WebGPU compute shader approach for real-time tissue classification
- Compare Blinn-Phong vs SOMA's subsurface scattering for anatomical accuracy

## Sources

- https://github.com/fraserlove/ossium
