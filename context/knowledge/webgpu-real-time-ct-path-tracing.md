# webgpu-real-time-ct-path-tracing

*Researched: 2026-04-06 03:25 CDT*

# WebGPU Real-Time Path Tracing of Medical CT Volumes

## Source
Hacker News Show HN post by MickGorobets (Feb 2026)
URL: https://news.ycombinator.com/item?id=46933474
Live demo: https://grenzwert.net

## Key Technical Details
- **GPU path tracer** for volumetric medical data running entirely in Chrome via WebGPU + WebAssembly (C++/Emscripten)
- **Delta tracking** (Woodcock null-collision algorithm) for unbiased volume rendering
- **Cook-Torrance GGX BRDF** + **Henyey-Greenstein phase function** — physically-based rendering
- **MacroGrid acceleration**: DDA empty-space skipping + GPU tile culling
- **Progressive frame accumulation**: noisy at first, converges to ground truth
- **HDR pipeline**: bloom, auto-exposure, PBR Neutral / ACES tone mapping
- **Async mip-level streaming** with gzip decompression
- Built on **Diligent Engine** (contributor to its WebGPU backend)

## SOMA Relevance (HIGH)
- This is EXACTLY the rendering pipeline SOMA needs for realistic anatomy visualization
- The delta tracking + HG phase function approach is ideal for tissue rendering with subsurface scattering
- Progressive accumulation means interactive framerates are achievable even on mobile
- The mip-level streaming pattern handles large DICOM volumes efficiently
- C++/Emscripten approach is more mature than pure JS — consider for SOMA's rendering pipeline

## Integration Path
1. Study the Diligent Engine WebGPU backend for SOMA's rendering core
2. Implement Woodcock delta tracking for volume ray marching in anatomy viewer
3. Use Henyey-Greenstein phase function for subsurface scattering in tissue layers
4. Progressive accumulation allows smooth loading experience on mobile


## Sources

- https://news.ycombinator.com/item?id=46933474
- https://grenzwert.net
