# ossium-webgpu-dicom-volume-rendering

*Researched: 2026-04-06 14:49 CDT*

# Ossium: WebGPU DICOM Volume Renderer in Browser

**Repo:** https://github.com/fraserlove/ossium (13 stars, MIT license, 143 commits, TypeScript)

## Overview
A volume rendering application that displays 3D volumes created from DICOM files in the browser using WebGPU. Two rendering techniques:
1. **Multi-Planar Reformatting (MPR)** using Maximum Intensity Projection (MIP)
2. **Shaded Volume Rendering (SVR)** using Blinn-Phong lighting

## Tech Stack
- TypeScript
- WebGPU (requires WebGPU-enabled browser)
- Webpack build system
- Built-in sample: human brain volume in assets/

## SOMA Relevance
- **Directly applicable**: This is exactly the type of rendering SOMA needs for medical imaging
- WebGPU compute shaders handle volume rendering - could replace WebGL-based approaches
- MPR is standard for CT/MRI viewing (axial/sagittal/coronal reconstructions)
- SVR with Blinn-Phong is a starting point for anatomical visualization (SOMA uses SSS shaders for realistic tissue)
- TypeScript codebase = directly portable to SOMA's React Native + Three.js stack
- DICOM parsing pipeline can be studied and adapted

## Key Insight
WebGPU volume rendering in browser is now feasible. The ossium repo demonstrates real-time DICOM volume rendering with lighting. SOMA should evaluate WebGPU adoption for:
- Cross-sectional views (MPR) of anatomical models
- Real-time volumetric rendering of CT/MRI data
- Compute shader-based tissue classification and coloring

## Also Found
- MDPI paper (Yu 2025): "WebGPU-Based Volume Rendering Framework" for ocean scalar data - techniques transferable to medical volumes
- Reddit r/Radiology discussion on WebGPU volume rendering for CT
- GPU infrastructure guide for medical imaging AI (arccompute.io)


## Sources

- https://github.com/fraserlove/ossium
- https://www.mdpi.com/2076-3417/15/5/2782
