# WebGPU Medical CT Volume Path Tracing

*Researched: 2026-04-05 17:25 CDT*

# WebGPU Medical CT Volume Path Tracing (2026)

## Source
Hacker News Show HN by MickGorobets (Feb 2026). Demo at grenzwert.net.

## Key Technical Details
- **GPU path tracer for volumetric medical data** running entirely in Chrome via WebGPU + WebAssembly (C++/Emscripten)
- **Delta tracking** (Woodcock null-collision algorithm) for unbiased volume rendering
- **Cook-Torrance GGX BRDF** + **Henyey-Greenstein phase function** — production-quality shading
- **MacroGrid acceleration**: DDA empty-space skipping + GPU tile culling for performance
- **Progressive frame accumulation**: noisy at first, converges to ground truth over frames
- **HDR pipeline**: bloom, auto-exposure, PBR Neutral / ACES tone mapping
- **Async mip-level streaming** with gzip decompression — handles large volumes
- Built on **Diligent Engine** (contributor to its WebGPU backend)

## Relevance to SOMA
- Directly demonstrates WebGPU can handle medical volume rendering in-browser
- The Delta tracking / null-collision approach could replace our simpler SSS shader for realistic tissue rendering
- Henyey-Greenstein phase function is exactly what's needed for realistic subsurface light scattering in tissue
- MacroGrid acceleration pattern applicable to our anatomy LOD system
- Progressive accumulation is a viable quality fallback for lower-end devices

## SIGGRAPH 2025 SSS Advancement (complementary)
- SIGGRAPH 2025 Advances course covers real-time SSS via hybrid ReSTIR-path tracing + diffusion
- PDF: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- This represents the state-of-the-art for real-time subsurface scattering

## Action Items for SOMA
1. Evaluate Diligent Engine as alternative to raw WebGPU for SOMA's renderer
2. Implement Henyey-Greenstein phase function for tissue translucency
3. Consider progressive accumulation for quality modes on desktop
4. Study the Woodcock null-collision algorithm for unbiased tissue rendering

## Sources

- https://news.ycombinator.com/item?id=46933474
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
