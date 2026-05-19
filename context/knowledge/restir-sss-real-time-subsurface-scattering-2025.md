# ReSTIR-SSS-Real-Time-Subsurface-Scattering-2025

*Researched: 2026-04-06 05:31 CDT*

# ReSTIR Subsurface Scattering for Real-Time Path Tracing (SIGGRAPH 2025)

## Key Innovation
A **hybrid solution** combining diffusion approximation with path tracing via ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) for real-time subsurface scattering that approaches offline path-traced quality.

## Technical Approach
- Traditional real-time SSS uses **screen-space diffusion approximations** (Gaussian kernels in texture space) — fast but inaccurate for complex geometry
- New method: **Hybrid ReSTIR-Path Tracing + Diffusion**
  - Uses ReSTIR sampling to efficiently find important light paths through translucent materials
  - Combines sequential and spatial shifting strategies for better sample reuse
  - Enhances denoising quality through better sample distribution
  - Runs fast enough for current-gen game pipelines (60fps target)

## Why This Matters for SOMA
- **Anatomy rendering**: Skin, organs, and tissue all exhibit strong subsurface scattering — the soft, translucent appearance is critical for realism
- **Mobile WebGPU**: ReSTIR's reservoir-based approach is highly parallelizable — maps well to GPU compute shaders
- **Current SOMA approach**: We use screen-space Gaussian blur for SSS (fast but flat-looking). Hybrid approach could dramatically improve organ/tissue realism
- **Implementation path**: Could implement a simplified ReSTIR SSS in WGSL compute shaders for the Three.js WebGPU renderer

## Sources
- ACM DL: https://dl.acm.org/doi/abs/10.1145/3675372
- SIGGRAPH 2025 course: https://advances.realtimerendering.com/s2025/
- PDF slides: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Video: https://www.youtube.com/watch?v=AtFBbMnUgoc

## Integration Priority
**Medium-High** — After base anatomy model rendering is stable, this technique could be the differentiator that makes SOMA's visuals stand out from competitors (Complete Anatomy, BioDigital). The hybrid approach means we can fall back to diffusion-only on low-end devices.


## Sources

- https://dl.acm.org/doi/abs/10.1145/3675372
- https://advances.realtimerendering.com/s2025/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
