# webgpu-medical-volume-rendering-techniques

*Researched: 2026-04-05 14:16 CDT*

# WebGPU Medical Volume Rendering Techniques (2025-2026)

## Key Finding: Real-time Path Tracing of CT Volumes in Browser
**Source:** Hacker News Show HN by MickGorobets (Feb 2026)
**URL:** https://news.ycombinator.com/item?id=46933474

### Core Rendering Pipeline
- **Delta tracking (Woodcock null-collision algorithm)** for unbiased volume rendering — eliminates need for explicit ray-surface intersection
- **Cook-Torrance GGX BRDF** for surface shading + **Henyey-Greenstein phase function** for volumetric scattering
- **MacroGrid acceleration** — DDA empty-space skipping + GPU tile culling for performance
- **Progressive frame accumulation** — noisy first frame converges to ground truth over frames
- **HDR pipeline**: bloom, auto-exposure, PBR Neutral / ACES tone mapping
- **Async mip-level streaming** with gzip decompression for large volumes

### Tech Stack
- WebGPU + WebAssembly (C++/Emscripten)
- Built on **Diligent Engine** (open-source graphics framework with WebGPU backend)
- Requires Chrome with WebGPU enabled; discrete GPU recommended but works on integrated

### SOMA Integration Potential
1. **Henyey-Greenstein phase function** — applicable to subsurface scattering in anatomical tissue (skin, organs)
2. **MacroGrid acceleration** — could optimize SOMA's anatomy model loading with empty-space culling
3. **Progressive accumulation** — ideal for mobile where first-frame latency matters; show low-quality preview immediately
4. **Async mip streaming** — directly relevant to SOMA's LOD strategy for large anatomical datasets
5. **Diligent Engine** — potential alternative to raw Three.js for WebGPU backend

### Related: MDPI WebGPU Volume Rendering Framework
**URL:** https://www.mdpi.com/2076-3417/15/5/2782
- WebGPU-based volume rendering framework for interactive scalar data visualization
- Academic implementation of similar techniques

### Related: WebGPU Client-Side Medical AI
**URL:** https://www.researchgate.net/publication/401110730
- WebGPU compute shaders for on-device skin lesion classification
- Privacy-preserving medical diagnostics running client-side via WebGPU compute
- Demonstrates WebGPU compute pipeline viable for real medical inference tasks


## Sources

- https://news.ycombinator.com/item?id=46933474
- https://www.mdpi.com/2076-3417/15/5/2782
- https://www.researchgate.net/publication_401110730
