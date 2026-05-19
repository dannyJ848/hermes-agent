# webgpu-volume-rendering-2025

*Researched: 2026-04-06 13:46 CDT*

# WebGPU Volume Rendering Framework (2025)

## Source
MDPI Applied Sciences 15(5), 2782 (2025) — "The Implementation of a WebGPU-Based Volume Rendering Framework for Interactive Visualization of Ocean Scalar Data"

## Key Findings

### Performance
- WebGPU delivers **3-5x performance improvement** over WebGL for volume rendering in medical and scientific applications (confirmed by VolumeShader.dev benchmark).
- Ray casting algorithm optimized with WebGPU compute shaders enables interactive frame rates for large volumetric datasets.

### Architecture
- Uses WebGPU compute shaders for ray-casting volume rendering
- Handles large-scale scalar data (ocean, medical CT/MRI)
- Interactive — real-time slicing, contrast adjustment, 3D reconstruction
- Universal browser support since late 2025

### SOMA Relevance
- **Directly applicable** to SOMA's 3D anatomy viewer
- Ray casting with compute shaders could replace Three.js mesh-based approach for volumetric medical data (CT/MRI scans)
- 3-5x performance gain critical for mobile where thermal throttling is the bottleneck
- Compute shader approach enables:
  - Real-time transfer function editing (opacity/color mapping)
  - Interactive cross-sections without geometry regeneration
  - Multi-volume compositing (overlaying anatomy layers)

### Migration Path
- Three.js already supports WebGPU renderer (experimental → stable)
- Can start with WebGPURenderer adapter, then add compute shader passes
- Fallback to WebGL2 for Safari < 18 (now rare)

### Related Work
- LinkedIn: Interactive 3D Brain Visualization using WebGPU volume rendering (Oserebameh Beckley)
- Khronos "3D on the Web" GDC 2025: Large Scale Scientific Visualization with WebGL/WebGPU
- VolumeShader.dev: WebGL vs WebGPU benchmark showing 3-5x gains in scientific viz

## Action Items for SOMA
1. Prototype WebGPU compute shader for volumetric rendering of DICOM data
2. Benchmark vs current Three.js mesh approach on mobile
3. Evaluate Three.js WebGPU renderer migration path
4. Consider compute shader for subsurface scattering (SSS) — currently using fragment shader hack


## Sources

- https://www.mdpi.com/2076-3417/15/5/2782
- https://www.volumeshader.dev/ru/blog/webgl-vs-webgpu
- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
