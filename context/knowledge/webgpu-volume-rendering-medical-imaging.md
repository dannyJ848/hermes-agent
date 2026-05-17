# webgpu-volume-rendering-medical-imaging

*Researched: 2026-04-05 19:52 CDT*

# WebGPU Volume Rendering for Medical Imaging

## Key Findings (April 2026)

### 1. Ossium (github.com/fraserlove/ossium)
- WebGPU-based volume rendering app for DICOM data in the browser
- Implements two techniques: Multi-Planar Reformatting (MPR) with MIP and Shaded Volume Rendering (SVR) with Blinn-Phong shading
- 13 stars, early project but clean architecture
- Relevance to SOMA: Direct reference implementation for WebGPU-based anatomy rendering from DICOM volumes

### 2. WebGPU Volume Rendering Framework (MDPI Applied Sciences 2025)
- Paper: "The Implementation of a WebGPU-Based Volume Rendering Framework for Interactive Visualization of Ocean Scalar Data"
- Demonstrates WebGPU's compute shaders for real-time volume rendering
- Transfer functions and ray marching in WebGPU compute pipeline
- Techniques transferable to medical volume data (CT/MRI)

### 3. GPU-Driven Volume Rendering in Medical Imaging (IEEE 2025)
- Paper on GPU-optimized web-based volume rendering for peripheral artery disease (PAD)
- Highlights clinical applicability of browser-based volume rendering
- Demonstrates diagnostic quality rendering in web environment

### 4. BioLens (Babylon.js Forum)
- Volume ray marching approach for medical scan visualization
- Uses Babylon.js + WebGPU for volumetric rendering
- Each pixel casts ray into 3D texture — produces high-quality results
- Alternative to Three.js approach; could inform SOMA's rendering pipeline

### Techniques Summary
- **Ray marching**: Cast rays through 3D texture per-pixel, sample density, apply transfer functions
- **MPR (Multi-Planar Reformatting)**: Slice views with MIP (Maximum Intensity Projection)
- **SVR (Shaded Volume Rendering)**: Blinn-Phong shading applied to volume gradients
- **Compute shaders**: WebGPU compute pipeline enables parallel volume sampling

### SOMA Integration Notes
- WebGPU compute shaders could replace Three.js fragment-based volume rendering
- Transfer functions enable tissue-type differentiation (bone vs soft tissue)
- MPR views are standard in radiology — essential for SOMA's clinical utility
- Ossium is clean reference code for DICOM→WebGPU pipeline

## Sources

- https://github.com/fraserlove/ossium
- https://www.mdpi.com/2076-3417/15/5/2782
- https://ieeexplore.ieee.org/document/10820457/
- https://forum.babylonjs.com/t/volumetric-visualization-app-for-medical-scans-biolens/61537
