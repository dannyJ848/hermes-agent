# siggraph-2025-realtime-sss

*Researched: 2026-04-06 15:40 CDT*

# SIGGRAPH 2025: Real-Time Subsurface Scattering Advances

## Key Discovery: NVIDIA Hybrid RT SSS Technique (SIGGRAPH 2025)

At SIGGRAPH 2025 "Advances in Real-Time Rendering" (celebrating 20th anniversary), NVIDIA unveiled a **hybrid real-time subsurface scattering technique** that combines:

1. **Volumetric path tracing** — physically accurate light transport through translucent materials
2. **New physically-based diffusion model** — approximates multi-scattering efficiently
3. **ReSTIR integration** — "RT Subsurface Scattering via Hybrid ReSTIR-Path Tracing & Diffusion"

### Technique Name
**ReSTIR-Path Tracing + Diffusion Hybrid for SSS**

### Why It Matters for SOMA
- Current SOMA SSS uses screen-space blur (fast but inaccurate for organic tissue)
- NVIDIA's hybrid approach could be adapted for WebGPU compute shaders
- The diffusion component is computationally lighter than full path tracing
- ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) enables real-time performance

### Architecture Sketch
```
1. Primary rays hit surface → identify SSS pixels
2. For SSS pixels: launch ReSTIR-guided volumetric path samples
3. Combine with analytical diffusion approximation
4. Temporal accumulation for denoising
5. Result: real-time translucent skin/organ rendering
```

### References
- SIGGRAPH 2025 Advances course: https://advances.realtimerendering.com/s2025/
- PDF (binary, needs viewer): https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- YouTube talk: https://www.youtube.com/watch?v=AtFBbMnUgoc
- PR Newswire announcement: https://www.prnewswire.com/news-releases/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20-302526911.html

### Action Items for SOMA
1. Study ReSTIR algorithm for potential WebGPU adaptation
2. Evaluate diffusion-based SSS as replacement for current screen-space blur
3. Monitor for open-source implementations (likely NVIDIA will release reference code)
4. Consider compute-shader-based volumetric path sampling for organ close-ups


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.youtube.com/watch?v=AtFBbMnUgoc
- https://www.prnewswire.com/news-releases/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20-302526911.html
