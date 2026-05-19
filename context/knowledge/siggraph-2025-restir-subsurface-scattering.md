# siggraph-2025-restir-subsurface-scattering

*Researched: 2026-04-05 17:49 CDT*

# SIGGRAPH 2025: Real-Time Subsurface Scattering via Hybrid ReSTIR Path Tracing & Diffusion

**Source:** SIGGRAPH 2025 Advances in Real-Time Rendering course
**Paper:** dl.acm.org/doi/abs/10.1145/3675372
**Video:** youtube.com/watch?v=AtFBbMnUgoc

## Key Innovation

Traditional real-time SSS relies on **diffusion approximations** (screen-space blur, dipole models). These are fast but physically inaccurate — they miss light transport through thin tissue, colored translucency, and deep scattering.

The SIGGRAPH 2025 paper introduces a **hybrid approach** combining:
1. **ReSTIR (Reservoir-based Spatiotemporal Importance Resampling)** — for path-traced subsurface scattering
2. **Diffusion approximation** — as a fallback/supplement for performance

## Why This Matters for SOMA

- **Medical anatomy viewers need SSS** — skin, organs, and tissue all exhibit subsurface scattering. Without it, 3D anatomy looks plastic and lifeless.
- **Current approach (screen-space blur)** works on WebGL but is physically wrong — light doesn't bleed through thin membranes correctly.
- **WebGPU compute shaders** can run ReSTIR-style algorithms, making this viable for browser-based medical visualization.
- The hybrid approach is designed for "current generation pipelines" — meaning it runs at interactive rates.

## SOMA Integration Path

1. **Phase 1 (now):** Continue with screen-space SSS approximation (GPU Gems Ch.16 approach) for WebGL compatibility
2. **Phase 2:** When WebGPU is stable on iOS Safari (expected late 2026), implement the ReSTIR hybrid for:
   - Skin rendering (epidermis translucency)
   - Organ boundary visualization (light transmission through tissue layers)
   - Cross-section rendering (scattering at cut surfaces)

## Technical Notes

- ReSTIR resamples light paths from previous frames + spatial neighbors
- Hybrid = use ReSTIR where it converges fast (thin features, edges), diffusion where it doesn't (deep scattering)
- Paper claims "high-quality SSS fast enough for current generation pipelines"
- Published at ACM SIGGRAPH 2025, part of the "Advances in Real-Time Rendering" course

## Related: WebGPU Medical AI

A Feb 2026 paper by Patel et al. explores **WebGPU-accelerated client-side AI for dermatological diagnostics** with local differential privacy. This validates the direction of WebGPU for medical applications in the browser.

## References
- advances.realtimerendering.com/s2025/ (SIGGRAPH 2025 course)
- dl.acm.org/doi/abs/10.1145/3675372
- developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering (GPU Gems Ch.16 baseline)


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.youtube.com/watch?v=AtFBbMnUgoc
- https://dl.acm.org/doi/abs/10.1145/3675372
