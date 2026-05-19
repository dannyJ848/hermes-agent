# real-time-subsurface-scattering-2024-2025

*Researched: 2026-04-06 20:32 CDT*

# Real-Time Subsurface Scattering: Latest Techniques (2024-2025)

## ReSTIR Subsurface Scattering (Werner et al., HPG 2024)

**Key innovation:** Combines path tracing with diffusion approximation for real-time SSS, overcoming limitations of traditional screen-space algorithms.

**Problem with existing approaches:**
- Screen-space SSS approximations are fast but miss geometric detail
- Diffusion approximation captures more detail but increases noise
- Full volumetric path tracing is too expensive for real-time

**Solution:** ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) applied to subsurface scattering:
- Uses path tracing with diffusion approximation
- Improves efficiency via resampling — reuses samples across frames and pixels
- Dramatically reduces noise compared to naive diffusion path tracing
- Works in real-time at interactive framerates

## NVIDIA SIGGRAPH 2025 Hybrid SSS (upcoming)

NVIDIA announced a **hybrid real-time SSS technique** combining:
- Volumetric path tracing
- New physically-based diffusion model
- Presented at "Advances in Real-Time Rendering in Games" (SIGGRAPH 2025, 20th anniversary)

This appears to build on the ReSTIR SSS work with a proprietary implementation.

## Relevance to SOMA

For medical 3D anatomy rendering:
1. **Skin rendering:** SSS is critical for realistic skin on anatomical models
2. **Organ translucency:** Internal organs (liver, kidneys) exhibit strong subsurface scattering
3. **Current SOMA approach:** Uses screen-space blur approximation (fast but inaccurate)
4. **Upgrade path:** ReSTIR SSS could be adapted for WebGPU — the resampling approach is compatible with compute shaders
5. **Mobile concern:** ReSTIR has non-trivial memory overhead (reservoir buffers). May need simplified variant for mobile GPUs

### Implementation Notes
- ReSTIR requires storing per-pixel reservoir data (sample weights, PDFs) — estimate 32-64 bytes per pixel
- On mobile GPUs (iPhone A-series), memory bandwidth is the bottleneck
- A simplified 2-sample variant could work at ~4ms additional cost on modern mobile
- The diffusion profile can be precomputed per tissue type (skin, fat, muscle, organ)

## Sources
- ACM DL: https://dl.acm.org/doi/abs/10.1145/3675372
- ResearchGate: https://www.researchgate.net/publication/383018057
- SIGGRAPH 2025 Advances: https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/


## Sources

- https://dl.acm.org/doi/abs/10.1145/3675372
- https://www.researchgate.net/publication/383018057
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
