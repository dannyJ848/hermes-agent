# SIGGRAPH-2025-real-time-sss-hybrid-restir

*Researched: 2026-04-05 14:31 CDT*

# SIGGRAPH 2025: Real-Time Subsurface Scattering via Hybrid ReSTIR-Path-Tracing & Diffusion

**Date:** August 12, 2025 (SIGGRAPH 2025, Vancouver)
**Speaker:** Tanki Zhang (NVIDIA)
**Course:** Advances in Real-Time Rendering in Games — 20th Anniversary Edition

## Key Innovation
NVIDIA introduces a **hybrid real-time subsurface scattering technique** combining:
1. **Volumetric path tracing** (ReSTIR-based resampled importance sampling)
2. **Physically based diffusion approximation**

This replaces screen-space SSS approximations with true volume-aware scattering.

## Relevance to SOMA
- Current SOMA SSS uses screen-space Gaussian blur (cheap but inaccurate for thin anatomical structures like ears, nose, fingers)
- NVIDIA's hybrid approach could provide physically accurate light transmission through tissue layers
- ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) enables real-time performance by reusing light samples across frames
- Compatible with WebGPU compute shaders — ReSTIR is a sampling algorithm, not hardware-specific

## Technical Details
- SSS = volume scattering after surface transmission, where light scatters multiple times internally
- Traditional approaches: screen-space blur (cheap/wrong), pre-integrated skin (limited), diffusion profiles (medium cost)
- Hybrid approach: trace actual light paths through volume + correct with diffusion where path tracing is noisy
- Targets both high-end and mobile GPUs (HypeHype presentation covers mobile stochastic lighting)

## Other SIGGRAPH 2025 Presentations Relevant to SOMA
- **Adaptive Voxel-Based OIT** (Activision) — order-independent transparency for layered anatomy
- **Strand-based hair rendering** (MachineGames) — realistic hair/fur for anatomical models
- **idTech8 GI** (id Software) — real-time global illumination techniques
- **MegaLights** (Epic Games) — stochastic direct lighting for many lights (surgical lighting?)

## Source
SIGGRAPH 2025 Advances in Real-Time Rendering course page: https://advances.realtimerendering.com/s2025/
PDF slides: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf

## Sources

- https://advances.realtimerendering.com/s2025/index.html
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
