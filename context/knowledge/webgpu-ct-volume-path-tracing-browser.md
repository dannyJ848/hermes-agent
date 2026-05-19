# webgpu-ct-volume-path-tracing-browser

*Researched: 2026-04-05 19:25 CDT*

# Real-Time Path Tracing of Medical CT Volumes in Browser via WebGPU

**Source:** Hacker News Show HN (MickGorobets, ~Feb 2026) — grenzwert.net

## Key Technical Details

1. **Delta Tracking (Woodcock null-collision algorithm)** — Unbiased volume rendering. No pre-baked lighting, fully dynamic.
2. **Cook-Torrance GGX BRDF + Henyey-Greenstein phase function** — Physically-based scattering for volumetric media. The HG phase function controls forward/backward scattering asymmetry (g parameter). Critical for realistic tissue rendering.
3. **MacroGrid acceleration** — DDA empty-space skipping + GPU tile culling. Skips transparent/empty voxels efficiently.
4. **Progressive frame accumulation** — Noisy first frame converges to ground truth over frames. Acceptable for medical apps where the viewer spends time studying anatomy.
5. **HDR pipeline** — Bloom, auto-exposure, PBR Neutral / ACES tone mapping.
6. **Async mip-level streaming with gzip decompression** — Progressive loading for large DICOM volumes.

## SOMA Relevance

- **Volume rendering for anatomy:** SOMA currently uses mesh-based rendering (glTF/GLB). This technique adds volume rendering capability for CT/MRI data — a future feature.
- **Henyey-Greenstein for tissue SSS:** The HG phase function is exactly what SOMA's SSS shader needs for realistic skin/organ translucency.
- **MacroGrid acceleration pattern:** DDA + tile culling could optimize SOMA's large mesh rendering (skip empty octree nodes).
- **Progressive accumulation:** Matches SOMA's use case — users spend time studying, so convergent rendering is fine.
- **Built on Diligent Engine** — Has a mature WebGPU backend. SOMA could consider Diligent Engine instead of raw Three.js for WebGPU features.

## Action Items for SOMA
1. Implement Henyey-Greenstein phase function in SOMA's SSS shader (soma-sss-shaders skill)
2. Evaluate Diligent Engine vs Three.js WebGPU for volume rendering future
3. Study Woodcock delta tracking for potential volume rendering module
4. Progressive frame accumulation pattern for quality scaling on mobile


## Sources

- https://news.ycombinator.com/item?id=46933474
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
