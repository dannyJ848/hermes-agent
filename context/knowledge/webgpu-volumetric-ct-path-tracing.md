# webgpu-volumetric-ct-path-tracing

*Researched: 2026-04-06 19:52 CDT*

# WebGPU Volumetric CT Path Tracing in Browser

**Source:** Hacker News Show HN (Feb 2026) by MickGorobets
**URL:** https://grenzwert.net (demo), https://news.ycombinator.com/item?id=46933474

## Key Technical Details

A GPU path tracer for volumetric medical data running entirely in Chrome via **WebGPU + WebAssembly (C++/Emscripten)**.

### Rendering Pipeline
- **Delta tracking (Woodcock null-collision algorithm)** for unbiased volume rendering
- **Cook-Torrance GGX BRDF** + **Henyey-Greenstein phase function** — physically-based lighting
- **MacroGrid acceleration**: DDA empty-space skipping + GPU tile culling
- **Progressive frame accumulation**: noisy at first, converges to ground truth
- **HDR pipeline**: bloom, auto-exposure, PBR Neutral / ACES tone mapping
- **Async mip-level streaming** with gzip decompression

### Engineering Stack
- Built on **Diligent Engine** (cross-platform graphics engine with WebGPU backend)
- C++ compiled to WASM via Emscripten
- Requires Chrome with WebGPU enabled
- Works on discrete GPU best, but runs on integrated too

## Relevance to SOMA

This is directly applicable to SOMA's 3D anatomy viewer:
1. **Delta tracking / Woodcock algorithm** — could replace basic ray marching for more realistic tissue rendering
2. **Henyey-Greenstein phase function** — essential for subsurface scattering in tissue (already tracked in soma-sss-shaders skill)
3. **MacroGrid acceleration** — DDA empty-space skipping would improve performance for sparse anatomy data
4. **Progressive accumulation** — good UX pattern: show noisy preview immediately, refine over frames
5. **Mip-level streaming** — critical for large DICOM volumes on mobile

### Integration Path
- SOMA currently uses Three.js (WebGL). WebGPU migration is the prerequisite.
- Diligent Engine's WebGPU backend could serve as reference implementation.
- Phase function parameters could be tuned per tissue type (bone vs soft tissue vs fat).

## Related Work
- TU Wien FeatureLego: WebGPU volume rendering with D3.js cluster visualization (2025)
- OHIF Viewer: GPU-accelerated DICOM streaming with PET/CT fusion
- LinkedIn: WebGPU MRI pipeline with Phong reflection for digital twins

## Sources

- https://news.ycombinator.com/item?id=46933474
- https://www.cg.tuwien.ac.at/courses/Vis2/HallOfFame/2025/visvu-2025-jadhav-goncalves-schiebel-main/website/documentation.html
- https://www.researchgate.net/publication/393563051_Real-Time_Volumetric_Visualisations_of_Cone-Beam_Computed_Tomography_Scans_as_a_Simulation_Framework_for_Radiographic_Anatomy_Learning
