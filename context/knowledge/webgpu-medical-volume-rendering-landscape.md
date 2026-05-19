# webgpu-medical-volume-rendering-landscape

*Researched: 2026-04-05 23:31 CDT*

# WebGPU Medical Volume Rendering Landscape (April 2026)

## Key Projects

### Grenzwert — Path-Traced Volumetric CT in Browser
- **Author:** Mikhail Gorobets (Jan 2026)
- **Stack:** C++ compiled to WebAssembly + WebGPU compute shaders
- **Key Innovation:** No hardware RTX/ray tracing required — uses pure WebGPU compute shaders for Monte Carlo path tracing
- **Performance:** 3D mip pyramid streaming for responsive interaction during transfer function editing and volume cropping
- **Relevance to SOMA:** This architecture (C++/WASM + WebGPU compute) could replace Three.js ray marching for medical volume rendering with ground-truth quality. The mip pyramid approach is ideal for mobile LOD.

### VolView (Kitware) — NVIDIA Clara Integration
- Browser-native medical imaging platform
- Integrated Clara open-source AI models for segmentation
- Uses Cornerstone3D with shared WebGL context
- **Relevance:** SOMA could adopt a similar AI model integration pattern

### OHIF Viewer — Clinical-Grade WebGL DICOM Viewer
- Streams DICOM images directly to browser
- GPU-accelerated via Cornerstone3D
- Supports CT, MRI, PET fusion, tumor segmentation
- **Relevance:** DICOM streaming architecture reference for SOMA

### DECODE-3DViz — WebGL Volume Rendering Framework
- Cloud-based platform for noninvasive medical imaging
- WebGL-powered interactive volume rendering
- **Relevance:** Open-source reference for volume rendering pipeline

## Technical Insights for SOMA
1. **WebGPU compute shaders > WebGL ray marching** for volume rendering — no hardware RTX dependency
2. **Mip pyramid streaming** solves mobile performance: stream low-res during interaction, render full-res on idle
3. **C++/WASM compilation** gives near-native performance in browser — could accelerate SOMA's mesh processing
4. **Transfer function editing** in real-time is table-stakes for medical visualization
5. **Path tracing** (vs rasterization) produces ground-truth volumetric rendering — critical for diagnostic accuracy

## Action Items for SOMA
- Evaluate Grenzwert's mip pyramid approach for SOMA's anatomy LOD system
- Consider C++/WASM module for compute-heavy operations (mesh decimation, volume rendering)
- Monitor WebGPU adoption on iOS Safari (currently behind feature flag)


## Sources

- https://www.webgpu.com/tag/medical-visualization/
- https://www.reddit.com/r/GraphicsProgramming/comments/1s9xjtt/webgpu_path_tracer_in_c_followup/
- https://www.kitware.com/integrating-nvidia-clara-models-into-volview-a-technical-deep-dive/
