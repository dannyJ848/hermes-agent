# ReSTIR-SSS-siggraph-2025-real-time-subsurface-scattering

*Researched: 2026-04-06 04:20 CDT*

# ReSTIR-SSS: Real-Time Subsurface Scattering via Hybrid Path Tracing & Diffusion

**Source:** SIGGRAPH 2025 Advances in Real-Time Rendering in Games (20th Anniversary)
**Author:** Tanki Zhang (NVIDIA)
**Date:** August 2025
**ACM DOI:** https://dl.acm.org/doi/abs/10.1145/3675372

## Abstract

NVIDIA introduces a novel **hybrid solution** for real-time subsurface scattering (SSS) that approaches path-traced quality. The technique combines:

1. **Volumetric ReSTIR Path Tracing** — Reservoir-based spatiotemporal importance resampling for volumetric light transport through translucent materials
2. **Physically-Based Diffusion Approximation** — Classical diffusion theory for areas where path tracing is expensive

## Key Innovation: Hybrid Approach

Traditional real-time SSS relies on **diffusion approximations** (e.g., screen-space blur methods), which produce artifacts in thin or curved regions. NVIDIA's hybrid method:

- Uses **ReSTIR (Reservoir-based Spatiotemporal Importance Resampling)** to efficiently sample volumetric scattering paths
- Falls back to **diffusion approximation** where path tracing is computationally expensive
- Achieves **path-traced quality** at real-time frame rates on current-generation hardware
- Handles thin structures and curved surfaces without the artifacts of pure diffusion

## Relevance to SOMA Anatomy Viewer

This is **directly applicable** to SOMA's 3D anatomy rendering:

1. **Skin rendering** — Human skin is the classic SSS material (waxiness, light bleeding through ears/fingers)
2. **Organ tissue** — Internal organs exhibit strong subsurface scattering (liver, brain tissue, muscles)
3. **Thin anatomical structures** — Ear cartilage, eyelids, intestinal walls — exactly where diffusion fails
4. **Real-time performance** — Must run on mobile (iOS WKWebView), so hybrid approach matters

## Implementation Considerations for SOMA

- **WebGPU availability**: ReSTIR requires compute shaders — available in WebGPU but NOT WebGL2
- **Mobile GPU constraints**: iOS Safari supports WebGPU since iOS 16.4+; SOMA should detect and degrade gracefully
- **Fallback strategy**: Pure diffusion approximation (screen-space blur) for WebGL2 devices, hybrid ReSTIR for WebGPU
- **Existing skill**: `soma-sss-shaders` already covers basic SSS — this research upgrades it to state-of-the-art

## SIGGRAPH 2025 Course Context

Part of the 20th anniversary "Advances in Real-Time Rendering in Games" course featuring:
- Activision: Adaptive Voxel-Based Order-Independent Transparency
- Ubisoft: Ray Tracing in Assassin's Creed Shadows
- id Software: idTech8 Global Illumination
- Epic Games: MegaLights Stochastic Direct Lighting in UE5
- MachineGames: Strand-based hair/fur rendering

## References

- Paper: https://dl.acm.org/doi/abs/10.1145/3675372
- Slides: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Video: https://www.youtube.com/watch?v=AtFBbMnUgoc
- Course page: https://advances.realtimerendering.com/s2025/


## Sources

- https://dl.acm.org/doi/abs/10.1145/3675372
- https://advances.realtimerendering.com/s2025/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.youtube.com/watch?v=AtFBbMnUgoc
