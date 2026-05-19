# subsurface-scattering-realtime-2025

*Researched: 2026-04-06 00:06 CDT*

# Real-Time Subsurface Scattering for 3D Anatomy Rendering

## Key Finding (April 2026)
SIGGRAPH 2025 hosted a dedicated course on "Advances in Real-Time Subsurface Scattering" — a comprehensive state-of-the-art overview of SSS techniques for game-quality rendering. The course covers:

### Hybrid ReSTIR-Path Tracing + Diffusion
A novel hybrid approach combining ReSTIR path tracing with diffusion theory for real-time SSS. This allows physically-accurate subsurface light transport at interactive framerates, ideal for organic tissue rendering.

### Core Reference Pipeline (for SOMA implementation)
From the AdvancedVulkanDemos resource compilation:
1. **Separable Subsurface Scattering** (Jimenez et al.) — The industry standard. Separates 2D blur into two 1D passes, enabling real-time screen-space SSS. Paper: iryoku.com/separable-sss
2. **Fast Translucency Approximation** (Barre-Brisebois, GDC 2011) — Cheap wrap-lighting + inverse-transmittance trick for convincing SSS look without actual subsurface simulation
3. **GPU Gems Ch.16** — NVIDIA's classic real-time SSS approximations (texture-space blur, warp-based)
4. **PBRT BSSRDF** — Ground truth reference for validating approximations

### SOMA Application
For SOMA's WebGPU-based anatomy viewer, the recommended approach:
- **Tier 1 (fastest):** GDC 2011 translucency approximation — single shader pass, works on mobile
- **Tier 2 (balanced):** Separable SSS in screen space — two-pass Gaussian blur on light buffer
- **Tier 3 (quality):** Hybrid path-traced SSS — requires desktop GPU, not mobile-ready yet

The separable approach (Tier 2) is the sweet spot for mobile WebGPU — quality close to offline rendering at 60fps on mid-range devices.

## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
