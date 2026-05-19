# ossium-webgpu-volume-renderer-2026

*Researched: 2026-04-12 03:17 CDT*

# Ossium — WebGPU Volume Rendering for Medical Imaging

**Source:** github.com/fraserlove/ossium (143 commits, MIT license)

## Overview
Browser-based volume rendering app for DICOM data, built entirely with WebGPU.

## Features
- **Multi-Planar Reformatting (MPR)** using maximum intensity projection
- **Shaded Volume Rendering (SVR)** using Blinn-Phong lighting
- TypeScript + WebGPU + Webpack
- Loads DICOM files directly

## Relevance to SOMA
- Direct reference implementation for WebGPU-based 3D medical rendering
- Blinn-Phong SVR is a simpler alternative to full subsurface scattering
- WebGPU (not WebGL) = future-proof for iOS Safari when support lands
- TypeScript stack aligns with SOMA

## Technical Notes
- Uses WebGPU compute shaders for ray-casting
- Brain dataset included in assets/
- Built with webpack, runs as `yarn build && yarn dev`
- 5 forks, 13 stars — early but functional


## Sources

- https://github.com/fraserlove/ossium
