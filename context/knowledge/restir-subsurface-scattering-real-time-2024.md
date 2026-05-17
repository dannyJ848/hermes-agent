# reSTIR-subsurface-scattering-real-time-2024

*Researched: 2026-04-06 06:13 CDT*

# ReSTIR Subsurface Scattering for Real-Time Path Tracing (2024)

## Paper Info
- **Title:** ReSTIR Subsurface Scattering for Real-Time Path Tracing
- **Authors:** Tanki Zhang (NVIDIA), et al. — KIT (Karlsruhe Institute of Technology)
- **Venue:** SIGGRAPH 2024 / ACM Transactions on Graphics, presented at SIGGRAPH 2025 Advances in Real-Time Rendering
- **DOI:** 10.1145/3675372
- **PDF:** https://cg.ivd.kit.edu/publications/2024/restir-sss/restir-sss.pdf
- **Video:** https://www.youtube.com/watch?v=AtFBbMnUgoc

## Key Innovation
Extends the **ReSTIR (Reservoir-based Spatiotemporal Importance Resampling)** framework to handle subsurface scattering in real-time path tracing. This is a hybrid approach combining:

1. **Hybrid shift mapping** — A local SSS-specific criterion that deterministically selects between two shift strategies for each path, combining the strengths of both
2. **Sequential shift** — For temporal reuse of SSS paths across frames
3. **Diffusion approximation integration** — Combines path-traced SSS with screen-space diffusion for a practical hybrid solution

## Why It Matters for SOMA
- SOMA's 3D anatomy viewer needs realistic skin/tissue rendering on mobile WebGPU
- Traditional screen-space SSS (like Gaussian blur in texture space) has artifacts — this ReSTIR approach significantly reduces noise and denoising artifacts
- The hybrid approach (ReSTIR + diffusion) is especially interesting because SOMA may not have full RT hardware on mobile, but could use the diffusion component alone or a simplified ReSTIR on higher-end devices
- The SIGGRAPH 2025 Advances talk (Aug 12, 2025) by Tanki Zhang will have updated slides with production-ready details

## Technical Details (from abstract)
- "Subsurface scattering is an important visual cue and in real-time rendering it is often approximated using screen-space algorithms"
- They apply ReSTIR using hybrid and sequential shifts in real-time path tracing to "significantly reduce noise and denoising artifacts"
- Local SSS-specific criterion for hybrid shift deterministically selects one of two shifts for a path

## Relevance to SOMA Architecture
- **Current approach:** SOMA uses WGSL screen-space Gaussian blur for SSS (soma-sss-shaders skill)
- **Potential upgrade path:** Implement simplified diffusion-based SSS with optional ReSTIR on devices with RT cores
- **Mobile consideration:** The diffusion component alone could improve quality over simple Gaussian blur without needing ray tracing
- **WebGPU compatibility:** ReSTIR requires compute shaders (available in WebGPU) but full path tracing may be too expensive on mobile — hybrid approach allows graceful degradation

## SIGGRAPH 2025 Advances Course Context
This paper is being presented as part of the "Real-Time Subsurface Scattering via Hybrid ReSTIR-Path-Tracing and Diffusion" talk at SIGGRAPH 2025 Advances in Real-Time Rendering (Part II), alongside talks on:
- idTech8 Global Illumination (id Software)
- Stochastic Tile-Based Lighting (HypeHype)
- MegaLights stochastic direct lighting in UE5 (Epic Games)


## Sources

- https://dl.acm.org/doi/abs/10.1145/3675372
- https://cg.ivd.kit.edu/publications/2024/restir-sss/restir-sss.pdf
- https://advances.realtimerendering.com/s2025/index.html
- https://www.youtube.com/watch?v=AtFBbMnUgoc
