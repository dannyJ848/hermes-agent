# webgpu-realtime-medical-volume-rendering

*Researched: 2026-04-06 01:55 CDT*

# WebGPU Real-Time Medical Volume Path Tracing

## Source
Hacker News Show HN post by MickGorobets (Feb 2026)
URL: https://news.ycombinator.com/item?id=46933474

## Key Technical Details
A GPU path tracer for volumetric medical data running entirely in Chrome via **WebGPU + WebAssembly (C++/Emscripten)**.

### Rendering Pipeline
- **Delta tracking** (Woodcock null-collision algorithm) for unbiased volume rendering
- **Cook-Torrance GGX BRDF** + **Henyey-Greenstein phase function** for anisotropic scattering
- **MacroGrid acceleration** — DDA empty-space skipping + GPU tile culling
- **Progressive frame accumulation** — noisy first frame, converges to ground truth
- **HDR pipeline**: bloom, auto-exposure, PBR Neutral / ACES tone mapping
- **Async mip-level streaming** with gzip decompression

### Infrastructure
- Built on **Diligent Engine** (contributor to its WebGPU backend)
- Requirements: Chrome with WebGPU enabled
- Works on discrete and integrated GPUs

## Relevance to SOMA
1. **Volume rendering of CT data** — SOMA could use similar delta tracking for anatomical cross-sections
2. **Henyey-Greenstein phase function** — directly applicable to skin SSS in anatomy viewer
3. **Progressive accumulation** — viable for mobile WebGPU when it ships
4. **Mip-level streaming** — relevant for SOMA's asset pipeline (DICOM → optimized meshes)
5. **Diligent Engine** — cross-platform WebGPU abstraction worth evaluating vs raw WebGPU API

## SIGGRAPH 2025 SSS Advances (Parallel Finding)
SIGGRAPH 2025 "Advances in Real-Time Rendering" course includes:
- **Hybrid ReSTIR-Path Tracing & Diffusion** for real-time subsurface scattering
- Published PDF: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Key technique: combines ReSTIR resampling with diffusion approximation for skin rendering
- Could replace SOMA's current SSS shader approach with path-traced subsurface

## Action Items for SOMA
- Evaluate Diligent Engine as WebGPU abstraction layer
- Study Woodcock delta tracking for volume rendering mode
- Implement Henyey-Greenstein phase function in existing SSS shader
- Monitor mobile WebGPU adoption for progressive accumulation viability


## Sources

- https://news.ycombinator.com/item?id=46933474
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
