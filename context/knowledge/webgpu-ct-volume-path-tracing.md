# webgpu-ct-volume-path-tracing

*Researched: 2026-04-06 19:10 CDT*

# WebGPU Real-Time Path Tracing of Medical CT Volumes

**Source:** Hacker News (Show HN) - MickGorobets, ~Feb 2026
**URL:** https://news.ycombinator.com/item?id=46933474
**Relevance:** Directly applicable to SOMA's 3D anatomy rendering pipeline

## Technical Architecture

A GPU path tracer for volumetric medical data running entirely in Chrome via **WebGPU + WebAssembly (C++/Emscripten)**.

### Rendering Pipeline
- **Volume rendering:** Delta tracking (Woodcock null-collision algorithm) for unbiased volume rendering
- **Surface shading:** Cook-Torrance GGX BRDF + Henyey-Greenstein phase function for volume scattering
- **Acceleration:** MacroGrid (DDA empty-space skipping + GPU tile culling)
- **Convergence:** Progressive frame accumulation — noisy initially, converges to ground truth
- **HDR pipeline:** Bloom, auto-exposure, PBR Neutral / ACES tone mapping
- **Streaming:** Async mip-level streaming with gzip decompression

### Infrastructure
- Built on **Diligent Engine** (cross-platform graphics API with WebGPU backend)
- Requires Chrome with WebGPU enabled
- Works on both discrete and integrated GPUs

## SOMA Integration Opportunities

1. **Volume rendering of CT/MRI data:** The delta tracking + Henyey-Greenstein approach could render DICOM volumes directly in the browser
2. **MacroGrid acceleration:** DDA empty-space skipping is relevant for SOMA's LOD pipeline — skip empty anatomy regions
3. **Progressive accumulation:** Matches SOMA's need for mobile-friendly rendering (start noisy, refine over frames)
4. **Diligent Engine:** Worth evaluating as alternative to raw Three.js for WebGPU compute shaders
5. **Async mip-level streaming:** Pattern for streaming high-res anatomy meshes on mobile

## Key Takeaway
WebGPU is now production-ready for medical volume rendering in browsers. The delta tracking approach is particularly interesting for SOMA because it handles heterogeneous tissue densities naturally — bone, soft tissue, and skin all scatter light differently, and this algorithm captures that without precomputation.


## Sources

- https://news.ycombinator.com/item?id=46933474
