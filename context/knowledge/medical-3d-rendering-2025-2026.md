# medical-3d-rendering-2025-2026

*Researched: 2026-04-04 21:56 CDT*

# Medical 3D Rendering: 2025-2026 State of the Art

## WebGPU Revolution
- **WebGPU** is replacing WebGL/Three.js for medical visualization, enabling compute shaders, hardware-accelerated 3D textures, and native ray-marching
- Three.js rewriting core for WebGPU via TSL (Three Shading Language)
- Babylon.js (v7/v8) most production-ready WebGPU engine with native volume rendering
- vtk.js actively porting to WebGPU backend

## Key Libraries
- **Three.js WebGPU (TSL)**: `examples/jsm/nodes/` + `examples/webgpu_volume_rendering.html`
- **Babylon.js**: Built-in volume rendering pipeline + PBR subsurface scattering
- **vtk.js**: Kitware's medical visualization, WebGPU port in progress
- **itk-wasm**: Gold standard for medical image processing in browser via WebAssembly
- **VolView (Kitware)**: Open-source DICOM viewer with direct-to-web volume rendering

## Subsurface Scattering for Tissue
- **Screen-Space SSS (SSSSS)** + Pre-Integrated Skin Shading is 2025 industry standard for mobile
- 6-tap Gaussian blur in screen space, separate RGB channels for scattering depth
- **Three-Path-Tracing** (gkjohnson/three-gpu-pathtracer): WebGPU path tracer with SSS via random walk/Christensen-Burley
- Babylon.js `PBRMaterial` has built-in `subSurface` config optimized for WebGPU

## LOD for Mobile
- **Virtual Geometry / Nanite-style**: WebGPU compute-based occlusion culling, micro-cluster streaming
- **Mesh Shaders**: Coming to WebGPU (Chrome origin trial 2025/2026)
- **meshoptimizer** (zeux/meshoptimizer): Essential for mobile web, EXT_meshopt_compression
- **WebTransport over HTTP/3**: Progressive mesh streaming based on camera distance

## DICOM-to-3D Pipeline
1. DICOM Parsing: `dicomParser` + `itk-wasm`
2. Isosurface Extraction: Flying Edges (replacing Marching Cubes) via WASM SIMD
3. Decimation: paraview-glance algorithms via WASM → glTF with EXT_meshopt_compression

## Open-Source Datasets
- **Open Anatomy Project** (Brigham and Women's): Visible Human derivatives in glTF
- **BodyParts3D** (U Tokyo): Massive CC-licensed anatomical 3D models
- **OpenNeuro**: MRI/FMRI with automated WebGPU rendering pipelines
- **Embodi3D**: STL anatomical models optimized via MeshOptimizer

## SOMA Stack Recommendation (2026)
- Rendering: Three.js (WebGPU TSL) or Babylon.js
- Shaders: Custom WGSL Compute for Volume Ray Marching + Pre-Integrated SSS
- Data Format: DICOM → itk-wasm (Flying Edges) → glTF 2.0 + EXT_meshopt_compression + KHR_texture_basisu
- Streaming: WebTransport for chunked LOD delivery

## Sources

- https://github.com/BabylonJS/Babylon.js
- https://github.com/mrdoob/three.js
- https://github.com/Kitware/vtk-js
- https://github.com/InsightSoftwareConsortium/itk-wasm
- https://github.com/KitwareMedical/VolView
- https://github.com/zeux/meshoptimizer
