# WebGPU Real-Time Path Tracing for Medical CT Volumes

*Researched: 2026-04-06 04:46 CDT*

# WebGPU Real-Time Path Tracing for Medical CT Volumes

## Source: Grenzwert by Mikhail Gorobets (2025)

A GPU path tracer for volumetric medical data running entirely in Chrome via **WebGPU + WebAssembly (C++/Emscripten)**.

### Key Technical Details

1. **Delta Tracking (Woodcock null-collision algorithm)** — Unbiased volume rendering without pre-computation
2. **Cook-Torrance GGX BRDF + Henyey-Greenstein phase function** — Physically-based light interaction
3. **MacroGrid acceleration** — DDA empty-space skipping + GPU tile culling for performance
4. **Progressive frame accumulation** — Noisy at first, converges to ground truth over frames
5. **HDR pipeline** — Bloom, auto-exposure, PBR Neutral / ACES tone mapping
6. **Async mip-level streaming with gzip decompression** — Handles large volumetric datasets

### Built On
- **Diligent Engine** — Cross-platform graphics engine with WebGPU backend
- **C++ compiled to WASM via Emscripten**

### Performance Requirements
- Chrome with WebGPU enabled
- Works on discrete GPU (best) and integrated GPU (functional)
- Other browsers don't fully support WebGPU yet

### SOMA Relevance
This validates the approach of using WebGPU for browser-based medical visualization. Key techniques portable to SOMA:
- Delta tracking for volumetric tissue rendering (could replace mesh-only approach for certain organs)
- Henyey-Greenstein phase function for realistic subsurface light scattering in skin/tissue
- MacroGrid acceleration for handling large anatomy datasets on mobile
- Progressive rendering pattern ideal for mobile — start noisy, refine while user explores

### SIGGRAPH 2025 Advances
Additionally, SIGGRAPH 2025 introduced a novel **hybrid ReSTIR-Path Tracing + Diffusion** approach for real-time subsurface scattering. This combines:
- ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) for efficient light sampling
- Diffusion approximation for fast subsurface scattering
- Could achieve real-time SSS on consumer hardware, directly applicable to realistic skin rendering in SOMA

### Integration Considerations
- SOMA currently uses Three.js (WebGL). Migration path: Three.js → Three.js WebGPU renderer → custom WGSL shaders
- Progressive rendering aligns with mobile-first approach (render quality scales with available GPU)
- WASM + WebGPU combo proven viable for complex medical workloads in browser


## Sources

- https://news.ycombinator.com/item?id=46933474
- https://www.webgpu.com/showcase/grenzwert-volumetric-ct-rendering-webgpu/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
