# real-time-subsurface-scattering-siggraph2025

*Researched: 2026-04-05 19:43 CDT*

# Real-Time Subsurface Scattering — SIGGRAPH 2025 Update

## Key Discovery: Hybrid ReSTIR-Path Tracing + Diffusion (NVIDIA, SIGGRAPH 2025)
NVIDIA presented a novel hybrid approach combining volumetric path tracing with physically-based diffusion approximation for real-time SSS. This was presented at SIGGRAPH 2025 "Advances in Real-Time Rendering in Games" course (20th anniversary).

**Technique:** Combines ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) path tracing with a new diffusion model. This bridges the gap between offline-quality SSS and real-time performance.

**Relevance to SOMA:** Directly applicable to realistic skin/tissue rendering in 3D anatomy viewer. Could replace our simpler SSS shader with this hybrid approach.

## Practical SSS Implementation Resources (Ranked by Usefulness for SOMA)

### Tier 1 — Implement Today
1. **Separable Subsurface Scattering** (Jimenez et al.) — The gold standard for real-time. Two-pass blur approach. PDF: iryoku.com/separable-sss
2. **Approximating Translucency** (GDC 2011, Barre-Brisebois) — Fast, cheap, convincing SSS look. Best for mobile/WebGPU where compute budget is limited.
3. **MJP's Introduction to Real-Time SSS** — therealmjp.github.io/posts/sss-intro/ — Best tutorial for getting started

### Tier 2 — Quality Boost
4. **GPU Gems Ch.16** — Real-Time Approximations to SSS (warping technique)
5. **GPU Gems 3 Ch.14** — Advanced Techniques for Realistic Real-Time Skin Rendering (texture-space diffusion)
6. **Disney BSDF Extension** (Burley 2015) — Integrated subsurface into Disney principled shader

### Tier 3 — Research/Offline Reference
7. **BSSRDF** (PBRT Book) — Physically correct formulation
8. **Quantized-Diffusion Model** (d'Eon & Irving) — Higher-order diffusion approximation
9. **BSSRDF Importance Sampling** (Sony Pictures) — Sampling strategies

## SOMA Integration Path
1. Start with Separable SSS (Tier 1) — straightforward two-pass Gaussian blur in screen space
2. Profile on mobile WebGPU target
3. If budget allows, upgrade to hybrid ReSTIR approach from SIGGRAPH 2025
4. BSSRDF for offline-quality reference renders

## Source
- SIGGRAPH 2025 Advances course: https://advances.realtimerendering.com/s2025/
- Resource compilation: https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
