# grenzwert-webgpu-volumetric-ct-rendering

*Researched: 2026-04-11 17:40 CDT*

# Grenzwert: Path-Traced Volumetric CT Rendering in WebGPU

**Date:** January 28, 2026
**Author:** Mikhail Gorobets
**Live Demo:** https://grenzwert.net
**Source:** GitHub (open source)

## Key Technical Details

- **Core Engine:** Cross-platform C++ compiled to WebAssembly, with WebGPU for GPU compute
- **Rendering:** Ground-truth path tracing of volumetric medical CT data — NOT mesh-based
- **Progressive Streaming:** 3D mip pyramid — coarse level loads first, fine detail streams in progressively
- **Interactive Features:** Real-time transfer function editing (opacity/color mapping), 3D cropping, slicing
- **Performance:** Progressive refinement keeps interaction responsive even during heavy computation
- **Fidelity:** Comparable to medical imaging workstation quality, running in browser

## Relevance to SOMA

1. **Volume rendering pipeline:** Grenzwert's mip-pyramid streaming approach could be adapted for SOMA's anatomy visualization — instead of loading full-resolution volumes, stream coarse-to-fine
2. **WebGPU architecture:** C++/WASM + WebGPU pattern is more performant than pure JS/Three.js for volume rendering. SOMA could use this for CT/MRI visualization
3. **Transfer functions:** Real-time tissue layer peeling via opacity/color mapping is exactly what medical anatomy apps need
4. **Path tracing for medical data:** Physically-based light transport through volumes gives more realistic tissue appearance than surface rendering — relevant for SOMA's SSS shader work
5. **Progressive loading pattern:** Mip pyramid with progressive refinement is ideal for mobile — start showing something immediately, refine as bandwidth allows

## Architecture Lessons for SOMA
- Use WebGPU (not WebGL) for any volume rendering — significantly better compute capabilities
- Progressive/streaming approach is essential for mobile responsiveness
- Transfer function editing is the key interaction model for volumetric medical data
- Open source — can study shader structure and streaming pipeline directly

## Also Found
- **NVIDIA Clara + VolView integration** (Kitware): Browser-native medical imaging with AI models
- **WebGPU-based ocean volume rendering** (MDPI): Academic framework for interactive scalar field visualization
- **WebGPU client-side AI for dermatology** (2026): Privacy-preserving diagnostics running entirely in browser via WebGPU


## Sources

- https://www.webgpu.com/showcase/grenzwert-volumetric-ct-rendering-webgpu/
- https://grenzwert.net
- https://www.kitware.com/integrating-nvidia-clara-models-into-volview-a-technical-deep-dive/
