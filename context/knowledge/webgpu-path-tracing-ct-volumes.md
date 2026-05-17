# webgpu-path-tracing-ct-volumes

*Researched: 2026-04-05 19:46 CDT*

# WebGPU Path Tracing for Medical CT Volumes in Browser

**Source:** Hacker News Show HN (MickGorobets, ~Feb 2026)
**URL:** https://news.ycombinator.com/item?id=46933474

## Key Technical Details

A GPU path tracer for volumetric medical data running entirely in Chrome via WebGPU + WebAssembly (C++/Emscripten).

### Rendering Pipeline
- **Delta tracking (Woodcock null-collision algorithm)** for unbiased volume rendering
- **Cook-Torrance GGX BRDF** + **Henyey-Greenstein phase function** for light scattering
- **MacroGrid acceleration**: DDA empty-space skipping + GPU tile culling
- **Progressive frame accumulation**: noisy initially, converges to ground truth over frames

### Post-Processing
- **HDR pipeline**: bloom, auto-exposure
- **Tone mapping**: PBR Neutral / ACES

### Data Pipeline
- **Async mip-level streaming** with gzip decompression
- Built on **Diligent Engine** (author contributed to its WebGPU backend)

### SOMA Relevance
This is directly applicable to SOMA's anatomy viewer. Key takeaways:
1. **Delta tracking** is the gold standard for unbiased volume rendering — could replace ray-marching for CT/MRI slices
2. **MacroGrid acceleration** with DDA empty-space skipping would dramatically improve performance for sparse volumes
3. **Progressive accumulation** is a practical pattern: show a noisy preview immediately, converge over frames
4. **Henyey-Greenstein phase function** is essential for realistic tissue scattering (skin, fat, muscle)
5. **Mip-level streaming** solves the memory problem for large DICOM datasets on mobile

### Technical Feasibility for SOMA
- Requires Chrome with WebGPU enabled — NOT yet universal on iOS Safari
- Works on discrete GPU and integrated graphics
- C++/Emscripten → WASM compilation path is mature
- For Three.js-based SOMA: would need custom WebGPU compute shaders (Three.js WebGPU renderer is maturing)


## Sources

- https://news.ycombinator.com/item?id=46933474
