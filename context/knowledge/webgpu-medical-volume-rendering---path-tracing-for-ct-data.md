# WebGPU Medical Volume Rendering - Path Tracing for CT Data

*Researched: 2026-04-05 23:34 CDT*

# WebGPU Path Tracing for Medical CT Volumes

**Source:** Hacker News Show HN (Feb 2026), by MickGorobets
**URL:** https://grenzwert.net (demo), https://news.ycombinator.com/item?id=46933474

## Key Techniques
- **Delta tracking (Woodcock null-collision algorithm)** for unbiased volume rendering
- **Cook-Torrance GGX BRDF** + **Henyey-Greenstein phase function** for light scattering
- **MacroGrid acceleration**: DDA empty-space skipping + GPU tile culling
- **Progressive frame accumulation**: noisy first frame, converges to ground truth
- **HDR pipeline**: bloom, auto-exposure, PBR Neutral / ACES tone mapping
- **Async mip-level streaming** with gzip decompression

## Architecture
- Built on **Diligent Engine** (contributed WebGPU backend)
- C++ compiled to **WebAssembly via Emscripten**
- Runs entirely in Chrome (WebGPU required)
- Works on discrete and integrated GPUs

## Relevance to SOMA
1. **Volume rendering approach**: SOMA could adopt delta tracking for rendering volumetric medical data (CT/MRI slices) alongside mesh-based anatomy
2. **HG phase function**: Essential for realistic subsurface scattering in tissue — matches SOMA's SSS shader needs
3. **Progressive accumulation**: Perfect for mobile where instant full quality is too expensive
4. **Mip-level streaming**: Pattern for SOMA's asset pipeline — stream anatomy models at varying detail levels
5. **WebGPU readiness**: Validates that browser-based medical rendering at production quality is feasible

## Complementary: SIGGRAPH 2025 SSS Advances
- Hybrid RESTIR-Path Tracing + Diffusion for real-time SSS (SIGGRAPH 2025 Advances course)
- Paper: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Could inform next-gen SSS shaders for SOMA's tissue rendering

## Implementation Priority for SOMA
- **Phase 1**: Adopt HG phase function in existing Three.js SSS shader
- **Phase 2**: Progressive accumulation pattern for mobile performance
- **Phase 3**: Investigate Diligent Engine's WebGPU backend as alternative to raw Three.js


## Sources

- https://news.ycombinator.com/item?id=46933474
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.reddit.com/r/GraphicsProgramming/comments/1lfku5c/playing_around_with_realtime_subsurface/
