# webgpu-compute-shader-medical-volume-rendering-2025

*Researched: 2026-04-05 12:37 CDT*

# WebGPU Compute Shaders for Medical Volume Rendering (2025 Survey)

## Key Paper: Multi-Volume Rendering via Depth Buffers for Surgical Planning (2025)
- **Authors:** Faludi et al., University of Basel (Biomedical Engineering + Neurosurgery)
- **Published:** Int J Comput Assist Radiol Surg, June 2025 (doi: 10.1007/s11548-025-03432-y)
- **License:** CC-BY 4.0 (open access)
- **Technique:** Ray marching implemented as **compute shaders**, where each thread processes a single ray. Depth buffer compositing enables multi-volume overlay (CT + MRI + angiography) for surgical planning in VR.
- **Clinical use:** Neurosurgery — spine and brain surgical planning at University Hospital Basel.

## BioLens (BabylonJS Forum, 2025)
- Open-source volumetric medical scan viewer built on BabylonJS
- Uploads volume data to GPU as **3D texture** for fast sampling
- Relevant to SOMA as a potential reference implementation for WebGPU-based anatomy viewing

## WebGPU Volume Rendering Framework (MDPI Applied Sciences, 2025)
- Paper: "WebGPU-Based Volume Rendering Framework for Interactive Visualization of Scalar Data"
- General-purpose WebGPU volume rendering — transfer functions, ray casting
- Applicable to ocean/scalar data but architecture is transferable to medical volumes

## Implications for SOMA
1. **Compute shaders > fragment shaders** for volume rendering — better work distribution, each thread = 1 ray
2. **3D texture upload** is the standard approach for GPU-side volume data (DICOM/NIfTI → 3D texture)
3. **Depth buffer compositing** enables overlaying multiple scan types — directly applicable to SOMA's cross-section and dissection modes
4. **Mobile feasibility:** WebGPU compute shaders are supported in Chrome 113+ and Safari 18+ (iOS 18), making this viable for SOMA's mobile target
5. **Architecture suggestion:** SOMA should use a compute-shader ray marcher for volumetric anatomy rendering, with 3D texture upload from compressed NIfTI/GLB sources

## Next Steps
- Evaluate BioLens source code for reusable patterns
- Prototype compute shader ray marcher in Three.js r170+ (WebGPU renderer)
- Benchmark mobile performance on iOS 18 Safari WebGPU

## Sources

- https://pmc.ncbi.nlm.nih.gov/articles/PMC12575470/
- https://forum.babylonjs.com/t/volumetric-visualization-app-for-medical-scans-biolens/61537
- https://www.mdpi.com/2076-3417/15/5/2782
