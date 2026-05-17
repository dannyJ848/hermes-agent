# real-time-subsurface-scattering-2025

*Researched: 2026-04-06 20:17 CDT*

# Real-Time Subsurface Scattering: 2025 State of the Art

## ReSTIR SSS (KIT / NVIDIA, SIGGRAPH 2024-2025)

**Paper:** "ReSTIR Subsurface Scattering for Real-Time Path Tracing" (KIT Karlsruhe + NVIDIA)
- ACM DOI: 10.1145/3675372
- Authors from KIT (Karlsruhe Institute of Technology) + NVIDIA

**Core technique:** Applies ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) specifically to subsurface scattering in real-time path tracing. Uses hybrid and sequential shift mapping to:
- Significantly reduce noise in SSS regions
- Reduce denoising artifacts compared to traditional diffusion-based SSS
- Achieve real-time performance at interactive framerates

## NVIDIA Hybrid RT SSS (SIGGRAPH 2025 Advances in Real-Time Rendering)

**Talk:** "RT Subsurface Scattering via Hybrid ReSTIR-Path Tracing & Diffusion"
- Presented at SIGGRAPH 2025 "Advances in Real-Time Rendering in Games" (20th anniversary session)
- Introduces a **hybrid approach** combining:
  1. Volumetric path tracing (via ReSTIR resampling)
  2. New physically-based diffusion approximation
- Key insight: Traditional screen-space diffusion SSS produces artifacts in thin/curved regions. The hybrid approach uses path tracing where it matters and diffusion where it's sufficient.

## Relevance to SOMA 3D Anatomy Viewer

For SOMA's Three.js/WebGPU anatomy viewer:
1. **Diffusion profiles** remain the most practical real-time SSS for WebGL/WebGPU — screen-space, no path tracing needed
2. **WebGPU compute shaders** could implement simplified ReSTIR-style importance resampling for tissue rendering
3. **Thin structure handling** (blood vessels, skin layers) is exactly where diffusion SSS fails — the hybrid approach addresses this
4. NVIDIA's artist-friendly physically-based parameters are relevant for configuring tissue materials

## Implementation Priority for SOMA
- Short-term: Keep screen-space diffusion SSS (soma-sss-shaders skill)
- Medium-term: When WebGPU compute is stable, implement importance resampling for SSS in thin tissue regions
- Reference: The KIT paper's shift mapping strategy could be adapted as a WebGPU compute pass

## Sources
- KIT PDF: https://cg.ivd.kit.edu/publications/2024/restir-sss/restir-sss.pdf
- SIGGRAPH 2025 talk: https://www.youtube.com/watch?v=AtFBbMnUgoc
- SIGGRAPH 2025 Advances session: https://advances.realtimerendering.com/s2025/


## Sources

- https://cg.ivd.kit.edu/publications/2024/restir-sss/restir-sss.pdf
- https://dl.acm.org/doi/abs/10.1145/3675372
- https://www.youtube.com/watch?v=AtFBbMnUgoc
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
