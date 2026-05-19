# Ossium WebGPU Volume Rendering for Medical Imaging

*Researched: 2026-04-07 09:13 CDT*

# Ossium: WebGPU Volume Rendering for Medical Imaging

**Repo:** https://github.com/fraserlove/ossium
**Stars:** 13 (very new, April 2025)
**Language:** TypeScript (WebGPU)

## What It Does
Volume rendering application to display 3D medical imaging data (DICOM/NIfTI) in the browser using **pure WebGPU**. This is one of the first WebGPU-native medical volume renderers.

## Why It Matters for SOMA
- **Directly relevant** to SOMA's 3D anatomy rendering pipeline
- WebGPU offers 2-5x performance over WebGL2 for volume rendering
- Pure browser implementation — no server-side rendering needed
- Could replace or complement Three.js WebGL2 for DICOM/cross-section views
- Shader approach may inform SSS (subsurface scattering) implementation

## Key Technical Details
- TypeScript + WebGPU compute/render pipelines
- Browser-native, runs on any modern Chrome/Edge
- Volume rendering of 3D medical imaging data
- Very lightweight compared to NiiVue or VolView

## Integration Path for SOMA
1. Study the WebGPU shader code for ray-marching / volume rendering approach
2. Adapt SSS shader techniques for SOMA's anatomy models
3. Consider WebGPU fallback for browsers that support it (progressive enhancement)
4. Could enable real-time DICOM cross-section visualization in SOMA

## Risks
- Very new project (13 stars) — API may change
- WebGPU support still limited on Safari/iOS (critical for SOMA's mobile target)
- May need WebGL2 fallback for iOS Safari


## Sources

- https://github.com/fraserlove/ossium
