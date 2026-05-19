# realtime-sss-techniques-siggraph-2025

*Researched: 2026-04-06 06:25 CDT*

# Real-Time Subsurface Scattering: State of the Art (SIGGRAPH 2025 + NeurIPS 2024)

## SIGGRAPH 2025 Advances in Real-Time Rendering — SSS Session
- **Source:** "Real-Time Subsurface Scattering" — SIGGRAPH 2025 Advances course
- **Key trend:** Hybrid ReSTIR-Path Tracing + Diffusion for real-time SSS in RT pipelines
- **URL:** https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- **Relevance to SOMA:** Path-traced SSS with ReSTIR could eventually be ported to WebGPU compute shaders for anatomy rendering

## NVIDIA GPU Gems 3 — Chapter 14: Skin Rendering (Classic Reference)
- **Authors:** Eugene d'Eon, David Luebke (NVIDIA)
- **Core technique:** Separable subsurface scattering using Gaussian blur passes (screen-space)
- **Skin model:** Multilayer — oily surface + epidermis (specular via BRDF) + subsurface (diffusion profile)
- **Key insight:** ~6% of light reflects directly off skin surface (Fresnel), rest enters and scatters
- **Specular model:** Kelemen/Szirmay-Kalos (not Blinn-Phong) for physically accurate skin specular
- **SSS approximation:** Sum of Gaussians diffusion profile — texture-space blur with different kernel widths per RGB channel
- **Implementation:** 6 Gaussian passes in texture space (irradiance texture), each with different variance and weight
- **SOMA applicability:** The separable Gaussian SSS is EXACTLY what we implemented in `soma-sss-shaders` skill — confirms approach is standard industry practice

## NeurIPS 2024 — Subsurface Scattering for Gaussian Splatting
- **Authors:** Dihlmann, Majumdar, Engelhardt, Braun, Lensch
- **Innovation:** Decomposes scene into explicit surface (3D Gaussians + spatially-varying BRDF) + implicit volumetric scattering
- **Method:** Ray-traced differentiable rendering, joint optimization of shape + radiance transfer
- **Requires:** Multi-view OLAT (one light at a time) data — light-stage setup
- **Results:** Interactive-rate relighting, material editing, novel view synthesis
- **SOMA relevance:** Could apply to generating realistic anatomy models from photogrammetry/CT data — optimize Gaussian representation with SSS parameters

## glTF Extensions for Characters (SIGGRAPH 2025)
- Khronos proposing glTF extensions for granular mesh annotations
- Could enable per-part material properties (different SSS for muscle vs fat vs bone)
- Relevant to SOMA's glTF-based anatomy model pipeline

## Practical Takeaways for SOMA
1. **Our Gaussian SSS approach is validated** — separable Gaussians remain the standard for real-time
2. **WebGPU path tracing** is the future but not yet practical for mobile — keep Gaussian approach
3. **Gaussian Splatting + SSS** could replace our mesh-based anatomy models with more efficient representations
4. **glTF annotation extensions** could allow per-tissue SSS parameters in our glTF models


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- https://neurips.cc/virtual/2024/poster/96787
- https://www.khronos.org/assets/uploads/developers/presentations/glTF_Innovations_SIGGRAPH_2025.pdf
