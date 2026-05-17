# WebGPU Real-Time Medical Volume Path Tracing (2025)

*Researched: 2026-04-05 16:19 CDT*

# WebGPU Real-Time Medical Volume Path Tracing

**Source:** Hacker News Show HN (Feb 2025) by MickGorobets
**URL:** https://grenzwert.net (demo site)

## Key Technical Approach
- GPU path tracer for volumetric medical CT data running entirely in Chrome via **WebGPU + WebAssembly (C++/Emscripten)**
- Uses **Delta tracking (Woodcock null-collision algorithm)** for unbiased volume rendering
- **Cook-Torrance GGX BRDF** + **Henyey-Greenstein phase function** for realistic light scattering
- **MacroGrid acceleration**: DDA empty-space skipping + GPU tile culling
- **Progressive frame accumulation**: noisy at first, converges to ground truth over frames
- HDR pipeline: bloom, auto-exposure, PBR Neutral / ACES tone mapping
- Async mip-level streaming with gzip decompression

## SOMA Relevance
- Directly applicable to SOMA's 3D anatomy viewer — could replace/expensive Three.js volume rendering
- WebGPU path tracing achieves real-time medical volume visualization without server-side rendering
- The DDA empty-space skipping + tile culling pattern is relevant for mobile performance optimization
- Progressive accumulation is ideal for mobile: render low quality first, refine when user pauses
- Built on **Diligent Engine** (open-source) which has WebGPU backend — could be an alternative to Three.js for medical volumes

## SIGGRAPH 2025 SSS Advances (Related)
- SIGGRAPH 2025 course: "RT Subsurface Scattering via Hybrid RESTIR-Path Tracing & Diffusion"
- Novel hybrid approach combining ReSTIR path tracing with diffusion approximation
- Relevant for realistic skin/organ rendering in SOMA — current SSS shader uses simpler approximation
- Paper: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf


## Sources

- https://news.ycombinator.com/item?id=46933474
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
