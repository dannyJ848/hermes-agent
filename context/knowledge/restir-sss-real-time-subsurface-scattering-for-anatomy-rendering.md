# ReSTIR-SSS Real-Time Subsurface Scattering for Anatomy Rendering

*Researched: 2026-04-06 14:07 CDT*

# ReSTIR-SSS: Real-Time Subsurface Scattering via Resampled Importance Sampling

## Summary
ReSTIR SSS (Werner, Schüßler, Dachsbacher, HPG 2024) adapts the ReSTIR importance resampling framework to render subsurface scattering using BSSRDF importance sampling with spatiotemporal path reuse. This is directly relevant to SOMA's anatomy viewer — human tissue (skin, organs, muscles) all exhibit subsurface scattering, and realistic rendering of these materials is critical for medical visualization.

## Key Innovation
Traditional real-time SSS uses screen-space diffusion approximations (e.g., Jimenez SSS, Separable SSS). ReSTIR-SSS instead:
1. Uses **BSSRDF importance sampling** — samples paths that scatter beneath the surface
2. Applies **spatiotemporal resampling** (ReSTIR pattern) to reuse scattering paths across pixels and frames
3. Achieves **path-traced SSS** at real-time rates, eliminating the blurry artifacts of screen-space approximations

## SIGGRAPH 2025 Advances Course
A comprehensive SSS course was presented at SIGGRAPH 2025 Advances in Real-Time Rendering, covering the full state of the art. Source: `advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf`

## Open Source Implementation
- **Repo:** `MircoWerner/ReSTIR-SSS` (GitHub, 51 stars, C++)
- **Paper:** ACM DOI `10.1145/3675372`
- **Video:** HPG 2024 Day 1 presentation on YouTube

## SOMA Integration Relevance
For SOMA's 3D anatomy viewer (Three.js/WebGPU):
1. **Skin rendering:** SSS is essential for realistic skin — ears glowing red with backlight, waxiness of skin
2. **Organ tissue:** Liver, heart, brain tissue all scatter light subsurface — flat diffuse shading looks wrong
3. **Current gap:** SOMA likely uses standard PBR materials without SSS. Adding screen-space SSS (simpler than ReSTIR) would be a major visual upgrade
4. **Practical path:** Start with Separable SSS (Jimenez 2015) shader in Three.js, then consider ReSTIR-SSS if targeting WebGPU path tracing

## Implementation Strategy for Three.js
- Three.js has `MeshPhysicalMaterial` with `transmission` and `thickness` properties
- For screen-space SSS approximation: implement as a post-process pass using `EffectComposer`
- For WebGPU path: Custom `SubsurfaceScatteringNode` in Three.js node material system
- Key parameters per tissue type: scattering radius (R/G/B channels), albedo, Fresnel

## Sources
- Werner et al., "ReSTIR Subsurface Scattering for Real-Time Path Tracing," HPG 2024
- SIGGRAPH 2025 Advances in Real-Time Rendering course on SSS
- GitHub: MircoWerner/ReSTIR-SSS


## Sources

- https://dl.acm.org/doi/abs/10.1145/3675372
- https://github.com/MircoWerner/ReSTIR-SSS
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
