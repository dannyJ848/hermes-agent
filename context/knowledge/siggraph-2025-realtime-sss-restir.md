# siggraph-2025-realtime-sss-restir

*Researched: 2026-04-05 22:16 CDT*

# SIGGRAPH 2025: Real-Time Subsurface Scattering via Hybrid ReSTIR-Path-Tracing and Diffusion

**Source:** SIGGRAPH 2025 Advances in Real-Time Rendering in Games course (August 12, 2025)
**Speaker:** Tanki Zhang (NVIDIA)

## Key Innovation
A novel hybrid solution for real-time subsurface scattering (SSS) that approaches path-traced quality by combining:
- **ReSTIR (Reservoir-based Spatiotemporal Importance Resampling)** for path tracing
- **Diffusion approximation** for subsurface light transport

## Relevance to SOMA
This is directly applicable to SOMA's 3D anatomy viewer. Subsurface scattering is critical for realistic skin, tissue, and organ rendering. Current WebGPU-based anatomy viewers use either screen-space blur SSS or skip it entirely.

### Practical Takeaways for SOMA
1. The hybrid approach (ReSTIR + diffusion) is the state-of-the-art for real-time SSS in 2025
2. Could be adapted for WebGPU compute shaders using WGSL
3. The diffusion component is GPU-friendly and could run on mobile with reduced sample counts
4. For anatomy, the technique would dramatically improve skin, muscle tissue, and organ realism

## Course Context
The SIGGRAPH 2025 course also covers:
- Adaptive Voxel-Based Order-Independent Transparency (Activision)
- Ray Tracing for Assassin's Creed Shadows (Ubisoft)
- Strand-based hair/fur rendering (MachineGames / Indiana Jones)
- idTech8 Global Illumination (id Software)
- MegaLights stochastic direct lighting in UE5 (Epic Games)
- Stochastic Tile-Based Lighting for mobile (HypeHype) ← relevant for SOMA mobile

## PDF Slides Available
Full slides PDF: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf

## Next Steps for SOMA
- Extract the diffusion kernel parameters from the paper
- Prototype a WGSL compute shader implementing the diffusion approximation
- Test with SOMA's anatomy models (skin layer)
- The HypeHype stochastic tile-based lighting is also relevant for SOMA's mobile performance targets


## Sources

- https://advances.realtimerendering.com/s2025/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
