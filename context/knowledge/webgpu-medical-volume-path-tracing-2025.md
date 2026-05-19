# webgpu-medical-volume-path-tracing-2025

*Researched: 2026-04-06 00:55 CDT*

# WebGPU Medical Volume Path Tracing (2025)

## Source: Hacker News Show HN (MickGorobets)

### Key Project
Real-time path tracer for volumetric medical CT data running entirely in Chrome via WebGPU + WebAssembly (C++/Emscripten).

### Technical Pipeline
- **Delta tracking** (Woodcock null-collision algorithm) for unbiased volume rendering
- **Cook-Torrance GGX BRDF** + **Henyey-Greenstein phase function** for scattering
- **MacroGrid acceleration** (DDA empty-space skipping + GPU tile culling)
- **Progressive frame accumulation** — noisy at first, converges to ground truth
- **HDR pipeline**: bloom, auto-exposure, PBR Neutral / ACES tone mapping
- **Async mip-level streaming** with gzip decompression
- Built on **Diligent Engine** (contributor to its WebGPU backend)

### SOMA Relevance
- Directly applicable pattern for SOMA's 3D anatomy viewer
- Delta tracking could replace our simpler SSS approximation for tissue rendering
- MacroGrid acceleration solves the empty-space problem in volumetric medical data
- Progressive accumulation is ideal for mobile — start noisy, refine over frames
- Diligent Engine's WebGPU backend is a potential alternative to raw Three.js for compute-heavy tasks

### SIGGRAPH 2025 SSS Advances Course
- Published at advances.realtimerendering.com/s2025/
- Hybrid RESTIR-Path Tracing & Diffusion approach for real-time SSS
- Could dramatically improve tissue translucency in anatomy viewers

### Integration Ideas
1. WebGPU compute shaders for volume rendering of CT/MRI data in SOMA
2. Henyey-Greenstein phase function for realistic tissue scattering
3. Progressive rendering for mobile-friendly quality scaling
4. MacroGrid for efficient skipping of empty voxels in anatomy datasets


## Sources

- https://news.ycombinator.com/item?id=46933474
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
