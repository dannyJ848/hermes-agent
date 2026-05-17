# webgpu-medical-volume-rendering-subsurface-scattering-2025

*Researched: 2026-04-05 23:28 CDT*

# WebGPU Medical Volume Rendering & Subsurface Scattering (2025)

## Real-Time CT Volume Path Tracing in Browser (WebGPU)

**Source:** Hacker News Show HN (MickGorobets, ~Feb 2026)

A GPU path tracer for volumetric medical data running entirely in Chrome via WebGPU + WASM (C++/Emscripten).

### Key Techniques:
- **Delta tracking (Woodcock null-collision algorithm)** for unbiased volume rendering
- **Cook-Torrance GGX BRDF + Henyey-Greenstein phase function** for realistic light scattering
- **MacroGrid acceleration**: DDA empty-space skipping + GPU tile culling for performance
- **Progressive frame accumulation**: noisy at first, converges to ground truth
- **HDR pipeline**: bloom, auto-exposure, PBR Neutral / ACES tone mapping
- **Async mip-level streaming** with gzip decompression for large volumes

### SOMA Relevance:
- Delta tracking + HG phase function directly applicable to SOMA's tissue rendering
- Progressive accumulation is ideal for mobile — start noisy, refine
- MacroGrid acceleration solves the "empty space" problem in CT-to-mesh rendering
- Built on **Diligent Engine** (open-source, has WebGPU backend) — potential integration path

## SIGGRAPH 2025: Advances in Real-Time Subsurface Scattering

**Sources:**
- SIGGRAPH 2025 Advances course (advances.realtimerendering.com)
- "RT Subsurface Scattering via Hybrid ReSTIR-Path Tracing & Diffusion"

### Key Innovation:
Hybrid approach combining **ReSTIR path tracing** with **diffusion approximation** for real-time SSS. This is the state-of-the-art for interactive subsurface scattering — exactly what SOMA needs for realistic skin/tissue rendering.

## Reference Implementation Resources (SSS)

From Jaysmito101/AdvancedVulkanDemos:
1. **Separable Subsurface Scattering** (Jimenez et al.) — iryoku.com — the gold standard for screen-space SSS
2. **Approximating Translucency** (GDC 2011, Barre-Brisebois) — fast, cheap convincing SSS
3. **GPU Gems Ch.16** — Real-Time Approximations to Subsurface Scattering
4. **BSSRDF in PBRT** — physically-based reference

## Actionable for SOMA
- **Short-term**: Implement screen-space SSS using Separable SSS approach (Jimenez) — runs on any WebGL2/WebGPU
- **Medium-term**: Add Henyey-Greenstein phase function for translucency effects on thin tissue (ears, hands)
- **Long-term**: Progressive volume rendering for CT-derived anatomy overlays
- **Consider**: Diligent Engine as rendering backend if Three.js limits become blocking


## Sources

- https://news.ycombinator.com/item?id=46933474
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
