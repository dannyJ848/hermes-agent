# ossium-webgpu-medical-volume-rendering

*Researched: 2026-04-11 12:52 CDT*

# Ossium — WebGPU Volume Rendering for Medical Imaging

**Source:** github.com/fraserlove/ossium
**License:** MIT
**Stars:** 13 | **Forks:** 5 | **Commits:** 143

## Key Features
- Volume rendering application displaying 3D volumes from DICOM files in the browser
- Built entirely with WebGPU (no WebGL fallback)
- Two rendering techniques:
  1. **Multi-Planar Reformatting (MPR)** using Maximum Intensity Projection
  2. **Shaded Volume Rendering (SVR)** using Blinn-Phong lighting
- TypeScript + Webpack build system
- Includes example brain DICOM dataset

## Relevance to SOMA
- **Directly applicable** for volume rendering of CT/MRI data in SOMA's WebGPU pipeline
- MPR technique can complement SOMA's mesh-based anatomy rendering
- SVR with Blinn-Phong could be a lighter-weight alternative to full subsurface scattering
- MIT license allows direct integration
- Shader code in `shaders/` directory likely reusable

## Integration Notes
- Uses WebGPU natively — aligns with SOMA's WebGPU roadmap
- DICOM loading pipeline could replace/supplement current asset pipeline
- Brain volume dataset included for testing
- Webpack-based — may need adaptation for Vite build system

## Sources

- https://github.com/fraserlove/ossium
