# ossium-webgpu-volume-rendering

*Researched: 2026-04-06 14:58 CDT*

# Ossium: WebGPU Volume Rendering for Medical Imaging

**Source:** https://github.com/fraserlove/ossium (13 stars, MIT license, 143 commits, TypeScript)

## Overview
Ossium is a browser-based volume rendering application that displays 3D volumes created from DICOM files using WebGPU. This is directly relevant to SOMA's anatomy viewer — it demonstrates production WebGPU techniques for medical data.

## Key Rendering Techniques
1. **Multi-Planar Reformatting (MPR)** — Uses maximum intensity projection (MIP) to display orthogonal slices through volumetric data
2. **Shaded Volume Rendering (SVR)** — Uses Blinn-Phong lighting model for realistic 3D volume shading

## Architecture Notes
- Written in TypeScript with WebGPU API
- Built with Webpack
- Includes shader programs in `shaders/` directory
- DICOM parsing in `src/`
- Has sample brain volume in `assets/`

## Relevance to SOMA
- **Direct technique transfer:** The SVR with Blinn-Phong could enhance SOMA's anatomy rendering
- **DICOM pipeline:** Shows how to parse DICOM → volume → WebGPU rendering
- **MPR feature:** Multi-planar reformatting is a standard medical imaging feature SOMA should support
- **WebGPU shaders:** The shader code in `shaders/` could be studied for SOMA's WebGPU migration

## Related Paper
MDPI Applied Sciences 2025: "The Implementation of a WebGPU-Based Volume Rendering Framework" — uses ray casting with early ray termination and adaptive sampling. Applies to ocean scalar data but techniques are transferable to medical imaging.

## DECODE-3DViz
Another relevant project (Springer 2025): WebGL-based high-fidelity visualization for medical imaging using ray casting through volumetric data with shading/lighting.

## Sources

- https://github.com/fraserlove/ossium
- https://www.mdpi.com/2076-3417/15/5/2782
- https://link.springer.com/article/10.1007/s10278-025-01430-9
