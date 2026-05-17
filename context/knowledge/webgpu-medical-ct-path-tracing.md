# webgpu-medical-ct-path-tracing

*Researched: 2026-04-06 06:07 CDT*

# WebGPU Medical CT Volume Path Tracing (2025)

**Source:** Hacker News Show HN by MickGorobets (Feb 2026)
**URL:** https://grenzwert.net (demo) | https://news.ycombinator.com/item?id=46933474

## Key Technical Details
- **GPU path tracer** for volumetric medical data running entirely in Chrome via **WebGPU + WebAssembly (C++/Emscripten)**
- **Delta tracking** (Woodcock null-collision algorithm) for unbiased volume rendering
- **Cook-Torrance GGX BRDF** + **Henyey-Greenstein phase function** for scattering
- **MacroGrid acceleration**: DDA empty-space skipping + GPU tile culling
- **Progressive frame accumulation** — noisy at first, converges to ground truth
- **HDR pipeline**: bloom, auto-exposure, PBR Neutral / ACES tone mapping
- **Async mip-level streaming** with gzip decompression

## Architecture
- Built on **Diligent Engine** (author contributed to its WebGPU backend)
- Requires Chrome with WebGPU enabled
- Works on discrete and integrated GPUs

## Relevance to SOMA
This proves that real-time medical volume rendering in the browser via WebGPU is achievable today. Key patterns to adopt:
1. **Progressive accumulation** — acceptable for anatomy viewing where users dwell on structures
2. **MacroGrid + DDA** — empty-space skipping is essential for CT data performance
3. **Henyey-Greenstein phase function** — models light scattering in tissue correctly
4. **Async mip-level streaming** — critical for loading large DICOM volumes on mobile
5. **Diligent Engine** — cross-platform graphics API that supports WebGPU

## SOTA Reference: SIGGRAPH 2025 SSS
- Real-time SSS via hybrid **ReSTIR-Path Tracing + Diffusion** (SIGGRAPH 2025 Advances)
- PDF: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Novel hybrid solution combining path tracing with diffusion approximation for real-time subsurface scattering


## Sources

- https://news.ycombinator.com/item?id=46933474
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
