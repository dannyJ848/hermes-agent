# webgpu-path-tracing-medical-ct

*Researched: 2026-04-06 04:22 CDT*

# WebGPU Real-Time Path Tracing for Medical CT Volumes

## Source
Show HN by MickGorobets (Feb 2026) — grenzwert.net

## Key Technical Details
A GPU path tracer for volumetric medical data running entirely in Chrome via WebGPU + WebAssembly (C++/Emscripten).

### Rendering Pipeline
- **Delta tracking (Woodcock null-collision algorithm)** for unbiased volume rendering
- **Cook-Torrance GGX BRDF** + **Henyey-Greenstein phase function** for scattering
- **MacroGrid acceleration**: DDA empty-space skipping + GPU tile culling
- **Progressive frame accumulation**: noisy at first, converges to ground truth
- **HDR pipeline**: bloom, auto-exposure, PBR Neutral / ACES tone mapping
- **Async mip-level streaming** with gzip decompression

### Infrastructure
- Built on **Diligent Engine** (author contributed to its WebGPU backend)
- Requires Chrome with WebGPU enabled
- Works on discrete GPU best, runs on integrated too
- C++ compiled to WASM via Emscripten

## Relevance to SOMA
- **Directly applicable**: SOMA's 3D anatomy viewer could adopt this pipeline for volumetric rendering of CT/MRI data
- **Henyey-Greenstein phase function**: Essential for realistic subsurface scattering in anatomical tissue
- **MacroGrid + DDA skipping**: Performance optimization pattern applicable to SOMA's LOD system
- **Progressive accumulation**: Pattern for maintaining interactivity while converging to quality — ideal for mobile where GPU budget is limited
- **Diligent Engine**: Worth evaluating as alternative to raw Three.js for SOMA's WebGPU path

## Follow-up
- Evaluate Diligent Engine's WebGPU backend for SOMA integration
- Implement Henyey-Greenstein phase function in SOMA's SSS shader
- Research Woodcock delta tracking for potential volumetric anatomy rendering


## Sources

- https://news.ycombinator.com/item?id=46933474
- https://grenzwert.net
