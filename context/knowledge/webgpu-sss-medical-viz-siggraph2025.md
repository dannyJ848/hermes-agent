# webgpu-sss-medical-viz-siggraph2025

*Researched: 2026-04-05 16:46 CDT*

# WebGPU SSS & Medical Visualization (April 2026 Research)

## SIGGRAPH 2025 Real-Time SSS
- New hybrid ReSTIR-Path Tracing + Diffusion approach for real-time subsurface scattering
- Paper: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Key insight: volume scattering after surface transmission, multiple internal bounces
- Applicable to SOMA: realistic tissue rendering in anatomy viewer

## WebGPU for Medical AI (Feb 2026)
- Paper: "WebGPU Accelerated Client-Side AI for Privacy Preserving Dermatological Diagnostics"
- Client-side AI with local differential privacy via WebGPU
- Validates WebGPU as viable platform for medical applications in browser

## GPU Gems SSS Techniques (for SOMA shaders)
Three approximation levels for real-time SSS:
1. **Wrap Lighting** — simplest: `max(0, (dot(L,N) + wrap) / (1 + wrap))` where wrap ∈ [0,1]
   - Softens diffuse lighting, reduces contrast
   - Color shift toward red at shadow transitions (simulates blood absorption)
   - Can encode in texture lookup for fragment shader efficiency
2. **Depth-Map SSS** — render light-space depth, blur in screen space
3. **Texture-Space Diffusion** — render diffuse lighting to texture, apply Gaussian blur kernels

### SOMA Integration Priority
- Start with wrap lighting (cheapest, ~0 perf cost)
- Add texture-lookup with color shift for skin realism
- Reserve full texture-space diffusion for desktop WebGPU; skip for mobile WebGL
- The SIGGRAPH 2025 hybrid approach is aspirational — may be feasible on WebGPU in 1-2 years


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- https://www.researchgate.net/publication/401110730
