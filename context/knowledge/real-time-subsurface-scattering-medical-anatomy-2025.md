# real-time-subsurface-scattering-medical-anatomy-2025

*Researched: 2026-04-05 23:46 CDT*

# Real-Time Subsurface Scattering for Medical Anatomy Rendering (2025)

## Why It Matters for SOMA
Human anatomy rendering requires convincing subsurface scattering (SSS) — skin, organs, and tissue all exhibit translucency where light enters one point and exits nearby. Without SSS, 3D anatomy looks plastic and lifeless.

## Core Concepts (from MJP's Introduction)
- **Standard diffuse (Lambertian)** assumes scattered light exits within the same pixel's footprint — adequate for opaque materials
- **True SSS** occurs when light scatters far enough to exit under neighboring pixels — requires global consideration of nearby lighting
- **Offline approach**: Volumetric path tracing (accurate but expensive)
- **Real-time approximation**: Two main families:
  1. **Screen-space diffusion** (Separable SSS by Jimenez et al.) — blur in screen space using Gaussian kernels tuned to skin profiles
  2. **Pre-integrated skin shading** (Penner & Borshukov) — precompute diffusion into a lookup texture

## SIGGRAPH 2025 Advances
The SIGGRAPH 2025 "Advances in Real-Time Rendering" course introduced a **hybrid ReSTIR-Path Tracing + Diffusion** approach for real-time SSS. This combines:
- ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) for sample generation
- Path tracing for accurate volumetric scattering
- Diffusion approximation as a fallback for performance
- This represents the state-of-the-art for real-time SSS as of 2025

## Key Reference Papers (from Jaysmito101/AdvancedVulkanDemos)
1. **Separable Subsurface Scattering** — Jimenez et al. (iryoku.com) — the workhorse technique for game SSS
2. **Approximating Translucency** — Colin Barre-Brisebois, GDC 2011 — fast/cheap SSS look using wrap lighting + N·L tricks
3. **GPU Gems Ch.16** — NVIDIA's real-time SSS approximations (texture-space diffusion)
4. **The BSSRDF** — PBRT chapter on the Bidirectional Subsurface Scattering Reflectance Distribution Function

## Recommended Approach for SOMA (Mobile/WebGPU)
For SOMA's mobile + Three.js/WebGPU target:
1. **Start with**: Pre-integrated skin shading (cheapest, works on mobile WebGL)
2. **Upgrade to**: Screen-space Gaussian blur SSS when WebGPU available
3. **Future**: Full ReSTIR-PT SSS when mobile GPUs support it (2-3 years)

### Minimal SSS for Mobile (Pre-integrated)
- Use a 2D LUT texture indexed by (N·L, curvature)
- Bake skin diffusion profile into the LUT
- Cost: 1 texture lookup per pixel — essentially free
- Convincing enough for anatomy education

## Sources
- MJP Blog: https://therealmjp.github.io/posts/sss-intro/
- SIGGRAPH 2025 SSS Course: https://advances.realtimerendering.com/s2025/
- Separable SSS Paper: https://www.iryoku.com/separable-sss/
- GPU Gems Ch.16: https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering


## Sources

- https://therealmjp.github.io/posts/sss-intro/
- https://advances.realtimerendering.com/s2025/
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
