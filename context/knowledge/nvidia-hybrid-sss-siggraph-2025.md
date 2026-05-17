# nvidia-hybrid-sss-siggraph-2025

*Researched: 2026-04-05 23:12 CDT*

# NVIDIA Hybrid Real-Time Subsurface Scattering (SIGGRAPH 2025)

## Source
SIGGRAPH 2025 "Advances in Real-Time Rendering in Games" — 20th anniversary course.
Speaker: Tanki Zhang (NVIDIA)
Part of the session on Aug 12, 2025.

## Technique: Hybrid ReSTIR-Path-Tracing + Diffusion
NVIDIA introduced a novel **hybrid solution** combining:
1. **Volumetric path tracing** via ReSTIR (Reservoir-based Spatiotemporal Importance Resampling)
2. **Physically-based diffusion** model for subsurface scattering

This replaces older screen-space SSS approximations (e.g., separable Gaussians from GPU Gems 3) with a physically accurate approach that works in real-time.

## Relevance to SOMA
- **Directly applicable** to 3D anatomy rendering where skin realism matters
- Current SOMA SSS uses separable screen-space blur (GPU Gems 3 Chapter 14 approach)
- Hybrid technique could provide significantly more accurate skin translucency
- ReSTIR-based approach handles complex geometry (ears, nose) better than screen-space methods
- WebGPU compute shaders could implement the diffusion component
- Path tracing component may be too heavy for mobile — but diffusion alone is viable

## Implementation Path (for SOMA)
1. Start with diffusion-only SSS (no path tracing) for mobile compatibility
2. Use WebGPU compute pipeline for the diffusion step
3. Profile against current separable Gaussian approach
4. Consider ReSTIR path tracing as optional high-quality mode for desktop

## Other Notable Talks (Same Session)
- **Adaptive Voxel-Based Order-Independent Transparency** (Activision) — useful for layered anatomy
- **idTech8 Global Illumination** (id Software) — GI techniques adaptable to medical scenes
- **MegaLights: Stochastic Direct Lighting in UE5** (Epic) — many-lights for anatomy viewers
- **Strand-based hair/fur rendering** (MachineGames) — applicable to anatomical hair/fiber rendering

## References
- SIGGRAPH 2025 Advances course page: https://advances.realtimerendering.com/s2025/
- PDF slides: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- YouTube talk: https://www.youtube.com/watch?v=AtFBbMnUgoc


## Sources

- https://advances.realtimerendering.com/s2025/
- https://www.youtube.com/watch?v=AtFBbMnUgoc
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
