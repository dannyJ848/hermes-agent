# webgpu-medical-volume-rendering

*Researched: 2026-04-06 19:40 CDT*

# WebGPU Medical Volume Rendering — Key Techniques (2025-2026)

## 1. Real-Time Path Tracing of CT Volumes in Browser (MickGorobets, Jan 2026)
Source: https://news.ycombinator.com/item?id=46933474

**Architecture:** GPU path tracer for volumetric medical data running entirely in Chrome via WebGPU + WebAssembly (C++/Emscripten).

**Key techniques relevant to SOMA:**
- **Delta tracking (Woodcock null-collision algorithm)** — Unbiased volume rendering, no pre-computation needed
- **Cook-Torrance GGX BRDF + Henyey-Greenstein phase function** — Physically accurate light scattering through tissue
- **MacroGrid acceleration** — DDA empty-space skipping + GPU tile culling for performance
- **Progressive frame accumulation** — Noisy at first, converges to ground truth (ideal for mobile where single-frame perf matters)
- **HDR pipeline** — Bloom, auto-exposure, PBR Neutral / ACES tone mapping
- **Async mip-level streaming with gzip decompression** — Critical for mobile bandwidth
- Built on **Diligent Engine** (cross-platform graphics framework with WebGPU backend)

**SOMA implications:**
- Delta tracking could replace pre-baked SSS shaders for more realistic tissue rendering
- Progressive accumulation is mobile-friendly (render low quality first, improve over time)
- Mip-level streaming solves mobile bandwidth constraints for large anatomy datasets
- Henyey-Greenstein phase function directly applicable to subsurface scattering in anatomical tissue

## 2. WebGPU Volume Rendering Framework (MDPI Applied Sciences, 2025)
Source: https://www.mdpi.com/2076-3417/15/5/2782
- WebGPU-based volume rendering for interactive visualization of scalar data
- Applicable to medical imaging pipelines

## 3. WebGPU Client-Side AI for Dermatological Diagnostics (Patel, Feb 2026)
Source: ResearchGate publication
- Privacy-preserving: runs inference entirely client-side via WebGPU
- Relevant to SOMA's potential AI diagnostic features
- Proves WebGPU can handle both rendering AND inference workloads

## 4. FusionRender — WebGPU Performance (ACM, 2025)
Source: https://dl.acm.org/doi/abs/10.1145/3589334.3645395
- 29.3%-122.1% rendering performance improvement over existing baselines
- General WebGPU optimization techniques applicable to anatomy rendering


## Sources

- https://news.ycombinator.com/item?id=46933474
- https://www.mdpi.com/2076-3417/15/5/2782
- https://www.researchgate.net/publication/401110730
- https://dl.acm.org/doi/abs/10.1145/3589334.3645395
