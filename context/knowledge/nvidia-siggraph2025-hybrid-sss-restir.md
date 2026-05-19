# nvidia-siggraph2025-hybrid-sss-restir

*Researched: 2026-04-06 02:18 CDT*

# NVIDIA SIGGRAPH 2025: Real-Time SSS via Hybrid ReSTIR-Path-Tracing & Diffusion

**Source:** SIGGRAPH 2025 Advances in Real-Time Rendering in Games (20th Anniversary)
**Presenter:** Tanki Zhang (NVIDIA)
**Date:** August 12, 2025

## Key Innovation
NVIDIA introduced a novel **hybrid solution for real-time subsurface scattering** that combines:
1. **ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) Path Tracing** — for accurate volumetric light transport in translucent materials
2. **Diffusion approximation** — for fast multi-scatter estimation

This hybrid approach bridges the gap between offline-quality SSS and real-time performance, which is critical for:
- **Medical visualization** (skin, organ tissue rendering)
- Game character skin rendering
- Wax, marble, and other translucent materials

## Relevance to SOMA
SOMA's 3D anatomy viewer currently uses screen-space SSS shaders (see `soma-sss-shaders` skill). This NVIDIA technique could provide:
- More physically accurate tissue rendering (skin, muscle, organ subsurface light transport)
- Real-time performance via ReSTIR's importance sampling
- Better visual quality for close-up anatomy views

## Implementation Considerations
- ReSTIR requires ray tracing capabilities (WebGPU ray tracing or compute-based approaches)
- Current WebGPU support for ray tracing is limited; may need compute shader emulation
- The diffusion component could be adapted to WGSL shaders independently
- For mobile (iOS Safari), would need fallback to screen-space methods

## Other SIGGRAPH 2025 Highlights Relevant to SOMA
- **Adaptive Voxel-Based OIT** (Activision) — order-independent transparency for anatomy cross-sections
- **Strand-based hair/fur rendering** (MachineGames) — could improve body surface detail
- **idTech8 Global Illumination** (id Software) — fast GI for ambient light in body cavities
- **MegaLights stochastic lighting** (Epic Games) — many-lights rendering for complex anatomy scenes

## Open Questions
- Will WebGPU ray tracing APIs mature enough for ReSTIR by 2026-2027?
- Can the diffusion component be implemented as a standalone WGSL compute shader?
- What's the minimum GPU tier needed for real-time hybrid SSS?


## Sources

- https://advances.realtimerendering.com/s2025/
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
