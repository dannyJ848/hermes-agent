# webgpu-compute-sss-medical-rendering

*Researched: 2026-04-06 06:47 CDT*

# WebGPU Compute Shaders for Real-Time SSS in Medical 3D

## SIGGRAPH 2025: Hybrid ReSTIR-Path Tracing + Diffusion for Real-Time SSS
- **Source**: SIGGRAPH 2025 "Advances in Real-Time Rendering" course
- **Key innovation**: Hybrid approach combining ReSTIR path tracing with diffusion approximation for real-time subsurface scattering
- **Relevance to SOMA**: Could replace screen-space SSS approximation with physically-accurate light transport
- **URL**: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf

## WebGPU Compute Shader Capabilities (2025)
- **SPH fluid simulation**: Smoothed Particle Hydrodynamics fully implementable in WebGPU compute shaders
- **Key features now available**: Storage Buffers, Compute Shaders, 3D Textures, Indirect Draw Calls, Atomics
- **Histopyramids**: GPU-side stream compaction enabling efficient particle culling
- **Marching cubes on GPU**: Direct mesh extraction from volumetric data — directly applicable to medical imaging
- **Performance**: 13 years of WebGL→WebGPU evolution shows compute shaders enable real-time complex simulations previously impossible in browsers
- **Source**: Hector Arellano (Hat), Codrops, Jan 2025
- **URL**: https://tympanus.net/codrops/2025/01/29/particles-progress-and-perseverance-a-journey-into-webgpu-fluids/

## Application to SOMA
1. **SSS via Compute**: Replace Three.js screen-space SSS with WebGPU compute-based diffusion approximation
2. **Volume Rendering**: 3D textures + marching cubes for direct DICOM/NIfTI volume rendering
3. **Particle-based Tissue**: SPH could simulate soft tissue deformation in real-time
4. **Architecture**: WebGPU pipeline alongside Three.js WebGL — use `renderer.getContext()` upgrade path or dual-context approach

## Next Steps for SOMA
- Evaluate WebGPU browser support on iOS Safari (critical for mobile deployment)
- Prototype compute shader for separable SSS (Gaussian profile fitting)
- Test 3D texture upload from glTF volumetric data


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://tympanus.net/codrops/2025/01/29/particles-progress-and-perseverance-a-journey-into-webgpu-fluids/
